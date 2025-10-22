"""
Auto-Application Dashboard API endpoints.
Provides comprehensive dashboard views for managing auto-application features.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.user_models import User, Profile
from app.database.auto_application_models import (
    PendingAutoApplication, AutoApplicationLog, JobMatchNotification,
    AutoApplicationStatus, JobMatchNotificationType
)
from app.database.job_models import JobApplication
from app.schemas.auto_application_schemas import (
    DashboardSummary, AutoApplicationAnalytics, JobMatchSummary
)

router = APIRouter(prefix="/api/v1/dashboard/auto-apply", tags=["Auto Application Dashboard"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard overview for auto-applications."""
    try:
        user_id = current_user.id
        
        # Get pending applications count
        pending_count = await db.scalar(
            select(func.count(PendingAutoApplication.id))
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.status == AutoApplicationStatus.PENDING_APPROVAL
                )
            )
        )
        
        # Get unread notifications count
        unread_notifications = await db.scalar(
            select(func.count(JobMatchNotification.id))
            .where(
                and_(
                    JobMatchNotification.user_id == user_id,
                    JobMatchNotification.is_read == False
                )
            )
        )
        
        # Get recent applications (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_applications = await db.execute(
            select(PendingAutoApplication)
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= thirty_days_ago
                )
            )
            .order_by(desc(PendingAutoApplication.created_at))
            .limit(5)
        )
        recent_apps = recent_applications.scalars().all()
        
        # Get user settings status
        profile = current_user.profile
        settings_completeness = 0
        missing_settings = []
        
        if profile:
            if profile.auto_apply_enabled:
                settings_completeness += 25
            else:
                missing_settings.append("Enable auto-apply")
                
            if profile.preferred_job_types:
                settings_completeness += 25
            else:
                missing_settings.append("Set preferred job types")
                
            if profile.salary_expectations_min:
                settings_completeness += 25
            else:
                missing_settings.append("Set salary expectations")
                
            if profile.required_skills:
                settings_completeness += 25
            else:
                missing_settings.append("Specify required skills")
        
        settings_status = "complete" if settings_completeness >= 75 else "incomplete"
        
        # Get success metrics
        approved_count = await db.scalar(
            select(func.count(PendingAutoApplication.id))
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.status == AutoApplicationStatus.APPROVED,
                    PendingAutoApplication.created_at >= thirty_days_ago
                )
            )
        )
        
        submitted_count = await db.scalar(
            select(func.count(PendingAutoApplication.id))
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.status == AutoApplicationStatus.SUBMITTED,
                    PendingAutoApplication.created_at >= thirty_days_ago
                )
            )
        )
        
        # Calculate average match score
        avg_match_score = await db.scalar(
            select(func.avg(PendingAutoApplication.match_score))
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= thirty_days_ago
                )
            )
        )
        
        # Generate next actions
        next_actions = []
        if pending_count > 0:
            next_actions.append(f"Review {pending_count} pending applications")
        if not profile or not profile.auto_apply_enabled:
            next_actions.append("Enable auto-apply to start finding matches")
        if settings_completeness < 75:
            next_actions.append("Complete your auto-apply preferences")
        if unread_notifications > 0:
            next_actions.append(f"Check {unread_notifications} new notifications")
        
        if not next_actions:
            next_actions.append("Your auto-apply system is working! Check back later for new matches.")
        
        return {
            "overview": {
                "pending_applications": pending_count or 0,
                "unread_notifications": unread_notifications or 0,
                "settings_completeness": settings_completeness,
                "settings_status": settings_status,
                "auto_apply_enabled": profile.auto_apply_enabled if profile else False
            },
            "recent_activity": [
                {
                    "id": app.id,
                    "job_title": app.job_title,
                    "company": app.company_name,
                    "match_score": app.match_score,
                    "status": app.status.value,
                    "created_at": app.created_at.isoformat()
                }
                for app in recent_apps
            ],
            "metrics": {
                "total_matches_30_days": len(recent_apps),
                "approved_applications": approved_count or 0,
                "submitted_applications": submitted_count or 0,
                "average_match_score": float(avg_match_score) if avg_match_score else 0.0,
                "success_rate": round((submitted_count / max(len(recent_apps), 1)) * 100, 1) if recent_apps else 0.0
            },
            "next_actions": next_actions,
            "missing_settings": missing_settings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard overview: {str(e)}"
        )


@router.get("/analytics")
async def get_auto_application_analytics(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed analytics for auto-applications."""
    try:
        user_id = current_user.id
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Get applications by status for the period
        status_counts = {}
        for status in AutoApplicationStatus:
            count = await db.scalar(
                select(func.count(PendingAutoApplication.id))
                .where(
                    and_(
                        PendingAutoApplication.user_id == user_id,
                        PendingAutoApplication.status == status,
                        PendingAutoApplication.created_at >= start_date
                    )
                )
            )
            status_counts[status.value] = count or 0
        
        # Get daily activity data
        daily_stats = await db.execute(
            text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as applications,
                    AVG(match_score) as avg_match_score,
                    AVG(confidence_score) as avg_confidence
                FROM pending_auto_applications 
                WHERE user_id = :user_id AND created_at >= :start_date
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 30
            """),
            {"user_id": user_id, "start_date": start_date}
        )
        
        daily_data = [
            {
                "date": row.date.isoformat(),
                "applications": row.applications,
                "avg_match_score": float(row.avg_match_score) if row.avg_match_score else 0.0,
                "avg_confidence": float(row.avg_confidence) if row.avg_confidence else 0.0
            }
            for row in daily_stats
        ]
        
        # Get top companies by applications
        company_stats = await db.execute(
            select(
                PendingAutoApplication.company_name,
                func.count(PendingAutoApplication.id).label('application_count'),
                func.avg(PendingAutoApplication.match_score).label('avg_match_score')
            )
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= start_date
                )
            )
            .group_by(PendingAutoApplication.company_name)
            .order_by(desc('application_count'))
            .limit(10)
        )
        
        top_companies = [
            {
                "company": row.company_name,
                "applications": row.application_count,
                "avg_match_score": float(row.avg_match_score)
            }
            for row in company_stats
        ]
        
        # Get job title distribution
        title_stats = await db.execute(
            select(
                PendingAutoApplication.job_title,
                func.count(PendingAutoApplication.id).label('count')
            )
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= start_date
                )
            )
            .group_by(PendingAutoApplication.job_title)
            .order_by(desc('count'))
            .limit(10)
        )
        
        job_titles = [
            {"title": row.job_title, "count": row.count}
            for row in title_stats
        ]
        
        # Calculate totals
        total_applications = sum(status_counts.values())
        successful_applications = status_counts.get('submitted', 0) + status_counts.get('approved', 0)
        
        # Generate recommendations
        recommendations = []
        
        if total_applications == 0:
            recommendations.append("Complete your profile to start getting job matches")
        elif status_counts.get('pending_approval', 0) > 5:
            recommendations.append("You have many pending applications - review and approve them")
        elif successful_applications / max(total_applications, 1) < 0.3:
            recommendations.append("Consider adjusting your match score threshold to get better quality matches")
        
        avg_match_score = await db.scalar(
            select(func.avg(PendingAutoApplication.match_score))
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= start_date
                )
            )
        )
        
        if avg_match_score and avg_match_score < 0.7:
            recommendations.append("Consider updating your skills and preferences for better matches")
        
        profile = current_user.profile
        
        return {
            "period_days": period_days,
            "summary": {
                "total_matches": total_applications,
                "pending_applications": status_counts.get('pending_approval', 0),
                "approved_applications": status_counts.get('approved', 0),
                "submitted_applications": status_counts.get('submitted', 0),
                "rejected_applications": status_counts.get('rejected', 0),
                "average_match_score": float(avg_match_score) if avg_match_score else 0.0,
                "success_rate": round((successful_applications / max(total_applications, 1)) * 100, 1)
            },
            "status_breakdown": status_counts,
            "daily_activity": daily_data,
            "top_companies": top_companies,
            "job_title_distribution": job_titles,
            "settings": {
                "auto_apply_enabled": profile.auto_apply_enabled if profile else False,
                "daily_limit": profile.max_daily_auto_applications if profile else 3,
                "match_threshold": profile.min_match_score_threshold if profile else 0.75,
                "manual_approval": profile.require_manual_approval if profile else True
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analytics: {str(e)}"
        )


@router.get("/activity-feed")
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    activity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's auto-application activity feed."""
    try:
        # Get activity logs
        query = select(AutoApplicationLog).where(
            AutoApplicationLog.user_id == current_user.id
        )
        
        if activity_type:
            query = query.where(AutoApplicationLog.activity_type == activity_type)
        
        query = query.order_by(desc(AutoApplicationLog.created_at)).limit(limit)
        
        result = await db.execute(query)
        activity_logs = result.scalars().all()
        
        # Get recent notifications
        notifications_query = select(JobMatchNotification).where(
            JobMatchNotification.user_id == current_user.id
        ).order_by(desc(JobMatchNotification.created_at)).limit(10)
        
        notifications_result = await db.execute(notifications_query)
        notifications = notifications_result.scalars().all()
        
        # Combine and format activity
        activities = []
        
        # Add logs
        for log in activity_logs:
            activities.append({
                "id": f"log_{log.id}",
                "type": "activity",
                "activity_type": log.activity_type,
                "title": log.activity_description,
                "data": log.activity_data,
                "job_title": log.job_title,
                "company": log.company_name,
                "success": log.success,
                "created_at": log.created_at.isoformat()
            })
        
        # Add notifications
        for notif in notifications:
            activities.append({
                "id": f"notif_{notif.id}",
                "type": "notification",
                "notification_type": notif.notification_type.value,
                "title": notif.title,
                "message": notif.message,
                "job_title": notif.job_title,
                "company": notif.company_name,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat()
            })
        
        # Sort by date
        activities.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "activities": activities[:limit],
            "total_activities": len(activities),
            "activity_types": [
                "job_matching_scan",
                "application_generated", 
                "application_approved",
                "application_submitted",
                "application_failed"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching activity feed: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed performance metrics for auto-applications."""
    try:
        user_id = current_user.id
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        # Get metrics for different periods
        periods = [
            ("last_30_days", thirty_days_ago),
            ("last_90_days", ninety_days_ago)
        ]
        
        metrics = {}
        
        for period_name, start_date in periods:
            # Applications by status
            status_counts = {}
            for status in AutoApplicationStatus:
                count = await db.scalar(
                    select(func.count(PendingAutoApplication.id))
                    .where(
                        and_(
                            PendingAutoApplication.user_id == user_id,
                            PendingAutoApplication.status == status,
                            PendingAutoApplication.created_at >= start_date
                        )
                    )
                )
                status_counts[status.value] = count or 0
            
            # Average scores
            avg_match_score = await db.scalar(
                select(func.avg(PendingAutoApplication.match_score))
                .where(
                    and_(
                        PendingAutoApplication.user_id == user_id,
                        PendingAutoApplication.created_at >= start_date
                    )
                )
            )
            
            avg_confidence = await db.scalar(
                select(func.avg(PendingAutoApplication.confidence_score))
                .where(
                    and_(
                        PendingAutoApplication.user_id == user_id,
                        PendingAutoApplication.created_at >= start_date
                    )
                )
            )
            
            # Response rate (if we have actual job applications data)
            total_submitted = status_counts.get('submitted', 0)
            
            metrics[period_name] = {
                "total_matches": sum(status_counts.values()),
                "status_breakdown": status_counts,
                "average_match_score": float(avg_match_score) if avg_match_score else 0.0,
                "average_confidence": float(avg_confidence) if avg_confidence else 0.0,
                "approval_rate": round(
                    (status_counts.get('approved', 0) + status_counts.get('submitted', 0)) / 
                    max(sum(status_counts.values()), 1) * 100, 1
                ),
                "submission_rate": round(
                    total_submitted / max(sum(status_counts.values()), 1) * 100, 1
                )
            }
        
        # Profile strength analysis
        profile = current_user.profile
        profile_strength = {
            "completeness": profile.completion_percentage if profile else 0,
            "skills_count": len(profile.required_skills) if profile and profile.required_skills else 0,
            "preferences_set": bool(profile and profile.preferred_job_types),
            "salary_range_set": bool(profile and profile.salary_expectations_min),
            "auto_apply_configured": bool(profile and profile.auto_apply_enabled)
        }
        
        # Industry/company insights
        company_performance = await db.execute(
            select(
                PendingAutoApplication.company_name,
                func.count(PendingAutoApplication.id).label('total'),
                func.sum(func.case(
                    (PendingAutoApplication.status == AutoApplicationStatus.APPROVED, 1), 
                    else_=0
                )).label('approved'),
                func.avg(PendingAutoApplication.match_score).label('avg_score')
            )
            .where(
                and_(
                    PendingAutoApplication.user_id == user_id,
                    PendingAutoApplication.created_at >= ninety_days_ago
                )
            )
            .group_by(PendingAutoApplication.company_name)
            .having(func.count(PendingAutoApplication.id) >= 2)  # At least 2 applications
            .order_by(desc('avg_score'))
            .limit(10)
        )
        
        company_insights = [
            {
                "company": row.company_name,
                "total_applications": row.total,
                "approved_applications": row.approved,
                "approval_rate": round((row.approved / row.total) * 100, 1),
                "average_match_score": float(row.avg_score)
            }
            for row in company_performance
        ]
        
        return {
            "period_comparison": metrics,
            "profile_strength": profile_strength,
            "company_insights": company_insights,
            "recommendations": {
                "profile": _generate_profile_recommendations(profile_strength),
                "strategy": _generate_strategy_recommendations(metrics),
                "optimization": _generate_optimization_recommendations(company_insights)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating performance metrics: {str(e)}"
        )


def _generate_profile_recommendations(profile_strength: Dict[str, Any]) -> List[str]:
    """Generate profile improvement recommendations."""
    recommendations = []
    
    if profile_strength["completeness"] < 80:
        recommendations.append("Complete your profile to improve match quality")
    
    if profile_strength["skills_count"] < 5:
        recommendations.append("Add more skills to your profile for better targeting")
    
    if not profile_strength["preferences_set"]:
        recommendations.append("Set your preferred job types to focus matches")
    
    if not profile_strength["salary_range_set"]:
        recommendations.append("Set salary expectations to filter relevant opportunities")
    
    return recommendations


def _generate_strategy_recommendations(metrics: Dict[str, Any]) -> List[str]:
    """Generate strategy recommendations based on metrics."""
    recommendations = []
    
    last_30 = metrics.get("last_30_days", {})
    
    if last_30.get("total_matches", 0) == 0:
        recommendations.append("Your profile may be too restrictive - consider broadening your criteria")
    elif last_30.get("approval_rate", 0) < 30:
        recommendations.append("You're rejecting many matches - consider refining your preferences")
    elif last_30.get("average_match_score", 0) < 0.7:
        recommendations.append("Focus on improving profile completeness for better matches")
    
    return recommendations


def _generate_optimization_recommendations(company_insights: List[Dict[str, Any]]) -> List[str]:
    """Generate optimization recommendations."""
    recommendations = []
    
    if not company_insights:
        recommendations.append("Apply to more companies to gather performance data")
        return recommendations
    
    # Find top performing companies
    top_companies = [c for c in company_insights if c["approval_rate"] > 50]
    
    if top_companies:
        company_names = [c["company"] for c in top_companies[:3]]
        recommendations.append(f"Focus on companies like {', '.join(company_names)} where you perform well")
    
    return recommendations


# Health check
@router.get("/health")
async def dashboard_health():
    """Health check for auto-application dashboard."""
    return {
        "service": "auto_application_dashboard",
        "status": "healthy",
        "features": [
            "overview_dashboard",
            "detailed_analytics", 
            "activity_feed",
            "performance_metrics",
            "recommendations_engine"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }