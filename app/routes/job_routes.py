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
    """Search job listings."""
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
    """Get job by ID."""
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
    """Create job posting."""
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
    """Apply for a job."""
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
    """Get user's job applications."""
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
    """Update job application."""
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
    """Create job alert."""
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
    """Get user's job alerts."""
    try:
        return await job_service.get_user_job_alerts(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job alerts"
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
    """Get personalized job recommendations."""
    try:
        return await job_service.get_job_recommendations(db, current_user.id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job recommendations"
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
    """Create company profile."""
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
    """Get company by ID."""
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
    """Get job analytics."""
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
    """Get user's application analytics."""
    try:
        return await job_service.get_user_application_analytics(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application analytics"
        )


# Smart Job Matching

@router.get(
    "/recommendations",
    response_model=List[JobRecommendationResponse],
    summary="Get personalized job recommendations",
    description="Get AI-powered job recommendations based on user profile and skills"
)
async def get_personalized_recommendations(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized job recommendations using free AI matching."""
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
    """Save a job posting for later reference."""
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
    """Get user's saved jobs."""
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
    """Get information about AI job matching capabilities."""
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
    """Check job alerts and send notifications."""
    try:
        # TODO: Add admin role check
        result = await job_service.check_job_alerts(db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process job alerts"
        )