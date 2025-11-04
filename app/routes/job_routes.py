"""
Job search routes for job listings, applications, and recommendations.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.services.job_service import job_service
from app.database.user_models import User
from app.schemas.job_schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse,
    JobAlertCreate, JobAlertResponse, JobRecommendationResponse,
    CompanyCreate, CompanyResponse, JobSearchRequest,
    JobAnalyticsResponse, ApplicationAnalyticsResponse,
    SavedJobResponse, JobMatchingCapabilitiesResponse
)

router = APIRouter(prefix="/jobs", tags=["Job Search"])


# Job Listings

@router.get(
    "/",
    response_model=JobListResponse,
    summary="Search jobs",
    description="Search job listings with advanced filters"
)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search query for job title or description"),
    location: Optional[str] = Query(None, description="Job location"),
    employment_type: Optional[str] = Query(None, description="Employment type (full_time, part_time, contract, etc.)"),
    experience_level: Optional[str] = Query(None, description="Experience level (entry, mid, senior)"),
    salary_min: Optional[int] = Query(None, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, description="Maximum salary"),
    remote_only: Optional[bool] = Query(None, description="Remote jobs only"),
    company_size: Optional[str] = Query(None, description="Company size filter"),
    posted_within_days: Optional[int] = Query(None, description="Posted within X days"),
    sort_by: Optional[str] = Query("posted_date_desc", description="Sort by (posted_date_desc, salary_desc, relevance)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search job listings.
    
    Example query parameters:
    ?query=python developer&location=Lagos&employment_type=full-time&experience_level=mid&remote_only=true&limit=10
    """
    try:
        search_params = JobSearchRequest(
            query=query,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            remote_only=remote_only,
            company_size=company_size,
            posted_within_days=posted_within_days,
            sort_by=sort_by
        )
        
        return await job_service.search_jobs(db, search_params, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search jobs"
        )


# Job Recommendations

@router.get(
    "/recommendations",
    response_model=List[JobRecommendationResponse],
    summary="Get job recommendations",
    description="Get personalized job recommendations for the authenticated user"
)
async def get_job_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized job recommendations.
    
    Example query parameters:
    ?limit=15
    """
    try:
        return await job_service.get_job_recommendations(db, current_user.id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job recommendations"
        )

@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create job posting",
    description="Create a new job posting (for employers/admins)"
)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create job posting.
    
    Example request body:
    {
        "title": "Senior Product Manager",
        "company_name": "TalentFlow Labs",
        "location": "Remote - North America",
        "description": "Lead AI-driven job matching features",
        "employment_type": "full-time",
        "work_mode": "remote",
        "experience_level": "senior",
        "salary_min": 15000000,
        "salary_max": 18500000,
        "source_platform": "company_website"
    }
    """
    try:
        # TODO: Add role-based access control for job creation
        # For now, any authenticated user can create jobs
        return await job_service.create_job(db, job_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job posting"
        )


# Job Applications

@router.post(
    "/applications",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for job",
    description="Submit application for a job"
)
async def apply_for_job(
    application_data: JobApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Apply for a job.
    
    Example request body:
    {
        "job_listing_id": 1,
        "cv_id": 1,
        "cover_letter": "I'm excited about this role...",
        "customized_cv_content": {
            "summary_override": "Product leader in AI platforms"
        },
        "tailored_skills": ["AI Strategy", "Product Analytics"],
        "priority_level": "high"
    }
    """
    try:
        return await job_service.apply_for_job(db, current_user.id, application_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit job application"
        )


@router.get(
    "/applications/my",
    response_model=List[JobApplicationResponse],
    summary="Get my applications",
    description="Get current user's job applications"
)
async def get_my_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's job applications.
    
    Example query parameters:
    ?skip=0&limit=20
    """
    try:
        return await job_service.get_user_applications(db, current_user.id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve applications"
        )


@router.put(
    "/applications/{application_id}",
    response_model=JobApplicationResponse,
    summary="Update application",
    description="Update job application status or details"
)
async def update_application(
    application_id: int,
    application_data: JobApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update job application.
    
    Example request body:
    {
        "status": "interview",
        "response_received": true,
        "interview_scheduled": true,
        "interview_date": "2025-11-15T14:00:00Z",
        "interview_type": "video"
    }
    """
    try:
        updated_application = await job_service.update_application_status(
            db, application_id, current_user.id, application_data
        )
        if not updated_application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found or access denied"
            )
        return updated_application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )


# Job Alerts

@router.post(
    "/alerts",
    response_model=JobAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create job alert",
    description="Create a job alert for matching job notifications"
)
async def create_job_alert(
    alert_data: JobAlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create job alert.
    
    Example request body:
    {
        "title": "AI Product Manager roles",
        "keywords": "ai product manager, talent platforms",
        "location": "Remote",
        "experience_level": "senior",
        "salary_min": 14000000,
        "job_type": "remote",
        "frequency": "daily",
        "email_notifications": true
    }
    """
    try:
        return await job_service.create_job_alert(db, current_user.id, alert_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job alert"
        )


@router.get(
    "/alerts/my",
    response_model=List[JobAlertResponse],
    summary="Get my job alerts",
    description="Get current user's job alerts"
)
async def get_my_job_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's job alerts.
    
    Example: No parameters required - returns all alerts for authenticated user
    """
    try:
        return await job_service.get_user_job_alerts(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job alerts"
        )


# Companies

@router.post(
    "/companies",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create company",
    description="Create a new company profile"
)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create company profile.
    
    Example request body:
    {
        "company_name": "TalentFlow Labs",
        "industry": "HR Tech",
        "company_size": "medium",
        "remote_policy": "remote_first",
        "benefits": ["Remote stipend", "Learning budget"],
        "hr_email": "recruiting@talentflow.io"
    }
    """
    try:
        return await job_service.create_company(db, company_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )


@router.get(
    "/companies/{company_id}",
    response_model=CompanyResponse,
    summary="Get company by ID",
    description="Get company information by ID"
)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get company by ID.
    
    Example: GET /api/v1/jobs/companies/5
    """
    try:
        company = await job_service.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        return company
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company"
        )


# Analytics

@router.get(
    "/applications/analytics",
    response_model=ApplicationAnalyticsResponse,
    summary="Get application analytics",
    description="Get current user's job application analytics"
)
async def get_application_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's application analytics.
    
    Example: No parameters required - returns analytics for authenticated user's applications
    """
    try:
        return await job_service.get_user_application_analytics(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application analytics"
        )


@router.get(
    "/{job_id}/analytics",
    response_model=JobAnalyticsResponse,
    summary="Get job analytics",
    description="Get job posting analytics (for job owners/employers)"
)
async def get_job_analytics(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get job analytics.
    
    Example: GET /api/v1/jobs/123/analytics
    """
    try:
        # TODO: Add authorization check - only job owner/employer should see analytics
        analytics = await job_service.get_job_analytics(db, job_id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job analytics"
        )


# Smart Job Matching

@router.get(
    "/recommendations/ai",
    response_model=List[JobRecommendationResponse],
    summary="Get AI job recommendations",
    description="Get AI-powered job recommendations based on user profile and skills"
)
async def get_personalized_recommendations(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-driven job recommendations using external matching service.
    
    Example query parameters:
    ?limit=10
    """
    try:
        from app.services.job_search_service import JobSearchService
        
        search_service = JobSearchService()
        recommendations = await search_service.get_personalized_job_recommendations(
            db, current_user.id, limit
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job recommendations: {str(e)}"
        )


@router.post(
    "/save",
    summary="Save job for later",
    description="Save a job posting to user's saved jobs list"
)
async def save_job(
    job_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save a job posting for later reference.
    
    Example request body:
    {
        "job_id": 123,
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Remote",
        "salary": "$120k-$150k",
        "url": "https://example.com/jobs/123"
    }
    """
    try:
        from app.services.job_search_service import JobSearchService
        
        search_service = JobSearchService()
        success = await search_service.save_job_for_user(
            db, current_user.id, job_data
        )
        
        if success:
            return {"message": "Job saved successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save job"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save job: {str(e)}"
        )


@router.get(
    "/saved",
    response_model=List[SavedJobResponse],
    summary="Get saved jobs",
    description="Get user's saved jobs list"
)
async def get_saved_jobs(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of saved jobs"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's saved jobs.
    
    Example query parameters:
    ?limit=20
    """
    try:
        from app.services.job_search_service import JobSearchService
        
        search_service = JobSearchService()
        saved_jobs = await search_service.get_user_saved_jobs(
            db, current_user.id, limit
        )
        
        return saved_jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get saved jobs: {str(e)}"
        )


@router.get(
    "/matching/capabilities",
    response_model=JobMatchingCapabilitiesResponse,
    summary="Get AI matching capabilities",
    description="Get information about available AI job matching features"
)
async def get_matching_capabilities():
    """
    Get information about AI job matching capabilities.
    
    Example: No parameters required - returns capability information
    """
    try:
        from app.services.job_search_service import JobSearchService
        
        search_service = JobSearchService()
        capabilities = search_service.get_matching_info()
        
        return capabilities
        
    except Exception as e:
        return JobMatchingCapabilitiesResponse(
            sentence_transformers_available=False,
            fallback_method="Basic job aggregation",
            features=["Free job API aggregation"],
            error=str(e)
        )


# Admin/Background Tasks

@router.post(
    "/alerts/check",
    summary="Check job alerts (Admin/System)",
    description="Process all job alerts and send notifications for matching jobs"
)
async def check_job_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check job alerts and send notifications.
    
    Example: No request body required - triggers alert processing for all active alerts
    """
    try:
        # TODO: Add admin role check
        result = await job_service.check_job_alerts(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process job alerts"
        )


# Job Details (placed last to avoid conflicts with static subpaths)

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job by ID",
    description="Get detailed job information by ID"
)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get job by ID.
    
    Example: GET /api/v1/jobs/123
    """
    try:
        job = await job_service.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job"
        )