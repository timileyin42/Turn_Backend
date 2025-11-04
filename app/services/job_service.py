"""
Job search and application management service.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc, text
from sqlalchemy.orm import selectinload

from app.database.job_models import (
    Job,
    JobApplication,
    JobAlert,
    JobSkillRequirement,
    CompanyProfile
)
from app.schemas.job_schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse,
    JobAlertCreate, JobAlertResponse, JobRecommendationResponse,
    CompanyCreate, CompanyResponse, JobSearchRequest,
    JobAnalyticsResponse, ApplicationAnalyticsResponse
)


class JobService:
    """Service for job search, applications, and career tracking."""
    
    # Job Management
    
    async def create_job(
        self, 
        db: AsyncSession, 
        job_data: JobCreate
    ) -> JobResponse:
        """
        Create a new job posting.
        
        Args:
            db: Database session
            job_data: Job creation data
            
        Returns:
            Created job response
        """
        payload = job_data.model_dump()
        db_job = Job(
            **payload,
            scraped_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)
        
        return JobResponse.model_validate(db_job)
    
    async def get_job_by_id(
        self, 
        db: AsyncSession, 
        job_id: int
    ) -> Optional[JobResponse]:
        """
        Get job by ID with company information.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job response with company details
        """
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.skill_requirements))
            .where(Job.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        return JobResponse.model_validate(job)
    
    async def search_jobs(
        self, 
        db: AsyncSession, 
        search_params: JobSearchRequest,
        skip: int = 0,
        limit: int = 20
    ) -> JobListResponse:
        """
        Search jobs with advanced filters.
        
        Args:
            db: Database session
            search_params: Search parameters
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Filtered job list
        """
        query = select(Job).options(selectinload(Job.skill_requirements))
        
        conditions = [Job.is_active.is_(True)]
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query}%"
            conditions.append(
                or_(
                    Job.title.ilike(search_term),
                    Job.description.ilike(search_term),
                    Job.company_name.ilike(search_term)
                )
            )
        
        # Location filter
        if search_params.location:
            location_term = f"%{search_params.location}%"
            conditions.append(Job.location.ilike(location_term))

        # Work mode filter
        if getattr(search_params, "work_mode", None):
            conditions.append(Job.work_mode == search_params.work_mode)
        
        # Employment type
        if search_params.employment_type:
            conditions.append(Job.employment_type == search_params.employment_type)
        
        # Experience level
        if search_params.experience_level:
            conditions.append(Job.experience_level == search_params.experience_level)
        
        # Salary range
        if search_params.salary_min:
            conditions.append(Job.salary_min >= search_params.salary_min)
        
        if search_params.salary_max:
            conditions.append(Job.salary_max <= search_params.salary_max)
        
        # Remote work
        if getattr(search_params, "remote_only", None):
            conditions.append(Job.work_mode.in_(["remote", "hybrid"]))

        if getattr(search_params, "is_remote_friendly", None):
            conditions.append(Job.is_remote_friendly.is_(True))
        
        # Skills
        if search_params.required_skills:
            for skill in search_params.required_skills:
                conditions.append(
                    Job.skill_requirements.any(
                        JobSkillRequirement.skill_name.ilike(f"%{skill}%")
                    )
                )
        
        # Company size
        if search_params.company_size:
            conditions.append(Job.company_size == search_params.company_size)
        
        # Date posted
        posted_window = getattr(search_params, "posted_within_days", None) or getattr(search_params, "posted_since", None)
        if posted_window:
            cutoff_date = datetime.utcnow() - timedelta(days=posted_window)
            conditions.append(Job.posted_at >= cutoff_date)
        
        query = query.where(and_(*conditions))
        
        # Count total results
        count_query = select(func.count(Job.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_by = getattr(search_params, "sort_by", None)
        if sort_by == "salary_desc":
            query = query.order_by(desc(Job.salary_max))
        elif sort_by == "posted_date_asc":
            query = query.order_by(Job.posted_at.asc())
        elif sort_by in {"relevance", "posted_date_desc"}:
            # TODO: Implement relevance scoring based on user profile
            query = query.order_by(desc(Job.posted_at))
        else:
            query = query.order_by(desc(Job.posted_at))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        job_responses = [JobResponse.model_validate(job) for job in jobs]
        
        return JobListResponse(
            jobs=job_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    # Job Application Management
    
    async def apply_for_job(
        self, 
        db: AsyncSession, 
        user_id: int, 
        application_data: JobApplicationCreate
    ) -> JobApplicationResponse:
        """
        Submit job application.
        
        Args:
            db: Database session
            user_id: Applicant user ID
            application_data: Application data
            
        Returns:
            Created application response
        """
        # Check if user already applied
        existing = await db.execute(
            select(JobApplication).where(
                and_(
                    JobApplication.user_id == user_id,
                    JobApplication.job_listing_id == application_data.job_listing_id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("You have already applied for this job")
        
        db_application = JobApplication(
            user_id=user_id,
            **application_data.model_dump(),
            applied_at=datetime.utcnow()
        )
        
        db.add(db_application)
        await db.commit()
        await db.refresh(db_application)
        
        return JobApplicationResponse.model_validate(db_application)
    
    async def get_user_applications(
        self, 
        db: AsyncSession, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[JobApplicationResponse]:
        """
        Get user's job applications.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of user applications
        """
        result = await db.execute(
            select(JobApplication)
            .options(
                selectinload(JobApplication.job_listing).selectinload(Job.skill_requirements)
            )
            .where(JobApplication.user_id == user_id)
            .order_by(desc(JobApplication.applied_at))
            .offset(skip)
            .limit(limit)
        )
        applications = result.scalars().all()
        
        return [JobApplicationResponse.model_validate(app) for app in applications]
    
    async def update_application_status(
        self, 
        db: AsyncSession, 
        application_id: int, 
        user_id: int, 
        application_data: JobApplicationUpdate
    ) -> Optional[JobApplicationResponse]:
        """
        Update job application (user can update their own applications).
        
        Args:
            db: Database session
            application_id: Application ID
            user_id: User ID
            application_data: Updated application data
            
        Returns:
            Updated application response
        """
        result = await db.execute(
            select(JobApplication).where(
                and_(
                    JobApplication.id == application_id,
                    JobApplication.user_id == user_id
                )
            )
        )
        application = result.scalar_one_or_none()
        
        if not application:
            return None
        
        # Update fields
        update_data = application_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(application, field, value)
            
            application.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(application)
        
        return JobApplicationResponse.model_validate(application)
    
    # Job Alerts
    
    async def create_job_alert(
        self, 
        db: AsyncSession, 
        user_id: int, 
        alert_data: JobAlertCreate
    ) -> JobAlertResponse:
        """
        Create job alert for user.
        
        Args:
            db: Database session
            user_id: User ID
            alert_data: Alert creation data
            
        Returns:
            Created job alert
        """
        db_alert = JobAlert(
            user_id=user_id,
            **alert_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_alert)
        await db.commit()
        await db.refresh(db_alert)
        
        return JobAlertResponse.model_validate(db_alert)
    
    async def get_user_job_alerts(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[JobAlertResponse]:
        """
        Get user's job alerts.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of job alerts
        """
        result = await db.execute(
            select(JobAlert)
            .where(JobAlert.user_id == user_id)
            .order_by(desc(JobAlert.created_at))
        )
        alerts = result.scalars().all()
        
        return [JobAlertResponse.model_validate(alert) for alert in alerts]
    
    async def check_job_alerts(
        self, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check all active job alerts and send notifications for matching jobs.
        
        Args:
            db: Database session
            
        Returns:
            Summary of alert processing
        """
        # Get all active alerts
        result = await db.execute(
            select(JobAlert).where(JobAlert.is_active == True)
        )
        alerts = result.scalars().all()
        
        notifications_sent = 0
        alerts_processed = len(alerts)
        
        for alert in alerts:
            # Find matching jobs posted since last check
            last_check = alert.last_checked or alert.created_at
            
            # Build search query based on alert criteria
            job_query = select(Job).where(
                and_(
                    Job.posted_at > last_check,
                    Job.is_active.is_(True)
                )
            )
            
            # Apply alert filters
            conditions = []
            
            if alert.keywords:
                keyword_conditions = []
                for keyword in alert.keywords:
                    keyword_term = f"%{keyword}%"
                    keyword_conditions.append(
                        or_(
                            Job.title.ilike(keyword_term),
                            Job.description.ilike(keyword_term)
                        )
                    )
                if keyword_conditions:
                    conditions.append(or_(*keyword_conditions))
            
            if alert.location:
                location_term = f"%{alert.location}%"
                conditions.append(Job.location.ilike(location_term))
            
            if alert.employment_type:
                conditions.append(Job.employment_type == alert.employment_type)
            
            if alert.salary_min:
                conditions.append(Job.salary_min >= alert.salary_min)
            
            if conditions:
                job_query = job_query.where(and_(*conditions))
            
            # Execute query
            matching_jobs_result = await db.execute(job_query)
            matching_jobs = matching_jobs_result.scalars().all()
            
            if matching_jobs:
                # TODO: Send notification to user about matching jobs
                # This would integrate with the email/notification service
                notifications_sent += len(matching_jobs)
            
            # Update last checked time
            alert.last_checked = datetime.utcnow()
        
        await db.commit()
        
        return {
            "alerts_processed": alerts_processed,
            "notifications_sent": notifications_sent,
            "processed_at": datetime.utcnow()
        }
    
    # Job Recommendations
    
    async def get_job_recommendations(
        self, 
        db: AsyncSession, 
        user_id: int,
        limit: int = 10
    ) -> List[JobRecommendationResponse]:
        """
        Get personalized job recommendations for user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            List of job recommendations
        """
        # TODO: Implement sophisticated recommendation algorithm
        # For now, return recent jobs that match user's profile
        
        # Get user's skills and experience from their profile/CV
        # This is a simplified version - real implementation would be more complex
        
        result = await db.execute(
            select(Job)
            .options(selectinload(Job.skill_requirements))
            .where(Job.is_active.is_(True))
            .order_by(desc(Job.posted_at))
            .limit(limit)
        )
        jobs = result.scalars().all()
        
        recommendations: List[JobRecommendationResponse] = []
        for index, job in enumerate(jobs):
            job_payload = JobResponse.model_validate(job).model_dump()
            score = max(0.0, min(1.0, 0.8 - (index * 0.05)))
            recommendations.append(
                JobRecommendationResponse(
                    job=job_payload,
                    similarity_score=score,
                    match_reasons=["Recent job matching your profile"],
                    matching_method="recency",
                    recommended_action="Apply now"
                )
            )

        return recommendations
    
    # Company Management
    
    async def create_company(
        self, 
        db: AsyncSession, 
        company_data: CompanyCreate
    ) -> CompanyResponse:
        """
        Create company profile.
        
        Args:
            db: Database session
            company_data: Company creation data
            
        Returns:
            Created company response
        """
        db_company = CompanyProfile(
            **company_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_company)
        await db.commit()
        await db.refresh(db_company)
        
        return CompanyResponse.model_validate(db_company)
    
    async def get_company_by_id(
        self, 
        db: AsyncSession, 
        company_id: int
    ) -> Optional[CompanyResponse]:
        """
        Get company by ID.
        
        Args:
            db: Database session
            company_id: Company ID
            
        Returns:
            Company response
        """
        result = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            return None
        
        return CompanyResponse.model_validate(company)
    
    # Analytics
    
    async def get_job_analytics(
        self, 
        db: AsyncSession, 
        job_id: int
    ) -> Optional[JobAnalyticsResponse]:
        """
        Get job posting analytics.
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Job analytics data
        """
        # Get job
        job_result = await db.execute(
            select(Job).where(Job.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            return None
        
        # Count applications
        app_count_result = await db.execute(
            select(func.count(JobApplication.id)).where(JobApplication.job_listing_id == job_id)
        )
        total_applications = app_count_result.scalar()
        
        # Count applications by status
        status_counts = {}
        status_result = await db.execute(
            select(JobApplication.status, func.count(JobApplication.id))
                .where(JobApplication.job_listing_id == job_id)
            .group_by(JobApplication.status)
        )
        
        for status, count in status_result.all():
            status_counts[status] = count
        
        return JobAnalyticsResponse(
            job_id=job_id,
            total_applications=total_applications,
            applications_by_status=status_counts,
            views_count=0,  # TODO: Implement view tracking
            posted_date=job.posted_at,
            days_since_posted=(datetime.utcnow() - job.posted_at).days if job.posted_at else 0
        )
    
    async def get_user_application_analytics(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> ApplicationAnalyticsResponse:
        """
        Get user's application analytics.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User application analytics
        """
        # Count total applications
        total_result = await db.execute(
            select(func.count(JobApplication.id)).where(JobApplication.user_id == user_id)
        )
        total_applications = total_result.scalar()
        
        # Count by status
        status_counts = {}
        status_result = await db.execute(
            select(JobApplication.status, func.count(JobApplication.id))
            .where(JobApplication.user_id == user_id)
            .group_by(JobApplication.status)
        )
        
        for status, count in status_result.all():
            status_counts[status] = count
        
        # Calculate response rate
        responded = status_counts.get("interview", 0) + status_counts.get("offer", 0) + status_counts.get("rejected", 0)
        response_rate = (responded / total_applications * 100) if total_applications > 0 else 0
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_result = await db.execute(
            select(func.count(JobApplication.id))
            .where(
                and_(
                    JobApplication.user_id == user_id,
                    JobApplication.applied_at >= thirty_days_ago
                )
            )
        )
        recent_applications = recent_result.scalar()
        
        return ApplicationAnalyticsResponse(
            user_id=user_id,
            total_applications=total_applications,
            applications_by_status=status_counts,
            response_rate=response_rate,
            applications_last_30_days=recent_applications,
            avg_response_time_days=0  # TODO: Calculate based on status change timestamps
        )


# Global job service instance
job_service = JobService()