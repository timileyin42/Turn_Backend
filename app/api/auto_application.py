"""
Auto-Application API endpoints for TURN Platform.
Handles intelligent job matching and auto-application features.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, update, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.user_models import User, Profile
from app.database.auto_application_models import (
    PendingAutoApplication, AutoApplicationLog, JobMatchNotification,
    AutoApplicationSettings, JobApplicationTemplate, AutoApplicationStatus,
    JobMatchNotificationType
)
from app.services.auto_application_service import auto_application_service, AutoApplicationCriteria
from app.services.ai_service import ai_service
from app.services.email_service import email_service
from app.core.rate_limiter import limiter, user_limiter, RateLimitTiers

router = APIRouter(prefix="/api/v1/auto-apply", tags=["Auto Application"])


# Request/Response Models
class AutoApplicationSettingsRequest(BaseModel):
    """Request to update auto-application settings."""
    auto_apply_enabled: bool = Field(default=False)
    job_alerts_enabled: bool = Field(default=True)
    max_daily_auto_applications: int = Field(default=3, ge=1, le=10)
    min_match_score_threshold: float = Field(default=0.75, ge=0.5, le=1.0)
    preferred_job_types: Optional[List[str]] = None
    salary_expectations_min: Optional[int] = None
    salary_expectations_max: Optional[int] = None
    excluded_companies: Optional[List[str]] = None
    auto_apply_only_remote: bool = Field(default=False)
    require_manual_approval: bool = Field(default=True)
    preferred_locations: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None


class AutoApplicationSettingsResponse(BaseModel):
    """Response with auto-application settings."""
    user_id: int
    auto_apply_enabled: bool
    job_alerts_enabled: bool
    max_daily_auto_applications: int
    min_match_score_threshold: float
    preferred_job_types: Optional[List[str]]
    salary_expectations_min: Optional[int]
    salary_expectations_max: Optional[int]
    excluded_companies: Optional[List[str]]
    auto_apply_only_remote: bool
    require_manual_approval: bool
    preferred_locations: Optional[List[str]]
    required_skills: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PendingApplicationResponse(BaseModel):
    """Response for pending auto-application."""
    id: int
    job_title: str
    company_name: str
    location: Optional[str]
    salary_range: Optional[str]
    match_score: float
    auto_apply_score: float
    match_reasons: Optional[List[str]]
    generated_cover_letter: Optional[str]
    application_summary: Optional[str]
    confidence_score: float
    status: AutoApplicationStatus
    expires_at: datetime
    created_at: datetime
    job_url: Optional[str]
    
    class Config:
        from_attributes = True


class JobMatchNotificationResponse(BaseModel):
    """Response for job match notification."""
    id: int
    notification_type: JobMatchNotificationType
    title: str
    message: str
    job_title: Optional[str]
    company_name: Optional[str]
    match_score: Optional[float]
    action_url: Optional[str]
    is_read: bool
    is_actioned: bool
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ApplicationDecisionRequest(BaseModel):
    """Request to approve/reject pending application."""
    decision: str = Field(..., pattern="^(approved|rejected|modified)$")
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class JobMatchRequest(BaseModel):
    """Request to manually trigger job matching."""
    limit: int = Field(default=20, ge=1, le=50)
    min_match_score: float = Field(default=0.6, ge=0.3, le=1.0)
    include_already_applied: bool = Field(default=False)


# API Endpoints

@router.get("/settings", response_model=AutoApplicationSettingsResponse)
async def get_auto_application_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's auto-application settings."""
    # Get from profile
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return AutoApplicationSettingsResponse(
        user_id=current_user.id,
        auto_apply_enabled=profile.auto_apply_enabled,
        job_alerts_enabled=profile.job_alerts_enabled,
        max_daily_auto_applications=profile.max_daily_auto_applications,
        min_match_score_threshold=profile.min_match_score_threshold,
        preferred_job_types=profile.preferred_job_types,
        salary_expectations_min=profile.salary_expectations_min,
        salary_expectations_max=profile.salary_expectations_max,
        excluded_companies=profile.excluded_companies,
        auto_apply_only_remote=profile.auto_apply_only_remote,
        require_manual_approval=profile.require_manual_approval,
        preferred_locations=profile.preferred_locations,
        required_skills=profile.required_skills,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.put("/settings", response_model=AutoApplicationSettingsResponse)
async def update_auto_application_settings(
    request: AutoApplicationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's auto-application settings."""
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Update profile settings
    profile.auto_apply_enabled = request.auto_apply_enabled
    profile.job_alerts_enabled = request.job_alerts_enabled
    profile.max_daily_auto_applications = request.max_daily_auto_applications
    profile.min_match_score_threshold = request.min_match_score_threshold
    profile.preferred_job_types = request.preferred_job_types
    profile.salary_expectations_min = request.salary_expectations_min
    profile.salary_expectations_max = request.salary_expectations_max
    profile.excluded_companies = request.excluded_companies
    profile.auto_apply_only_remote = request.auto_apply_only_remote
    profile.require_manual_approval = request.require_manual_approval
    profile.preferred_locations = request.preferred_locations
    profile.required_skills = request.required_skills
    
    await db.commit()
    await db.refresh(profile)
    
    return AutoApplicationSettingsResponse(
        user_id=current_user.id,
        auto_apply_enabled=profile.auto_apply_enabled,
        job_alerts_enabled=profile.job_alerts_enabled,
        max_daily_auto_applications=profile.max_daily_auto_applications,
        min_match_score_threshold=profile.min_match_score_threshold,
        preferred_job_types=profile.preferred_job_types,
        salary_expectations_min=profile.salary_expectations_min,
        salary_expectations_max=profile.salary_expectations_max,
        excluded_companies=profile.excluded_companies,
        auto_apply_only_remote=profile.auto_apply_only_remote,
        require_manual_approval=profile.require_manual_approval,
        preferred_locations=profile.preferred_locations,
        required_skills=profile.required_skills,
        created_at=profile.created_at,
        updated_at=profile.updated_at
    )


@router.post("/find-matches")
@user_limiter.limit(RateLimitTiers.AUTO_APPLY_SCAN)
async def find_job_matches(
    http_request: Request,
    request: JobMatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger job matching for user."""
    try:
        # Check if user has auto-apply enabled
        profile = current_user.profile
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Create criteria from user settings
        criteria = AutoApplicationCriteria(
            min_match_score=request.min_match_score,
            max_daily_applications=request.limit,
            preferred_locations=profile.preferred_locations or [],
            required_skills=profile.required_skills or [],
            excluded_companies=profile.excluded_companies or [],
            salary_min=profile.salary_expectations_min,
            salary_max=profile.salary_expectations_max,
            remote_only=profile.auto_apply_only_remote,
            experience_level_match=True
        )
        
        # Find matches
        matches = await auto_application_service.find_job_matches_for_user(
            db=db,
            user_id=current_user.id,
            criteria=criteria
        )
        
        # Process matches in background if auto-apply is enabled
        if profile.auto_apply_enabled and matches:
            background_tasks.add_task(
                process_job_matches_background,
                current_user.id,
                matches,
                profile.require_manual_approval
            )
        
        return {
            "success": True,
            "matches_found": len(matches),
            "matches": [
                {
                    "job_title": match["job"]["title"],
                    "company": match["job"]["company"],
                    "match_score": match["similarity_score"],
                    "auto_apply_score": match["auto_apply_score"],
                    "reasons": match["match_reasons"]
                }
                for match in matches[:10]  # Return first 10 for preview
            ],
            "auto_apply_enabled": profile.auto_apply_enabled,
            "will_auto_process": profile.auto_apply_enabled and len(matches) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding job matches: {str(e)}"
        )


@router.get("/pending", response_model=List[PendingApplicationResponse])
async def get_pending_applications(
    status_filter: Optional[AutoApplicationStatus] = None,
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's pending auto-applications."""
    query = select(PendingAutoApplication).where(
        PendingAutoApplication.user_id == current_user.id
    )
    
    if status_filter:
        query = query.where(PendingAutoApplication.status == status_filter)
    
    query = query.order_by(desc(PendingAutoApplication.created_at)).limit(limit)
    
    result = await db.execute(query)
    pending_applications = result.scalars().all()
    
    return [
        PendingApplicationResponse.model_validate(app)
        for app in pending_applications
    ]


@router.post("/pending/{pending_id}/decision")
@user_limiter.limit(RateLimitTiers.AUTO_APPLY_SUBMIT)
async def make_application_decision(
    http_request: Request,
    pending_id: int,
    request: ApplicationDecisionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve, reject, or modify a pending application."""
    # Get pending application
    result = await db.execute(
        select(PendingAutoApplication).where(
            and_(
                PendingAutoApplication.id == pending_id,
                PendingAutoApplication.user_id == current_user.id
            )
        )
    )
    pending_app = result.scalar_one_or_none()
    
    if not pending_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending application not found"
        )
    
    if pending_app.status != AutoApplicationStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application is not pending approval"
        )
    
    # Update decision
    pending_app.user_decision = request.decision
    pending_app.user_decision_at = datetime.utcnow()
    pending_app.user_feedback = request.feedback
    
    if request.decision == "approved":
        pending_app.status = AutoApplicationStatus.APPROVED
        # Submit application in background
        background_tasks.add_task(
            submit_approved_application,
            pending_app.id,
            current_user.id
        )
        
    elif request.decision == "rejected":
        pending_app.status = AutoApplicationStatus.REJECTED
        
    elif request.decision == "modified":
        # Handle modifications
        if request.modifications:
            if "cover_letter" in request.modifications:
                pending_app.generated_cover_letter = request.modifications["cover_letter"]
            # Apply other modifications...
        pending_app.status = AutoApplicationStatus.APPROVED
        background_tasks.add_task(
            submit_approved_application,
            pending_app.id,
            current_user.id
        )
    
    await db.commit()
    
    return {
        "success": True,
        "decision": request.decision,
        "status": pending_app.status.value,
        "will_submit": request.decision in ["approved", "modified"]
    }


@router.get("/notifications", response_model=List[JobMatchNotificationResponse])
async def get_job_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's job match notifications."""
    query = select(JobMatchNotification).where(
        JobMatchNotification.user_id == current_user.id
    )
    
    if unread_only:
        query = query.where(JobMatchNotification.is_read == False)
    
    query = query.order_by(desc(JobMatchNotification.created_at)).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [
        JobMatchNotificationResponse.model_validate(notif)
        for notif in notifications
    ]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notification as read."""
    result = await db.execute(
        select(JobMatchNotification).where(
            and_(
                JobMatchNotification.id == notification_id,
                JobMatchNotification.user_id == current_user.id
            )
        )
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"success": True, "message": "Notification marked as read"}


@router.get("/analytics")
async def get_auto_application_analytics(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get auto-application analytics for user."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get pending applications count
    pending_count = await db.scalar(
        select(func.count(PendingAutoApplication.id))
        .where(
            and_(
                PendingAutoApplication.user_id == current_user.id,
                PendingAutoApplication.status == AutoApplicationStatus.PENDING_APPROVAL
            )
        )
    )
    
    # Get applications by status
    status_counts = {}
    for status in AutoApplicationStatus:
        count = await db.scalar(
            select(func.count(PendingAutoApplication.id))
            .where(
                and_(
                    PendingAutoApplication.user_id == current_user.id,
                    PendingAutoApplication.status == status,
                    PendingAutoApplication.created_at >= start_date
                )
            )
        )
        status_counts[status.value] = count or 0
    
    # Get notifications count
    unread_notifications = await db.scalar(
        select(func.count(JobMatchNotification.id))
        .where(
            and_(
                JobMatchNotification.user_id == current_user.id,
                JobMatchNotification.is_read == False
            )
        )
    )
    
    # Get average match scores
    avg_match_score = await db.scalar(
        select(func.avg(PendingAutoApplication.match_score))
        .where(
            and_(
                PendingAutoApplication.user_id == current_user.id,
                PendingAutoApplication.created_at >= start_date
            )
        )
    )
    
    return {
        "period_days": days,
        "pending_applications": pending_count or 0,
        "applications_by_status": status_counts,
        "unread_notifications": unread_notifications or 0,
        "average_match_score": float(avg_match_score) if avg_match_score else 0.0,
        "auto_apply_enabled": current_user.profile.auto_apply_enabled if current_user.profile else False,
        "profile_completeness": current_user.profile.completion_percentage if current_user.profile else 0
    }


# Background Tasks

async def process_job_matches_background(
    user_id: int,
    matches: List[Dict[str, Any]],
    require_approval: bool
):
    """Process job matches in background."""
    # This would be implemented with a proper task queue in production
    # For now, just log the activity
    print(f"Processing {len(matches)} job matches for user {user_id}, approval required: {require_approval}")


async def submit_approved_application(
    pending_application_id: int,
    user_id: int
):
    """Submit approved application in background."""
    # This would be implemented with a proper task queue in production
    print(f"Submitting approved application {pending_application_id} for user {user_id}")


# Health check endpoint
@router.get("/health")
async def auto_application_health():
    """Health check for auto-application service."""
    return {
        "service": "auto_application",
        "status": "healthy",
        "features": [
            "job_matching",
            "ai_application_generation",
            "manual_approval_workflow",
            "notification_system",
            "analytics_dashboard"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }