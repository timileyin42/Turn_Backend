"""
Platform management service for core platform features, learning modules, and analytics.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc, distinct
from sqlalchemy.orm import selectinload

from app.database.platform_models import (
    LearningPath, SimulationStatus, CVStatus, 
    JobApplicationStatus, PortfolioVisibility,
    LearningModule, UserModuleProgress, FeatureUsageTracking
)
from app.database.user_models import User, Profile
from app.database.cv_models import CV
from app.database.job_models import JobApplication
from app.database.portfolio_models import Portfolio
from app.schemas.platform_schemas import (
    LearningModuleResponse, StartModuleRequest, UserProgressResponse,
    SimulationResponse, LearningPathResponse, PlatformAnalyticsResponse
)
from app.core.logger import logger


class PlatformService:
    """Service for platform-wide features and analytics."""
    
    async def get_learning_paths(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None
    ) -> List[LearningPathResponse]:
        """Get available learning paths, optionally with user progress."""
        try:
            learning_paths = []
            
            for path in LearningPath:
                # Get total modules for this path
                modules_result = await db.execute(
                    select(func.count(LearningModule.id))
                    .where(
                        and_(
                            LearningModule.learning_path == path,
                            LearningModule.is_active == True
                        )
                    )
                )
                modules_count = modules_result.scalar() or 0
                
                # Calculate total duration
                duration_result = await db.execute(
                    select(func.sum(LearningModule.estimated_duration_minutes))
                    .where(
                        and_(
                            LearningModule.learning_path == path,
                            LearningModule.is_active == True
                        )
                    )
                )
                total_duration = duration_result.scalar() or 0
                
                # Get user progress if user_id provided
                progress_percentage = 0
                is_completed = False
                
                if user_id and modules_count > 0:
                    # Get completed modules count
                    completed_result = await db.execute(
                        select(func.count(UserModuleProgress.id))
                        .join(LearningModule)
                        .where(
                            and_(
                                UserModuleProgress.user_id == user_id,
                                UserModuleProgress.is_completed == True,
                                LearningModule.learning_path == path
                            )
                        )
                    )
                    completed_count = completed_result.scalar() or 0
                    progress_percentage = (completed_count / modules_count) * 100
                    is_completed = completed_count == modules_count
                
                # Determine difficulty level based on path
                difficulty_map = {
                    LearningPath.AGILE_SCRUM: 2,
                    LearningPath.WATERFALL_TRADITIONAL: 1,
                    LearningPath.HYBRID_APPROACHES: 3,
                    LearningPath.LEADERSHIP_SOFT_SKILLS: 2,
                    LearningPath.TOOLS_TECHNOLOGY: 3,
                    LearningPath.CERTIFICATION_PREP: 4
                }
                
                learning_paths.append(LearningPathResponse(
                    id=path.value,
                    name=path.value.replace('_', ' ').title(),
                    description=self._get_path_description(path),
                    modules_count=modules_count,
                    estimated_duration=total_duration,
                    difficulty_level=difficulty_map.get(path, 2),
                    is_completed=is_completed,
                    progress_percentage=round(progress_percentage, 1)
                ))
            
            return learning_paths
            
        except Exception as e:
            logger.error(f"Error getting learning paths: {str(e)}")
            raise e
    
    async def get_user_learning_progress(
        self,
        db: AsyncSession,
        user_id: int,
        learning_path: Optional[LearningPath] = None
    ) -> Dict[str, Any]:
        """Get comprehensive learning progress for a user."""
        try:
            # Get total modules
            total_modules_query = select(func.count(LearningModule.id)).where(
                LearningModule.is_active == True
            )
            if learning_path:
                total_modules_query = total_modules_query.where(
                    LearningModule.learning_path == learning_path
                )
            
            total_modules_result = await db.execute(total_modules_query)
            total_modules = total_modules_result.scalar() or 0
            
            # Get completed modules
            completed_modules_query = select(func.count(UserModuleProgress.id)).join(
                LearningModule
            ).where(
                and_(
                    UserModuleProgress.user_id == user_id,
                    UserModuleProgress.is_completed == True,
                    LearningModule.is_active == True
                )
            )
            if learning_path:
                completed_modules_query = completed_modules_query.where(
                    LearningModule.learning_path == learning_path
                )
            
            completed_result = await db.execute(completed_modules_query)
            completed_modules = completed_result.scalar() or 0
            
            # Get total time spent
            time_result = await db.execute(
                select(func.sum(UserModuleProgress.time_spent_minutes))
                .where(UserModuleProgress.user_id == user_id)
            )
            total_time_spent = time_result.scalar() or 0
            
            # Calculate current streak (consecutive days with activity)
            current_streak = await self._calculate_learning_streak(db, user_id)
            
            # Get progress by learning path
            learning_paths_progress = {}
            for path in LearningPath:
                path_modules_result = await db.execute(
                    select(func.count(LearningModule.id))
                    .where(
                        and_(
                            LearningModule.learning_path == path,
                            LearningModule.is_active == True
                        )
                    )
                )
                path_total = path_modules_result.scalar() or 0
                
                path_completed_result = await db.execute(
                    select(func.count(UserModuleProgress.id))
                    .join(LearningModule)
                    .where(
                        and_(
                            UserModuleProgress.user_id == user_id,
                            UserModuleProgress.is_completed == True,
                            LearningModule.learning_path == path
                        )
                    )
                )
                path_completed = path_completed_result.scalar() or 0
                
                learning_paths_progress[path.value] = {
                    "total_modules": path_total,
                    "completed_modules": path_completed,
                    "progress_percentage": (path_completed / path_total * 100) if path_total > 0 else 0
                }
            
            # Get recent activity (last 10 activities)
            recent_activities = await db.execute(
                select(UserModuleProgress)
                .options(selectinload(UserModuleProgress.module))
                .where(UserModuleProgress.user_id == user_id)
                .order_by(desc(UserModuleProgress.last_accessed_at))
                .limit(10)
            )
            recent_activity = [
                {
                    "module_title": activity.module.title if activity.module else "Unknown",
                    "progress": activity.progress_percentage,
                    "last_accessed": activity.last_accessed_at.isoformat() if activity.last_accessed_at else None,
                    "completed": activity.is_completed
                }
                for activity in recent_activities.scalars().all()
            ]
            
            progress_data = {
                "user_id": user_id,
                "total_modules": total_modules,
                "completed_modules": completed_modules,
                "completion_percentage": (completed_modules / total_modules * 100) if total_modules > 0 else 0,
                "total_time_spent_minutes": total_time_spent,
                "total_time_spent_hours": round(total_time_spent / 60, 1),
                "current_streak_days": current_streak,
                "learning_paths": learning_paths_progress,
                "recent_activity": recent_activity,
                "achievements": await self._get_user_achievements(db, user_id)
            }
            
            # Add learning path specific progress if requested
            if learning_path:
                path_progress = learning_paths_progress.get(learning_path.value, {})
                estimated_completion = None
                if path_progress.get("progress_percentage", 0) > 0:
                    # Rough estimate based on current pace
                    remaining_modules = path_progress["total_modules"] - path_progress["completed_modules"]
                    if completed_modules > 0 and total_time_spent > 0:
                        avg_time_per_module = total_time_spent / completed_modules
                        estimated_days = (remaining_modules * avg_time_per_module) / 60 / 2  # Assuming 2 hours per day
                        estimated_completion = (datetime.utcnow() + timedelta(days=estimated_days)).isoformat()
                
                progress_data["current_path"] = {
                    "path": learning_path.value,
                    "progress_percentage": path_progress.get("progress_percentage", 0),
                    "modules_completed": path_progress.get("completed_modules", 0),
                    "modules_total": path_progress.get("total_modules", 0),
                    "estimated_completion": estimated_completion
                }
            
            return progress_data
            
        except Exception as e:
            logger.error(f"Error getting user learning progress: {str(e)}")
            raise e
    
    async def get_platform_analytics(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        admin_view: bool = False
    ) -> PlatformAnalyticsResponse:
        """Get platform-wide analytics and statistics."""
        try:
            if admin_view:
                # Admin view - platform-wide stats
                
                # Total users
                total_users_result = await db.execute(select(func.count(User.id)))
                total_users = total_users_result.scalar() or 0
                
                # Active users today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                active_today_result = await db.execute(
                    select(func.count(distinct(UserModuleProgress.user_id)))
                    .where(UserModuleProgress.last_accessed_at >= today_start)
                )
                active_users_today = active_today_result.scalar() or 0
                
                # Total learning modules
                total_modules_result = await db.execute(
                    select(func.count(LearningModule.id))
                    .where(LearningModule.is_active == True)
                )
                total_learning_modules = total_modules_result.scalar() or 0
                
                # Total simulations completed (would need Simulation table)
                total_simulations_completed = 0  # Placeholder
                
                # Total CVs created
                total_cvs_result = await db.execute(select(func.count(CV.id)))
                total_cvs_created = total_cvs_result.scalar() or 0
                
                # Total job applications
                total_apps_result = await db.execute(select(func.count(JobApplication.id)))
                total_job_applications = total_apps_result.scalar() or 0
                
                # Popular learning paths
                popular_paths_result = await db.execute(
                    select(
                        LearningModule.learning_path,
                        func.count(UserModuleProgress.id).label('usage_count')
                    )
                    .join(UserModuleProgress)
                    .group_by(LearningModule.learning_path)
                    .order_by(desc('usage_count'))
                    .limit(5)
                )
                popular_learning_paths = [
                    {"path": row[0].value, "users": row[1]}
                    for row in popular_paths_result.all()
                ]
                
                # User engagement stats
                avg_session_result = await db.execute(
                    select(func.avg(UserModuleProgress.time_spent_minutes))
                )
                avg_session_duration = avg_session_result.scalar() or 0
                
                # Daily active users (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                dau_result = await db.execute(
                    select(func.count(distinct(UserModuleProgress.user_id)))
                    .where(UserModuleProgress.last_accessed_at >= week_ago)
                )
                daily_active_users = dau_result.scalar() or 0
                
                analytics = PlatformAnalyticsResponse(
                    total_users=total_users,
                    active_users_today=active_users_today,
                    total_learning_modules=total_learning_modules,
                    total_simulations_completed=total_simulations_completed,
                    total_cvs_created=total_cvs_created,
                    total_job_applications=total_job_applications,
                    popular_learning_paths=popular_learning_paths,
                    user_engagement_stats={
                        "avg_session_duration_minutes": round(avg_session_duration, 1),
                        "daily_active_users": daily_active_users,
                        "weekly_retention": round((daily_active_users / total_users * 100) if total_users > 0 else 0, 1),
                        "monthly_retention": 0  # Would need more complex calculation
                    }
                )
            else:
                # User view - personal stats
                
                # Modules completed
                modules_completed_result = await db.execute(
                    select(func.count(UserModuleProgress.id))
                    .where(
                        and_(
                            UserModuleProgress.user_id == user_id,
                            UserModuleProgress.is_completed == True
                        )
                    )
                )
                modules_completed = modules_completed_result.scalar() or 0
                
                # Total learning time
                time_result = await db.execute(
                    select(func.sum(UserModuleProgress.time_spent_minutes))
                    .where(UserModuleProgress.user_id == user_id)
                )
                total_learning_time = time_result.scalar() or 0
                
                # Simulations completed (placeholder)
                simulations_completed = 0
                
                # CVs created
                cvs_result = await db.execute(
                    select(func.count(CV.id))
                    .where(CV.user_id == user_id)
                )
                cvs_created = cvs_result.scalar() or 0
                
                # Job applications sent
                apps_result = await db.execute(
                    select(func.count(JobApplication.id))
                    .where(JobApplication.user_id == user_id)
                )
                job_applications_sent = apps_result.scalar() or 0
                
                # Current learning streak
                current_learning_streak = await self._calculate_learning_streak(db, user_id)
                
                # Achievements earned
                achievements_earned = len(await self._get_user_achievements(db, user_id))
                
                # Portfolio views
                portfolio_views_result = await db.execute(
                    select(func.sum(Portfolio.view_count))
                    .where(Portfolio.user_id == user_id)
                )
                portfolio_views = portfolio_views_result.scalar() or 0
                
                analytics = PlatformAnalyticsResponse(
                    user_id=user_id,
                    modules_completed=modules_completed,
                    total_learning_time=total_learning_time,
                    simulations_completed=simulations_completed,
                    cvs_created=cvs_created,
                    job_applications_sent=job_applications_sent,
                    current_learning_streak=current_learning_streak,
                    achievements_earned=achievements_earned,
                    portfolio_views=portfolio_views
                )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting platform analytics: {str(e)}")
            raise e
    
    async def get_platform_features(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Get available platform features and their status for a user."""
        try:
            features = {
                "ai_coaching": {
                    "enabled": True,
                    "description": "AI-powered project management coaching",
                    "usage_count": 0,
                    "last_used": None
                },
                "cv_builder": {
                    "enabled": True,
                    "description": "Professional CV/Resume builder",
                    "cvs_created": 0,
                    "last_used": None
                },
                "job_search": {
                    "enabled": True,
                    "description": "Job search and application tracking",
                    "applications_sent": 0,
                    "last_used": None
                },
                "project_simulations": {
                    "enabled": True,
                    "description": "Interactive project management simulations",
                    "simulations_completed": 0,
                    "last_used": None
                },
                "portfolio": {
                    "enabled": True,
                    "description": "Professional portfolio management",
                    "portfolios_created": 0,
                    "last_used": None
                },
                "learning_modules": {
                    "enabled": True,
                    "description": "Structured learning paths and modules",
                    "modules_completed": 0,
                    "last_used": None
                }
            }
            
            # Get user's CVs count and last usage
            cvs_result = await db.execute(
                select(func.count(CV.id), func.max(CV.created_at))
                .where(CV.user_id == user_id)
            )
            cv_count, cv_last_used = cvs_result.first()
            features["cv_builder"]["cvs_created"] = cv_count or 0
            features["cv_builder"]["last_used"] = cv_last_used.isoformat() if cv_last_used else None
            
            # Get user's job applications count and last usage
            apps_result = await db.execute(
                select(func.count(JobApplication.id), func.max(JobApplication.applied_at))
                .where(JobApplication.user_id == user_id)
            )
            apps_count, apps_last_used = apps_result.first()
            features["job_search"]["applications_sent"] = apps_count or 0
            features["job_search"]["last_used"] = apps_last_used.isoformat() if apps_last_used else None
            
            # Get user's portfolios count and last usage
            portfolios_result = await db.execute(
                select(func.count(Portfolio.id), func.max(Portfolio.created_at))
                .where(Portfolio.user_id == user_id)
            )
            portfolio_count, portfolio_last_used = portfolios_result.first()
            features["portfolio"]["portfolios_created"] = portfolio_count or 0
            features["portfolio"]["last_used"] = portfolio_last_used.isoformat() if portfolio_last_used else None
            
            # Get user's completed learning modules count and last usage
            modules_result = await db.execute(
                select(
                    func.count(UserModuleProgress.id),
                    func.max(UserModuleProgress.last_accessed_at)
                )
                .where(
                    and_(
                        UserModuleProgress.user_id == user_id,
                        UserModuleProgress.is_completed == True
                    )
                )
            )
            modules_count, modules_last_used = modules_result.first()
            features["learning_modules"]["modules_completed"] = modules_count or 0
            features["learning_modules"]["last_used"] = modules_last_used.isoformat() if modules_last_used else None
            
            # Get feature usage from tracking table
            usage_result = await db.execute(
                select(
                    FeatureUsageTracking.feature_name,
                    func.count(FeatureUsageTracking.id).label('count'),
                    func.max(FeatureUsageTracking.timestamp).label('last_used')
                )
                .where(FeatureUsageTracking.user_id == user_id)
                .group_by(FeatureUsageTracking.feature_name)
            )
            
            for row in usage_result.all():
                feature_name = row[0]
                usage_count = row[1]
                last_used = row[2]
                
                if feature_name in features:
                    features[feature_name]["usage_count"] = usage_count
                    if last_used and not features[feature_name]["last_used"]:
                        features[feature_name]["last_used"] = last_used.isoformat()
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting platform features: {str(e)}")
            raise e
    
    async def track_feature_usage(
        self,
        db: AsyncSession,
        user_id: int,
        feature_name: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track usage of platform features for analytics."""
        try:
            # Create feature usage tracking record
            usage_record = FeatureUsageTracking(
                user_id=user_id,
                feature_name=feature_name,
                action=action,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            db.add(usage_record)
            await db.commit()
            
            logger.info(
                f"Tracked feature usage: user_id={user_id}, feature={feature_name}, "
                f"action={action}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
            await db.rollback()
            return False
    
    async def get_system_status(self, db: AsyncSession) -> Dict[str, Any]:
        """Get overall system health and status."""
        try:
            status = {
                "database": "unknown",
                "api": "operational",
                "ai_services": "unknown",
                "file_storage": "unknown",
                "email_service": "unknown",
                "last_updated": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            
            # Check database connectivity
            try:
                await db.execute(select(func.count(User.id)))
                status["database"] = "healthy"
            except Exception as db_error:
                logger.error(f"Database health check failed: {str(db_error)}")
                status["database"] = "unhealthy"
                status["database_error"] = str(db_error)
            
            # Check AI service (if available)
            try:
                from app.services.ai_service import ai_service
                # Simple check - if we can import, assume operational
                status["ai_services"] = "operational"
            except Exception as ai_error:
                logger.error(f"AI service check failed: {str(ai_error)}")
                status["ai_services"] = "unavailable"
            
            # Check email service (if available)
            try:
                from app.services.email_service import email_service
                # If we can import, assume operational
                status["email_service"] = "operational"
            except Exception as email_error:
                logger.error(f"Email service check failed: {str(email_error)}")
                status["email_service"] = "unavailable"
            
            # Check file storage (if available)
            try:
                from app.services.cloudinary_service import cloudinary_service
                # If we can import, assume operational
                status["file_storage"] = "operational"
            except Exception as storage_error:
                logger.error(f"File storage check failed: {str(storage_error)}")
                status["file_storage"] = "unavailable"
            
            # Calculate overall health
            services = ["database", "api", "ai_services", "file_storage", "email_service"]
            healthy_count = sum(
                1 for service in services 
                if status.get(service) in ["healthy", "operational"]
            )
            status["overall_health"] = "healthy" if healthy_count >= 4 else "degraded" if healthy_count >= 2 else "unhealthy"
            status["services_operational"] = f"{healthy_count}/{len(services)}"
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking system status: {str(e)}")
            return {
                "database": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat(),
                "overall_health": "unhealthy"
            }
    
    # Helper methods
    
    def _get_path_description(self, learning_path: str) -> str:
        """Get description for a learning path."""
        descriptions = {
            "frontend_development": "Master modern frontend technologies including HTML, CSS, JavaScript, React, and responsive design.",
            "backend_development": "Learn server-side programming, databases, APIs, and system architecture.",
            "fullstack_development": "Comprehensive training in both frontend and backend development.",
            "data_science": "Explore data analysis, machine learning, statistics, and data visualization.",
            "devops": "Learn CI/CD, cloud platforms, containerization, and infrastructure automation.",
            "mobile_development": "Build native and cross-platform mobile applications.",
            "ui_ux_design": "Master user interface design, user experience principles, and design tools.",
            "cloud_computing": "Learn cloud platforms, serverless architecture, and cloud-native development.",
            "cybersecurity": "Understand security principles, ethical hacking, and system protection.",
            "ai_ml": "Deep dive into artificial intelligence, machine learning, and neural networks.",
            "blockchain": "Learn blockchain technology, smart contracts, and decentralized applications.",
            "game_development": "Create games using popular engines and programming techniques."
        }
        return descriptions.get(learning_path, "Comprehensive learning path for career development.")
    
    async def _calculate_learning_streak(self, db: AsyncSession, user_id: int) -> int:
        """Calculate user's current learning streak in days."""
        try:
            # Get user's learning activity dates (when they accessed modules)
            activities_result = await db.execute(
                select(func.date(UserModuleProgress.last_accessed_at))
                .where(UserModuleProgress.user_id == user_id)
                .distinct()
                .order_by(desc(func.date(UserModuleProgress.last_accessed_at)))
            )
            
            activity_dates = [row[0] for row in activities_result.all()]
            
            if not activity_dates:
                return 0
            
            # Check if there's activity today or yesterday (to continue streak)
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            
            if activity_dates[0] not in [today, yesterday]:
                return 0  # Streak broken
            
            # Count consecutive days
            streak = 1
            current_date = activity_dates[0]
            
            for i in range(1, len(activity_dates)):
                expected_date = current_date - timedelta(days=1)
                if activity_dates[i] == expected_date:
                    streak += 1
                    current_date = activity_dates[i]
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating learning streak: {str(e)}")
            return 0
    
    async def _get_user_achievements(self, db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """Get user's earned achievements."""
        try:
            achievements = []
            
            # Count completed modules
            modules_result = await db.execute(
                select(func.count(UserModuleProgress.id))
                .where(
                    and_(
                        UserModuleProgress.user_id == user_id,
                        UserModuleProgress.is_completed == True
                    )
                )
            )
            modules_completed = modules_result.scalar() or 0
            
            # Module completion achievements
            if modules_completed >= 1:
                achievements.append({
                    "id": "first_module",
                    "name": "First Steps",
                    "description": "Completed your first learning module",
                    "icon": "🎓",
                    "earned_at": None
                })
            if modules_completed >= 5:
                achievements.append({
                    "id": "module_enthusiast",
                    "name": "Learning Enthusiast",
                    "description": "Completed 5 learning modules",
                    "icon": "📚",
                    "earned_at": None
                })
            if modules_completed >= 10:
                achievements.append({
                    "id": "module_master",
                    "name": "Knowledge Master",
                    "description": "Completed 10 learning modules",
                    "icon": "🏆",
                    "earned_at": None
                })
            
            # Count CVs created
            cvs_result = await db.execute(
                select(func.count(CV.id))
                .where(CV.user_id == user_id)
            )
            cvs_created = cvs_result.scalar() or 0
            
            if cvs_created >= 1:
                achievements.append({
                    "id": "first_cv",
                    "name": "Professional Profile",
                    "description": "Created your first CV",
                    "icon": "📄",
                    "earned_at": None
                })
            
            # Count job applications
            apps_result = await db.execute(
                select(func.count(JobApplication.id))
                .where(JobApplication.user_id == user_id)
            )
            apps_sent = apps_result.scalar() or 0
            
            if apps_sent >= 1:
                achievements.append({
                    "id": "first_application",
                    "name": "Job Seeker",
                    "description": "Sent your first job application",
                    "icon": "💼",
                    "earned_at": None
                })
            if apps_sent >= 10:
                achievements.append({
                    "id": "application_pro",
                    "name": "Application Pro",
                    "description": "Sent 10 job applications",
                    "icon": "🎯",
                    "earned_at": None
                })
            
            # Calculate learning streak for streak achievements
            streak = await self._calculate_learning_streak(db, user_id)
            
            if streak >= 3:
                achievements.append({
                    "id": "three_day_streak",
                    "name": "Consistency",
                    "description": "Maintained a 3-day learning streak",
                    "icon": "🔥",
                    "earned_at": None
                })
            if streak >= 7:
                achievements.append({
                    "id": "week_streak",
                    "name": "Dedicated Learner",
                    "description": "Maintained a 7-day learning streak",
                    "icon": "⭐",
                    "earned_at": None
                })
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error getting user achievements: {str(e)}")
            return []


# Create service instance
platform_service = PlatformService()