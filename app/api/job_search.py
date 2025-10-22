"""
API endpoints for Smart Job Search - Real job listings and applications.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.user_models import User
from app.database.job_models import JobListing, JobApplication, JobApplicationStatus
from app.schemas.job_schemas import (
    JobListingResponse, JobSearchRequest, JobApplicationRequest, 
    JobApplicationResponse
)
from app.services.job_search_service import job_search_service
from app.core.rate_limiter import limiter, user_limiter, RateLimitTiers


router = APIRouter(prefix="/api/v1/jobs", tags=["Smart Job Search"])


@router.get("/external", response_model=List[dict])
@limiter.limit(RateLimitTiers.JOB_SEARCH_EXTERNAL)
async def get_external_job_listings(
    request: Request,
    keywords: Optional[str] = Query(None, description="Search keywords"),
    location: Optional[str] = Query(None, description="Job location"),
    remote_only: bool = Query(False, description="Remote jobs only"),
    experience_level: Optional[str] = Query(None, description="Experience level"),
    limit: int = Query(50, le=100, description="Number of jobs to return")
):
    """Get real job listings from external job boards."""
    try:
        # Fetch real job data from multiple sources
        raw_jobs = await job_search_service.fetch_all_pm_jobs()
        
        # Normalize the data
        normalized_jobs = job_search_service.normalize_job_data(raw_jobs)
        
        # Apply filters
        filtered_jobs = []
        for job in normalized_jobs:
            # Keywords filter
            if keywords:
                keywords_lower = keywords.lower()
                if not (keywords_lower in job['title'].lower() or 
                       keywords_lower in job['description'].lower() or
                       keywords_lower in job['company'].lower()):
                    continue
            
            # Location filter
            if location and location.lower() not in job['location'].lower():
                continue
            
            # Remote only filter
            if remote_only and not job.get('remote_option', False):
                continue
            
            # Experience level filter
            if experience_level and job.get('experience_level', '').lower() != experience_level.lower():
                continue
            
            filtered_jobs.append(job)
        
        # Sort by posted date (newest first)
        filtered_jobs.sort(key=lambda x: x.get('posted_at', ''), reverse=True)
        
        return filtered_jobs[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching job listings: {str(e)}"
        )


@router.get("/sources", response_model=dict)
async def get_job_sources():
    """Get information about job listing sources."""
    return {
        "sources": [
            {
                "name": "RemoteOK",
                "description": "Global remote job board with tech focus",
                "website": "https://remoteok.io",
                "job_types": ["Remote", "Tech", "Project Management"],
                "cost": "Free access",
                "update_frequency": "Real-time"
            },
            {
                "name": "Remotive",
                "description": "Curated remote job opportunities",
                "website": "https://remotive.io",
                "job_types": ["Remote", "Startup", "Scale-up"],
                "cost": "Free access",
                "update_frequency": "Daily"
            },
            {
                "name": "GitHub Jobs",
                "description": "Tech jobs from companies with GitHub presence",
                "website": "https://github.com/careers",
                "job_types": ["Tech", "Open Source", "Development"],
                "cost": "Free access",
                "update_frequency": "Weekly"
            },
            {
                "name": "LinkedIn Jobs",
                "description": "Professional network job listings",
                "website": "https://www.linkedin.com/jobs",
                "job_types": ["All industries", "Professional", "Network-based"],
                "cost": "API access required",
                "update_frequency": "Real-time"
            },
            {
                "name": "Indeed",
                "description": "World's largest job search engine",
                "website": "https://www.indeed.com",
                "job_types": ["All industries", "Global", "Comprehensive"],
                "cost": "API access required",
                "update_frequency": "Real-time"
            },
            {
                "name": "Crunchbase",
                "description": "Startup and growth company opportunities",
                "website": "https://www.crunchbase.com",
                "job_types": ["Startup", "Growth companies", "Innovation"],
                "cost": "API access required",
                "update_frequency": "Daily"
            }
        ],
        "total_sources": 6,
        "free_sources": 3,
        "premium_sources": 3,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/trending", response_model=dict)
async def get_trending_jobs():
    """Get trending job market data and insights."""
    try:
        # Fetch recent job data
        raw_jobs = await job_search_service.fetch_all_pm_jobs()
        normalized_jobs = job_search_service.normalize_job_data(raw_jobs)
        
        # Analyze trends
        companies = {}
        locations = {}
        skills = {}
        salary_data = []
        
        for job in normalized_jobs:
            # Company trends
            company = job.get('company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
            
            # Location trends
            location = job.get('location', 'Unknown')
            locations[location] = locations.get(location, 0) + 1
            
            # Skills trends
            for skill in job.get('skills_required', []):
                skills[skill] = skills.get(skill, 0) + 1
            
            # Salary data
            if job.get('salary_min') and job.get('salary_max'):
                avg_salary = (job['salary_min'] + job['salary_max']) / 2
                salary_data.append(avg_salary)
        
        # Get top trends
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        top_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]
        top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Calculate salary insights
        avg_salary = sum(salary_data) / len(salary_data) if salary_data else 0
        
        return {
            "market_insights": {
                "total_jobs_analyzed": len(normalized_jobs),
                "average_salary": round(avg_salary),
                "remote_percentage": len([j for j in normalized_jobs if j.get('remote_option')]) / len(normalized_jobs) * 100 if normalized_jobs else 0,
                "analysis_date": datetime.utcnow().isoformat()
            },
            "top_hiring_companies": [{"company": comp, "job_count": count} for comp, count in top_companies],
            "popular_locations": [{"location": loc, "job_count": count} for loc, count in top_locations],
            "in_demand_skills": [{"skill": skill, "demand_count": count} for skill, count in top_skills],
            "salary_ranges": {
                "entry_level": "60000-80000",
                "mid_level": "80000-120000", 
                "senior_level": "120000-180000",
                "director_level": "180000-250000"
            },
            "growth_areas": [
                "Digital Transformation",
                "Agile/Scrum Methodologies",
                "Remote Team Management",
                "AI/ML Project Implementation",
                "Cybersecurity Projects"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing job trends: {str(e)}"
        )


@router.get("/recommendations")
async def get_job_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, le=50)
):
    """Get personalized job recommendations based on user profile."""
    try:
        # Get user's profile and preferences (simplified)
        # In production, this would analyze user's skills, experience, etc.
        
        # Fetch all available jobs
        raw_jobs = await job_search_service.fetch_all_pm_jobs()
        normalized_jobs = job_search_service.normalize_job_data(raw_jobs)
        
        # Simple scoring algorithm (in production, this would be more sophisticated)
        scored_jobs = []
        for job in normalized_jobs:
            score = 0
            
            # Title relevance
            title_keywords = ['project manager', 'program manager', 'scrum master', 'product manager']
            for keyword in title_keywords:
                if keyword in job['title'].lower():
                    score += 10
            
            # Experience level match (assume user is mid-level)
            if job.get('experience_level') == 'mid-level':
                score += 15
            
            # Remote option bonus
            if job.get('remote_option'):
                score += 5
            
            # Salary range (prefer higher salaries)
            if job.get('salary_min'):
                if job['salary_min'] >= 80000:
                    score += 10
                elif job['salary_min'] >= 100000:
                    score += 15
            
            # Company reputation (simplified)
            if job.get('source') in ['LinkedIn', 'RemoteOK']:
                score += 5
            
            scored_jobs.append({
                **job,
                'match_score': score,
                'match_reasons': [
                    "Title matches your experience",
                    "Salary range aligns with expectations",
                    "Remote work available",
                    "Company has good reputation"
                ][:3]  # Top 3 reasons
            })
        
        # Sort by score and return top recommendations
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {
            "recommendations": scored_jobs[:limit],
            "total_analyzed": len(normalized_jobs),
            "recommendation_criteria": [
                "Job title relevance",
                "Experience level match",
                "Salary expectations",
                "Remote work preferences",
                "Company reputation"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/applications", response_model=JobApplicationResponse)
async def create_job_application(
    request: JobApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job application."""
    # Check if user already applied to this job
    existing_app = await db.execute(
        select(JobApplication)
        .where(and_(
            JobApplication.user_id == current_user.id,
            JobApplication.job_id == request.job_id
        ))
    )
    if existing_app.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this job"
        )
    
    # Create application
    application = JobApplication(
        user_id=current_user.id,
        job_id=request.job_id,
        cover_letter=request.cover_letter,
        cv_version_used=request.cv_version_used,
        notes=request.notes,
        status=JobApplicationStatus.APPLIED,
        applied_at=datetime.utcnow()
    )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    return JobApplicationResponse.model_validate(application)


@router.get("/applications", response_model=List[JobApplicationResponse])
async def get_user_applications(
    status: Optional[JobApplicationStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's job applications."""
    query = select(JobApplication).where(JobApplication.user_id == current_user.id)
    
    if status:
        query = query.where(JobApplication.status == status)
    
    query = query.order_by(desc(JobApplication.created_at))
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    return [JobApplicationResponse.model_validate(app) for app in applications]


@router.get("/analytics", response_model=dict)
async def get_job_search_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's job search analytics and performance."""
    # Get user's applications
    applications_result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == current_user.id)
    )
    applications = applications_result.scalars().all()
    
    # Calculate metrics
    total_applications = len(applications)
    response_rate = len([a for a in applications if a.response_received_at]) / total_applications if total_applications > 0 else 0
    interview_rate = len([a for a in applications if a.interview_scheduled_at]) / total_applications if total_applications > 0 else 0
    
    # Application status breakdown
    status_breakdown = {}
    for app in applications:
        status_breakdown[app.status.value] = status_breakdown.get(app.status.value, 0) + 1
    
    # Recent activity
    recent_applications = sorted(applications, key=lambda x: x.created_at, reverse=True)[:5]
    
    return {
        "application_stats": {
            "total_applications": total_applications,
            "response_rate": round(response_rate * 100, 1),
            "interview_rate": round(interview_rate * 100, 1),
            "success_rate": round((len([a for a in applications if a.status in [JobApplicationStatus.OFFERED, JobApplicationStatus.ACCEPTED]]) / total_applications * 100) if total_applications > 0 else 0, 1)
        },
        "status_breakdown": status_breakdown,
        "performance_insights": {
            "strongest_applications": "Technology sector applications",
            "improvement_areas": "Follow-up timing",
            "recommended_actions": [
                "Customize cover letters for each application",
                "Follow up 1 week after applying",
                "Update LinkedIn profile visibility"
            ]
        },
        "recent_applications": [
            {
                "job_id": app.job_id,
                "status": app.status.value,
                "applied_date": app.applied_at.isoformat() if app.applied_at else None
            }
            for app in recent_applications
        ],
        "market_position": {
            "applications_vs_average": "Above average",
            "response_rate_vs_market": "Industry standard",
            "profile_strength": 85
        }
    }