"""
API endpoints for the main platform dashboard - overview and user activity.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.user_models import User
from app.database.project_models import ProjectSimulation
from app.database.cv_models import CV
from app.database.job_models import JobApplication
from app.database.portfolio_models import Portfolio
from app.database.platform_models import (
    UserModuleProgress, UserAchievement, UserPoints, SimulationStatus
)
from app.schemas.platform_schemas import (
    DashboardStatsResponse, UserActivityResponse
)


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardStatsResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard overview for the user."""
    
    # Learning Progress
    learning_progress_result = await db.execute(
        select(UserModuleProgress)
        .where(UserModuleProgress.user_id == current_user.id)
    )
    learning_progress = learning_progress_result.scalars().all()
    
    completed_modules = len([p for p in learning_progress if p.is_completed])
    total_learning_time = sum(p.time_spent_minutes for p in learning_progress)
    
    # Simulation Stats
    simulations_result = await db.execute(
        select(ProjectSimulation)
        .where(ProjectSimulation.user_id == current_user.id)
    )
    simulations = simulations_result.scalars().all()
    
    completed_simulations = len([s for s in simulations if s.status == SimulationStatus.COMPLETED])
    avg_simulation_score = None
    if completed_simulations > 0:
        scores = [s.final_score for s in simulations if s.final_score is not None]
        if scores:
            avg_simulation_score = sum(scores) / len(scores)
    
    # CV Builder Stats
    cvs_result = await db.execute(
        select(CV)
        .where(CV.user_id == current_user.id)
    )
    cvs = cvs_result.scalars().all()
    
    total_cv_views = sum(cv.view_count for cv in cvs)
    total_cv_downloads = sum(cv.download_count for cv in cvs)
    
    # Job Search Stats
    applications_result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == current_user.id)
    )
    applications = applications_result.scalars().all()
    
    # Portfolio Stats
    portfolios_result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
    )
    portfolios = portfolios_result.scalars().all()
    
    total_portfolio_views = sum(p.view_count for p in portfolios)
    
    # Gamification Stats
    achievements_result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == current_user.id)
    )
    achievements = achievements_result.scalars().all()
    
    points_result = await db.execute(
        select(UserPoints)
        .where(UserPoints.user_id == current_user.id)
    )
    user_points = points_result.scalar_one_or_none()
    
    # Recent Activity (mock data for now)
    recent_activity = [
        {
            "id": 1,
            "activity_type": "learning_completed",
            "title": "Completed Agile Fundamentals",
            "description": "Finished learning module with 95% score",
            "points_earned": 50,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "metadata": {"module_id": 1, "score": 95}
        },
        {
            "id": 2,
            "activity_type": "simulation_started",
            "title": "Started E-commerce Platform Project",
            "description": "Began new project simulation",
            "points_earned": 25,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "metadata": {"simulation_id": 1}
        },
        {
            "id": 3,
            "activity_type": "cv_created",
            "title": "Created Professional CV",
            "description": "Built new CV using modern template",
            "points_earned": 30,
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "metadata": {"cv_id": 1, "template": "modern"}
        }
    ]
    
    dashboard_stats = {
        "learning_progress": {
            "modules_started": len(learning_progress),
            "modules_completed": completed_modules,
            "completion_rate": (completed_modules / len(learning_progress) * 100) if learning_progress else 0,
            "total_learning_hours": round(total_learning_time / 60, 1),
            "current_streak": 5,  # Mock data
            "next_milestone": "Complete 10 modules"
        },
        "simulation_stats": {
            "total_simulations": len(simulations),
            "completed_simulations": completed_simulations,
            "average_score": round(avg_simulation_score, 1) if avg_simulation_score else None,
            "industries_experienced": len(set(s.industry for s in simulations)),
            "current_simulation": simulations[0].title if simulations and simulations[0].status != SimulationStatus.COMPLETED else None
        },
        "job_search_stats": {
            "total_applications": len(applications),
            "active_applications": len([a for a in applications if a.status in ["applied", "interviewing"]]),
            "response_rate": 65.0,  # Mock data
            "interview_rate": 25.0,  # Mock data
            "saved_jobs": len([a for a in applications if a.status == "saved"])
        },
        "portfolio_stats": {
            "total_portfolios": len(portfolios),
            "total_views": total_portfolio_views,
            "public_portfolios": len([p for p in portfolios if p.visibility == "public"]),
            "cv_count": len(cvs),
            "cv_views": total_cv_views,
            "cv_downloads": total_cv_downloads
        },
        "gamification_stats": {
            "total_points": user_points.total_points if user_points else 0,
            "current_level": user_points.current_level if user_points else 1,
            "points_to_next_level": user_points.points_to_next_level if user_points else 100,
            "achievements_earned": len(achievements),
            "current_streak": user_points.current_streak if user_points else 0,
            "rank_percentile": 75  # Mock data
        },
        "recent_activity": recent_activity
    }
    
    return dashboard_stats


@router.get("/activity", response_model=List[UserActivityResponse])
async def get_user_activity(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's recent activity feed."""
    
    # This would typically come from an activity log table
    # For now, we'll create mock data based on user's actions
    activities = []
    
    # Learning activities
    learning_result = await db.execute(
        select(UserModuleProgress)
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.is_completed == True
        ))
        .order_by(desc(UserModuleProgress.completed_at))
        .limit(5)
    )
    completed_modules = learning_result.scalars().all()
    
    for module in completed_modules:
        activities.append({
            "id": f"learning_{module.id}",
            "activity_type": "learning_completed",
            "title": f"Completed Learning Module",
            "description": f"Finished module with {module.quiz_score or 'N/A'}% score",
            "points_earned": 50,
            "timestamp": module.completed_at,
            "metadata": {"module_id": module.module_id, "score": module.quiz_score}
        })
    
    # Simulation activities
    simulations_result = await db.execute(
        select(ProjectSimulation)
        .where(ProjectSimulation.user_id == current_user.id)
        .order_by(desc(ProjectSimulation.created_at))
        .limit(5)
    )
    recent_simulations = simulations_result.scalars().all()
    
    for sim in recent_simulations:
        if sim.status == SimulationStatus.COMPLETED:
            activities.append({
                "id": f"simulation_completed_{sim.id}",
                "activity_type": "simulation_completed",
                "title": f"Completed {sim.title}",
                "description": f"Finished simulation with {sim.final_score or 'N/A'}% score",
                "points_earned": 100,
                "timestamp": sim.completed_at,
                "metadata": {"simulation_id": sim.id, "score": sim.final_score}
            })
        else:
            activities.append({
                "id": f"simulation_started_{sim.id}",
                "activity_type": "simulation_started", 
                "title": f"Started {sim.title}",
                "description": f"Began new {sim.industry} project simulation",
                "points_earned": 25,
                "timestamp": sim.created_at,
                "metadata": {"simulation_id": sim.id}
            })
    
    # CV activities
    cvs_result = await db.execute(
        select(CV)
        .where(CV.user_id == current_user.id)
        .order_by(desc(CV.created_at))
        .limit(3)
    )
    recent_cvs = cvs_result.scalars().all()
    
    for cv in recent_cvs:
        activities.append({
            "id": f"cv_created_{cv.id}",
            "activity_type": "cv_created",
            "title": f"Created {cv.title}",
            "description": f"Built new CV using {cv.template_name} template",
            "points_earned": 30,
            "timestamp": cv.created_at,
            "metadata": {"cv_id": cv.id, "template": cv.template_name}
        })
    
    # Sort activities by timestamp and limit
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    activities = activities[:limit]
    
    return [UserActivityResponse(**activity) for activity in activities]


@router.get("/quick-stats", response_model=dict)
async def get_quick_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get quick stats for dashboard cards."""
    
    # Learning completion this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    learning_this_week = await db.execute(
        select(func.count(UserModuleProgress.id))
        .where(and_(
            UserModuleProgress.user_id == current_user.id,
            UserModuleProgress.completed_at >= week_ago,
            UserModuleProgress.is_completed == True
        ))
    )
    modules_this_week = learning_this_week.scalar() or 0
    
    # Active simulations
    active_sims = await db.execute(
        select(func.count(ProjectSimulation.id))
        .where(and_(
            ProjectSimulation.user_id == current_user.id,
            ProjectSimulation.status == SimulationStatus.IN_PROGRESS
        ))
    )
    active_simulations = active_sims.scalar() or 0
    
    # CV views this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    cv_views = await db.execute(
        select(func.sum(CV.view_count))
        .where(and_(
            CV.user_id == current_user.id,
            CV.updated_at >= month_ago
        ))
    )
    total_cv_views = cv_views.scalar() or 0
    
    # Job applications this month
    job_apps = await db.execute(
        select(func.count(JobApplication.id))
        .where(and_(
            JobApplication.user_id == current_user.id,
            JobApplication.created_at >= month_ago
        ))
    )
    apps_this_month = job_apps.scalar() or 0
    
    return {
        "modules_completed_this_week": modules_this_week,
        "active_simulations": active_simulations,
        "cv_views_this_month": total_cv_views,
        "job_applications_this_month": apps_this_month,
        "total_points": 1250,  # Mock data - would come from UserPoints table
        "current_level": 5,    # Mock data
        "next_level_progress": 75  # Mock data - percentage to next level
    }


@router.get("/goals", response_model=dict)
async def get_user_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's learning and career goals."""
    
    # This would typically come from a user goals/preferences table
    # For now, return mock personalized goals
    goals = {
        "weekly_goals": {
            "learning_modules": {
                "target": 3,
                "completed": 2,
                "progress": 67
            },
            "simulation_hours": {
                "target": 10,
                "completed": 6,
                "progress": 60
            },
            "job_applications": {
                "target": 5,
                "completed": 3,
                "progress": 60
            }
        },
        "monthly_goals": {
            "complete_learning_path": {
                "target": "Agile & Scrum Mastery",
                "progress": 45,
                "description": "Complete all modules in the Agile learning path"
            },
            "finish_simulation": {
                "target": "E-commerce Platform Launch",
                "progress": 30,
                "description": "Successfully complete the e-commerce project simulation"
            },
            "portfolio_update": {
                "target": "Professional Portfolio",
                "progress": 80,
                "description": "Create and publish a comprehensive portfolio"
            }
        },
        "career_objectives": {
            "target_role": "Senior Project Manager",
            "target_industry": "Technology",
            "target_salary": "$120,000",
            "timeline": "6 months",
            "key_skills_needed": [
                "Advanced Agile/Scrum",
                "Stakeholder Management",
                "Risk Assessment",
                "Team Leadership"
            ],
            "progress_to_goal": 65
        },
        "recommendations": [
            "Complete the Risk Management module to strengthen your profile",
            "Apply to 2-3 more senior PM positions this week",
            "Update your LinkedIn profile with recent achievements",
            "Schedule a mock interview session"
        ]
    }
    
    return goals


@router.get("/metrics", response_model=dict)
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed performance metrics and analytics."""
    
    # Calculate various performance metrics
    # This would involve complex queries across multiple tables
    
    metrics = {
        "learning_analytics": {
            "average_completion_time": "45 minutes",  # per module
            "retention_rate": 92,  # percentage
            "quiz_average": 87.5,
            "preferred_learning_time": "Evening",
            "strongest_topics": ["Risk Management", "Stakeholder Communication"],
            "improvement_areas": ["Budget Management", "Resource Planning"]
        },
        "simulation_performance": {
            "average_score": 82.3,
            "time_to_completion": "2.5 weeks",  # average
            "best_performing_area": "Team Leadership",
            "challenging_areas": ["Budget Control", "Timeline Management"],
            "project_types_mastered": ["Technology", "E-commerce"],
            "leadership_rating": 4.2  # out of 5
        },
        "job_search_effectiveness": {
            "application_to_response_ratio": 0.35,
            "response_to_interview_ratio": 0.60,
            "most_successful_platforms": ["LinkedIn", "Company Websites"],
            "optimal_application_time": "Tuesday-Thursday mornings",
            "cv_performance_score": 85,
            "cover_letter_effectiveness": 78
        },
        "skill_development_trend": {
            "fastest_growing_skills": ["Agile Methodology", "Risk Assessment"],
            "skill_gaps_identified": ["Digital Transformation", "Change Management"],
            "certification_progress": [
                {"name": "PMP", "progress": 40, "target_date": "2025-03-15"},
                {"name": "Scrum Master", "progress": 75, "target_date": "2025-01-30"}
            ],
            "peer_comparison": "Top 25% of learners"
        }
    }
    
    return metrics