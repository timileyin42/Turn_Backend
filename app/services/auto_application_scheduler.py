"""
Background task scheduler for auto-application job matching.
Periodically scans for new jobs and matches them with user profiles.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.logger import logger
from app.database.user_models import User, Profile
from app.database.auto_application_models import (
    PendingAutoApplication, AutoApplicationLog, JobMatchNotification,
    AutoApplicationStatus, JobMatchNotificationType
)
from app.services.auto_application_service import auto_application_service, AutoApplicationCriteria
from app.services.email_service import email_service


class AutoApplicationScheduler:
    """
    Background scheduler for auto-application job matching and processing.
    """
    
    def __init__(self):
        self.logger = logger
        self.is_running = False
        self.scan_interval_minutes = 60  # Scan every hour
        self.max_concurrent_users = 10   # Process max 10 users concurrently
        
    async def start_scheduler(self):
        """Start the background job matching scheduler."""
        self.is_running = True
        self.logger.info("Auto-application scheduler started")
        
        while self.is_running:
            try:
                await self.run_job_matching_cycle()
                await asyncio.sleep(self.scan_interval_minutes * 60)  # Convert to seconds
            except Exception as e:
                self.logger.error(f"Error in job matching cycle: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop_scheduler(self):
        """Stop the background scheduler."""
        self.is_running = False
        self.logger.info("Auto-application scheduler stopped")
    
    async def run_job_matching_cycle(self):
        """Run a complete job matching cycle for all eligible users."""
        self.logger.info("Starting job matching cycle")
        
        async for db in get_db():
            try:
                # Get users with auto-apply enabled
                eligible_users = await self._get_eligible_users(db)
                self.logger.info(f"Found {len(eligible_users)} eligible users for job matching")
                
                if not eligible_users:
                    return
                
                # Process users in batches
                for i in range(0, len(eligible_users), self.max_concurrent_users):
                    batch = eligible_users[i:i + self.max_concurrent_users]
                    await self._process_user_batch(db, batch)
                
                self.logger.info("Job matching cycle completed")
                
            except Exception as e:
                self.logger.error(f"Error in job matching cycle: {str(e)}")
            finally:
                await db.close()
    
    async def _get_eligible_users(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get users eligible for auto job matching."""
        # Get users with auto-apply enabled and complete profiles
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile).selectinload(Profile.skills))
            .join(Profile)
            .where(
                and_(
                    User.is_active == True,
                    User.is_verified == True,
                    Profile.auto_apply_enabled == True,
                    Profile.is_complete == True,
                    Profile.completion_percentage >= 70  # At least 70% complete
                )
            )
        )
        users = result.scalars().all()
        
        eligible_users = []
        current_time = datetime.utcnow()
        
        for user in users:
            profile = user.profile
            
            # Check if user hasn't been processed recently
            last_scan_time = getattr(profile, 'last_job_scan_at', None)
            if last_scan_time:
                time_since_last_scan = current_time - last_scan_time
                if time_since_last_scan < timedelta(hours=12):  # Don't scan more than twice per day
                    continue
            
            # Check daily application limit
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            today_applications = await db.scalar(
                select(func.count(PendingAutoApplication.id))
                .where(
                    and_(
                        PendingAutoApplication.user_id == user.id,
                        PendingAutoApplication.created_at >= today_start,
                        PendingAutoApplication.status.in_([
                            AutoApplicationStatus.PENDING_APPROVAL,
                            AutoApplicationStatus.APPROVED,
                            AutoApplicationStatus.SUBMITTED
                        ])
                    )
                )
            )
            
            if today_applications >= profile.max_daily_auto_applications:
                continue
            
            # Check if within user's preferred time window
            if not self._is_within_application_window(profile, current_time):
                continue
            
            eligible_users.append({
                "user": user,
                "profile": profile,
                "today_applications": today_applications,
                "remaining_quota": profile.max_daily_auto_applications - today_applications
            })
        
        return eligible_users
    
    async def _process_user_batch(self, db: AsyncSession, user_batch: List[Dict[str, Any]]):
        """Process a batch of users concurrently."""
        tasks = [
            self._process_single_user(db, user_data)
            for user_data in user_batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for i, result in enumerate(results):
            user_data = user_batch[i]
            user_id = user_data["user"].id
            
            if isinstance(result, Exception):
                self.logger.error(f"Error processing user {user_id}: {str(result)}")
            else:
                self.logger.info(f"Processed user {user_id}: {result}")
    
    async def _process_single_user(self, db: AsyncSession, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process job matching for a single user."""
        user = user_data["user"]
        profile = user_data["profile"]
        remaining_quota = user_data["remaining_quota"]
        
        try:
            # Create search criteria from user preferences
            criteria = AutoApplicationCriteria(
                min_match_score=profile.min_match_score_threshold,
                max_daily_applications=remaining_quota,
                preferred_locations=profile.preferred_locations or [],
                required_skills=profile.required_skills or [],
                excluded_companies=profile.excluded_companies or [],
                salary_min=profile.salary_expectations_min,
                salary_max=profile.salary_expectations_max,
                remote_only=profile.auto_apply_only_remote,
                experience_level_match=True
            )
            
            # Find job matches
            matches = await auto_application_service.find_job_matches_for_user(
                db=db,
                user_id=user.id,
                criteria=criteria
            )
            
            if not matches:
                # Update last scan time even if no matches
                await self._update_last_scan_time(db, user.id)
                return {"user_id": user.id, "matches_found": 0, "applications_created": 0}
            
            # Process matches
            applications_created = 0
            notifications_sent = 0
            
            for match in matches[:remaining_quota]:
                try:
                    # Generate application materials
                    application_materials = await auto_application_service.generate_ai_application(
                        db=db,
                        user_id=user.id,
                        job_data=match["job"]
                    )
                    
                    # Create pending application
                    pending_app = await self._create_pending_application(
                        db=db,
                        user_id=user.id,
                        match=match,
                        application_materials=application_materials
                    )
                    
                    if pending_app:
                        applications_created += 1
                        
                        # Create notification
                        await self._create_job_match_notification(
                            db=db,
                            user_id=user.id,
                            pending_application_id=pending_app.id,
                            match=match
                        )
                        notifications_sent += 1
                        
                        # If manual approval not required, auto-submit
                        if not profile.require_manual_approval:
                            await self._auto_submit_application(db, pending_app.id, user.id)
                    
                except Exception as e:
                    self.logger.error(f"Error processing match for user {user.id}: {str(e)}")
                    continue
            
            # Update last scan time
            await self._update_last_scan_time(db, user.id)
            
            # Send summary email if applications were created
            if applications_created > 0:
                await self._send_job_match_summary_email(
                    db=db,
                    user=user,
                    applications_created=applications_created,
                    matches_found=len(matches)
                )
            
            # Log activity
            await self._log_job_matching_activity(
                db=db,
                user_id=user.id,
                matches_found=len(matches),
                applications_created=applications_created
            )
            
            return {
                "user_id": user.id,
                "matches_found": len(matches),
                "applications_created": applications_created,
                "notifications_sent": notifications_sent
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user {user.id}: {str(e)}")
            raise
    
    async def _create_pending_application(
        self,
        db: AsyncSession,
        user_id: int,
        match: Dict[str, Any],
        application_materials: Dict[str, Any]
    ) -> PendingAutoApplication:
        """Create a pending auto-application record."""
        job = match["job"]
        
        # Check if similar application already exists
        existing = await db.execute(
            select(PendingAutoApplication)
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.company_name == job.get("company", ""),
                    PendingAutoApplication.job_title == job.get("title", ""),
                    PendingAutoApplication.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            )
        )
        
        if existing.scalar_one_or_none():
            return None  # Skip duplicate
        
        pending_app = PendingAutoApplication(
            user_id=user_id,
            external_job_id=job.get("id"),
            job_title=job.get("title", ""),
            company_name=job.get("company", ""),
            job_url=job.get("url"),
            job_description=job.get("description", "")[:2000],  # Truncate
            salary_range=job.get("salary_range"),
            location=job.get("location"),
            employment_type=job.get("employment_type"),
            match_score=match["similarity_score"],
            match_reasons=match["match_reasons"],
            auto_apply_score=match["auto_apply_score"],
            generated_cover_letter=application_materials["cover_letter"],
            cv_customizations=application_materials["cv_customizations"],
            application_summary=application_materials["application_summary"],
            confidence_score=application_materials["confidence_score"],
            status=AutoApplicationStatus.PENDING_APPROVAL,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Expire in 7 days
        )
        
        db.add(pending_app)
        await db.commit()
        await db.refresh(pending_app)
        
        return pending_app
    
    async def _create_job_match_notification(
        self,
        db: AsyncSession,
        user_id: int,
        pending_application_id: int,
        match: Dict[str, Any]
    ):
        """Create job match notification for user."""
        job = match["job"]
        
        notification = JobMatchNotification(
            user_id=user_id,
            pending_application_id=pending_application_id,
            notification_type=JobMatchNotificationType.NEW_MATCH,
            title=f"New Job Match: {job.get('title', 'Position')} at {job.get('company', 'Company')}",
            message=f"We found a great job match for you! This position has a {match['similarity_score']:.0%} match with your profile. Review and approve the auto-generated application.",
            action_url=f"/dashboard/auto-apply/pending/{pending_application_id}",
            job_title=job.get("title"),
            company_name=job.get("company"),
            match_score=match["similarity_score"],
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(notification)
        await db.commit()
    
    async def _auto_submit_application(self, db: AsyncSession, pending_app_id: int, user_id: int):
        """Auto-submit application without manual approval."""
        # Get pending application
        result = await db.execute(
            select(PendingAutoApplication).where(PendingAutoApplication.id == pending_app_id)
        )
        pending_app = result.scalar_one_or_none()
        
        if not pending_app:
            return
        
        try:
            # Submit application
            job_data = {
                "id": pending_app.external_job_id,
                "title": pending_app.job_title,
                "company": pending_app.company_name,
                "url": pending_app.job_url,
                "description": pending_app.job_description
            }
            
            application_materials = {
                "cover_letter": pending_app.generated_cover_letter,
                "cv_customizations": pending_app.cv_customizations,
                "application_summary": pending_app.application_summary,
                "confidence_score": pending_app.confidence_score
            }
            
            result = await auto_application_service.submit_auto_application(
                db=db,
                user_id=user_id,
                job_data=job_data,
                application_materials=application_materials,
                user_approved=True  # Auto-approved
            )
            
            # Update pending application status
            pending_app.status = AutoApplicationStatus.SUBMITTED
            pending_app.processed_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            # Mark as failed
            pending_app.status = AutoApplicationStatus.FAILED
            pending_app.submission_error = str(e)
            await db.commit()
            self.logger.error(f"Auto-submission failed for pending app {pending_app_id}: {str(e)}")
    
    async def _update_last_scan_time(self, db: AsyncSession, user_id: int):
        """Update the last job scan time for user."""
        await db.execute(
            update(Profile)
            .where(Profile.user_id == user_id)
            .values(last_job_scan_at=datetime.utcnow())
        )
        await db.commit()
    
    async def _send_job_match_summary_email(
        self,
        db: AsyncSession,
        user: User,
        applications_created: int,
        matches_found: int
    ):
        """Send job match summary email to user."""
        try:
            await email_service.send_job_match_summary(
                user_email=user.email,
                user_name=user.profile.first_name or "User",
                matches_found=matches_found,
                applications_created=applications_created,
                dashboard_url="/dashboard/auto-apply"
            )
        except Exception as e:
            self.logger.error(f"Error sending job match email to user {user.id}: {str(e)}")
    
    async def _log_job_matching_activity(
        self,
        db: AsyncSession,
        user_id: int,
        matches_found: int,
        applications_created: int
    ):
        """Log job matching activity."""
        log_entry = AutoApplicationLog(
            user_id=user_id,
            activity_type="job_matching_scan",
            activity_description=f"Automated job matching scan completed. Found {matches_found} matches, created {applications_created} pending applications.",
            activity_data={
                "matches_found": matches_found,
                "applications_created": applications_created,
                "scan_timestamp": datetime.utcnow().isoformat()
            },
            success=True
        )
        
        db.add(log_entry)
        await db.commit()
    
    def _is_within_application_window(self, profile: Profile, current_time: datetime) -> bool:
        """Check if current time is within user's preferred application window."""
        # For now, always return True
        # In a full implementation, you'd check auto_apply_window_start/end times
        # and auto_apply_days from the extended settings
        return True
    
    # Manual trigger methods
    
    async def trigger_user_job_matching(self, user_id: int) -> Dict[str, Any]:
        """Manually trigger job matching for a specific user."""
        async for db in get_db():
            try:
                # Get user
                result = await db.execute(
                    select(User)
                    .options(selectinload(User.profile))
                    .where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user or not user.profile:
                    return {"error": "User or profile not found"}
                
                if not user.profile.auto_apply_enabled:
                    return {"error": "Auto-apply not enabled for user"}
                
                # Process user
                user_data = {
                    "user": user,
                    "profile": user.profile,
                    "today_applications": 0,
                    "remaining_quota": user.profile.max_daily_auto_applications
                }
                
                result = await self._process_single_user(db, user_data)
                return result
                
            except Exception as e:
                self.logger.error(f"Error in manual job matching for user {user_id}: {str(e)}")
                return {"error": str(e)}
            finally:
                await db.close()
    
    async def cleanup_expired_applications(self):
        """Clean up expired pending applications."""
        async for db in get_db():
            try:
                # Update expired applications
                await db.execute(
                    update(PendingAutoApplication)
                    .where(
                        and_(
                            PendingAutoApplication.expires_at < datetime.utcnow(),
                            PendingAutoApplication.status == AutoApplicationStatus.PENDING_APPROVAL
                        )
                    )
                    .values(status=AutoApplicationStatus.EXPIRED)
                )
                
                await db.commit()
                self.logger.info("Cleaned up expired pending applications")
                
            except Exception as e:
                self.logger.error(f"Error cleaning up expired applications: {str(e)}")
            finally:
                await db.close()


# Global scheduler instance
auto_application_scheduler = AutoApplicationScheduler()