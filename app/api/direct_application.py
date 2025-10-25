"""
Direct Application API Endpoints
One-click direct application to company decision makers (CEO/HR/Founders).
Focus on startups and SMEs where direct outreach is most effective.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

from app.core.dependencies import get_db, get_current_user
from app.core.rate_limiter import limiter, user_limiter, RateLimitTiers
from app.database.user_models import User
from app.services.direct_application_service import direct_application_service
from app.services.company_scanner_service import company_scanner_service


router = APIRouter(prefix="/direct-applications", tags=["Direct Applications"])


# Request/Response schemas
class DirectApplicationRequest(BaseModel):
    """Request for one-click direct application."""
    company_url: HttpUrl = Field(..., description="Company website URL")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    job_title: str = Field(..., min_length=1, max_length=200, description="Job title applying for")
    custom_message: Optional[str] = Field(None, max_length=1000, description="Optional custom message to include")


class DirectApplicationResponse(BaseModel):
    """Response from direct application."""
    success: bool
    application_id: Optional[int] = None
    message: str
    recipient: Optional[dict] = None
    sent_at: Optional[str] = None
    tracking_id: Optional[str] = None
    next_steps: Optional[List[str]] = None
    company_scan: Optional[dict] = None
    error: Optional[str] = None
    fallback_action: Optional[str] = None


class CompanyScanRequest(BaseModel):
    """Request to scan company website."""
    company_url: HttpUrl = Field(..., description="Company website URL")
    company_name: str = Field(..., min_length=1, max_length=200)


class CompanyScanResponse(BaseModel):
    """Response from company scan."""
    company_name: str
    company_url: str
    scan_success: bool
    career_page_url: Optional[str] = None
    total_jobs_found: int = 0
    entry_level_count: int = 0
    is_startup: bool = False
    is_sme: bool = False
    company_size_estimate: Optional[str] = None
    ceo_contact: Optional[dict] = None
    hr_contact: Optional[dict] = None
    job_listings: Optional[List[dict]] = None
    entry_level_jobs: Optional[List[dict]] = None
    scan_timestamp: str
    error: Optional[str] = None


class BatchApplicationRequest(BaseModel):
    """Request for batch applications to multiple companies."""
    companies: List[dict] = Field(..., max_items=10, description="List of companies to apply to (max 10)")


class BatchApplicationResponse(BaseModel):
    """Response from batch applications."""
    total_attempted: int
    successful: int
    failed: int
    applications: List[dict]
    errors: Optional[List[dict]] = None


# Endpoints

@router.post("/one-click-apply", response_model=DirectApplicationResponse)
@user_limiter.limit(RateLimitTiers.AUTO_APPLY_SCAN)
async def one_click_direct_apply(
    request: DirectApplicationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ONE-CLICK DIRECT APPLICATION
    
    This is the magic feature that:
    1. Scans the company website for job openings
    2. Finds CEO/HR/Founder contacts automatically
    3. Sends a personalized application directly to the decision maker
    
    **Best for**: Startups and SMEs (< 250 employees)
    **Success Rate**: Higher than traditional job boards for small companies
    
    **How it works**:
    - AI scans company website
    - Identifies entry-level roles
    - Finds decision maker contacts
    - Crafts personalized pitch
    - Sends email directly to CEO/HR
    
    **Rate Limit**: 10 applications per hour (to maintain quality and avoid spam)
    """
    try:
        # Execute one-click application
        result = await direct_application_service.find_and_apply_direct(
            db=db,
            user_id=current_user.id,
            company_url=str(request.company_url),
            company_name=request.company_name,
            job_title=request.job_title,
            user_message=request.custom_message
        )
        
        if not result.get('success'):
            return DirectApplicationResponse(
                success=False,
                message=result.get('error', 'Application failed'),
                error=result.get('error'),
                fallback_action=result.get('alternative_action') or result.get('fallback_action')
            )
        
        return DirectApplicationResponse(
            success=True,
            application_id=result.get('application_id'),
            message=result.get('message', 'Application sent successfully!'),
            recipient=result.get('recipient'),
            sent_at=result.get('sent_at'),
            tracking_id=result.get('tracking_id'),
            next_steps=result.get('next_steps'),
            company_scan=result.get('company_scan')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing direct application: {str(e)}"
        )


@router.post("/scan-company", response_model=CompanyScanResponse)
@user_limiter.limit("20/hour")
async def scan_company_website(
    request: CompanyScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SCAN COMPANY WEBSITE
    
    Preview what the one-click application will find before sending.
    
    Scans company website to find:
    - Job openings (especially entry-level)
    - CEO/Founder contact information
    - HR/Recruiting contacts
    - Company size (startup/SME classification)
    - Career page URL
    
    Use this to verify the company is a good fit for direct application
    before sending.
    
    **Rate Limit**: 20 scans per hour
    """
    try:
        async with company_scanner_service as scanner:
            scan_result = await scanner.scan_company_website(
                company_url=str(request.company_url),
                company_name=request.company_name
            )
        
        return CompanyScanResponse(**scan_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning company website: {str(e)}"
        )


@router.post("/batch-apply", response_model=BatchApplicationResponse)
@user_limiter.limit("3/day")
async def batch_apply_to_companies(
    request: BatchApplicationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📨 BATCH APPLICATION TO MULTIPLE COMPANIES
    
    Apply to multiple startups/SMEs in one request.
    
    **Maximum**: 10 companies per batch
    **Rate Limit**: 3 batch requests per day (max 30 applications/day)
    
    Each company object should have:
    - `url`: Company website URL
    - `name`: Company name
    - `job_title`: Position applying for
    - `message`: Optional custom message
    
    **Processing**: Applications are sent sequentially with 2-second delays
    to be respectful and avoid triggering spam filters.
    
    **Best Practice**: Target companies you've researched and are genuinely
    interested in. Quality > Quantity.
    """
    try:
        # Validate company list
        if len(request.companies) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 companies per batch request"
            )
        
        # Execute batch application
        result = await direct_application_service.batch_apply_to_startups(
            db=db,
            user_id=current_user.id,
            company_list=request.companies,
            max_applications=10
        )
        
        return BatchApplicationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch applications: {str(e)}"
        )


@router.get("/recommendations/startups")
async def get_startup_recommendations(
    limit: int = 20,
    focus_entry_level: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
     GET STARTUP/SME RECOMMENDATIONS
    
    Get personalized startup and SME recommendations based on your profile.
    
    These are companies where direct applications are most effective:
    - Startups (< 50 employees)
    - Small businesses (< 250 employees)
    - Companies actively hiring for entry-level PM roles
    
    **Focus**: Entry-level friendly positions at growing companies
    **Source**: Curated list + live job board scraping
    
    Returns companies with:
    - Company details
    - Available positions
    - Contact information (if found)
    - Readiness score for direct application
    """
    try:
        # This would integrate with a curated startup database
        # or scrape job boards with startup filters
        # For now, return placeholder
        return {
            "recommendations": [],
            "total": 0,
            "message": "Feature coming soon - startup database integration pending",
            "manual_action": "Search AngelList, YCombinator jobs, or Wellfound for startups"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/my-applications")
async def get_my_direct_applications(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
     GET MY DIRECT APPLICATIONS
    
    View all your direct applications sent through the one-click feature.
    
    Includes:
    - Company and position details
    - Recipient information (CEO/HR)
    - Send status and tracking
    - Response status
    - Next actions
    
    **Tracking**: Know exactly who received your application and when.
    """
    try:
        from sqlalchemy import select, desc
        from app.database.job_models import JobApplication
        
        # Query direct applications
        query = (
            select(JobApplication)
            .where(
                JobApplication.user_id == current_user.id,
                JobApplication.application_method.in_([
                    'direct_to_decision_maker',
                    'direct_application'
                ])
            )
            .order_by(desc(JobApplication.applied_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        applications = result.scalars().all()
        
        # Count total
        count_query = (
            select(JobApplication)
            .where(
                JobApplication.user_id == current_user.id,
                JobApplication.application_method.in_([
                    'direct_to_decision_maker',
                    'direct_application'
                ])
            )
        )
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return {
            "applications": [
                {
                    "id": app.id,
                    "company": getattr(app, 'company_name', 'Unknown'),
                    "position": getattr(app, 'job_title', 'Unknown'),
                    "recipient_email": getattr(app, 'recipient_email', None),
                    "recipient_title": getattr(app, 'recipient_title', None),
                    "status": app.status,
                    "applied_at": app.applied_at.isoformat(),
                    "tracking_id": getattr(app, 'tracking_id', None)
                }
                for app in applications
            ],
            "total": total,
            "page": skip // limit + 1,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching applications: {str(e)}"
        )


@router.get("/stats")
async def get_direct_application_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
     GET DIRECT APPLICATION STATISTICS
    
    Your direct application performance metrics:
    - Total applications sent
    - Response rate
    - Interview rate
    - Most responsive company sizes
    - Best performing outreach types (CEO vs HR)
    
    Use these insights to optimize your application strategy.
    """
    try:
        from sqlalchemy import select, func
        from app.database.job_models import JobApplication
        
        # Total direct applications
        total_query = select(func.count()).select_from(JobApplication).where(
            JobApplication.user_id == current_user.id,
            JobApplication.application_method.in_([
                'direct_to_decision_maker',
                'direct_application'
            ])
        )
        total_result = await db.execute(total_query)
        total_applications = total_result.scalar() or 0
        
        # Applications with responses
        response_query = select(func.count()).select_from(JobApplication).where(
            JobApplication.user_id == current_user.id,
            JobApplication.application_method.in_([
                'direct_to_decision_maker',
                'direct_application'
            ]),
            JobApplication.status.in_(['reviewing', 'interviewed', 'offered'])
        )
        response_result = await db.execute(response_query)
        responses = response_result.scalar() or 0
        
        response_rate = (responses / total_applications * 100) if total_applications > 0 else 0
        
        return {
            "total_direct_applications": total_applications,
            "responses_received": responses,
            "response_rate": round(response_rate, 1),
            "recommendation": "Target startups with < 100 employees for best results" if response_rate < 20 else "Great job! Keep targeting similar companies"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching stats: {str(e)}"
        )
