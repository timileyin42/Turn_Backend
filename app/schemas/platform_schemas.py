"""
Pydantic schemas for platform features - Learning, Simulations, CV Builder, etc.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.database.platform_models import (
    LearningPath, SimulationStatus, CVStatus, 
    JobApplicationStatus, PortfolioVisibility
)


# Learning Module Schemas
class LearningModuleResponse(BaseModel):
    """Response schema for learning modules."""
    id: int
    title: str
    description: str
    learning_path: LearningPath
    duration_minutes: int
    order_index: int
    difficulty_level: int
    tags: Optional[List[str]] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    prerequisites: Optional[List[int]] = None
    
    class Config:
        from_attributes = True


class StartModuleRequest(BaseModel):
    """Request to start a learning module."""
    timestamp: Optional[datetime] = None


class UserProgressResponse(BaseModel):
    """Response schema for user module progress."""
    id: int
    user_id: int
    module_id: int
    is_completed: bool
    progress_percentage: int
    time_spent_minutes: int
    started_at: datetime
    last_accessed_at: datetime
    completed_at: Optional[datetime] = None
    quiz_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class LearningPathProgress(BaseModel):
    """Progress summary for a learning path."""
    learning_path: LearningPath
    total_modules: int
    completed_modules: int
    progress_percentage: float
    total_time_minutes: int


# Project Simulation Schemas
class CreateSimulationRequest(BaseModel):
    """Request to create a new simulation."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1, max_length=100)
    complexity_level: int = Field(..., ge=1, le=5)
    team_size: int = Field(..., ge=1, le=50)
    duration_weeks: int = Field(..., ge=1, le=52)
    budget: int = Field(..., ge=1)  # in thousands


class UpdateSimulationRequest(BaseModel):
    """Request to update simulation progress."""
    status: Optional[SimulationStatus] = None
    current_phase: Optional[str] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    skill_assessments: Optional[Dict[str, Any]] = None
    artifacts_created: Optional[List[str]] = None


class ProjectSimulationResponse(BaseModel):
    """Response schema for project simulations."""
    id: int
    user_id: int
    title: str
    description: str
    industry: str
    complexity_level: int
    team_size: int
    duration_weeks: int
    budget: int
    status: SimulationStatus
    current_phase: Optional[str] = None
    completion_percentage: int
    final_score: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SimulationStatsResponse(BaseModel):
    """Statistics for user simulations."""
    total_simulations: int
    completed_simulations: int
    in_progress_simulations: int
    average_score: Optional[float] = None
    industries_experienced: List[str]
    complexity_levels_completed: Dict[str, int]
    total_artifacts_created: int
    completion_rate: float


# CV Builder Schemas
class CVContentSection(BaseModel):
    """CV content section."""
    type: str  # personal_info, experience, education, skills, etc.
    title: str
    content: Dict[str, Any]
    order: int
    is_visible: bool = True


class CreateCVRequest(BaseModel):
    """Request to create a new CV."""
    title: str = Field(..., min_length=1, max_length=200)
    template_name: str = Field(..., min_length=1, max_length=100)
    content: List[CVContentSection]


class UpdateCVRequest(BaseModel):
    """Request to update a CV."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    template_name: Optional[str] = None
    content: Optional[List[CVContentSection]] = None
    status: Optional[CVStatus] = None


class CVResponse(BaseModel):
    """Response schema for CVs."""
    id: int
    user_id: int
    title: str
    template_name: str
    status: CVStatus
    content: List[Dict[str, Any]]
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    linkedin_format: Optional[str] = None
    view_count: int
    download_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Job Search Schemas
class JobListingResponse(BaseModel):
    """Response schema for job listings."""
    id: int
    title: str
    company: str
    location: str
    remote_option: bool
    description: str
    requirements: str
    responsibilities: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str
    experience_level: str
    employment_type: str
    industry: str
    skills_required: List[str]
    application_url: str
    company_website: Optional[str] = None
    posted_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    """Request for job search."""
    keywords: Optional[str] = None
    location: Optional[str] = None
    remote_only: bool = False
    salary_min: Optional[int] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    industry: Optional[str] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class JobApplicationRequest(BaseModel):
    """Request to create job application."""
    job_id: int
    cover_letter: Optional[str] = None
    cv_version_used: Optional[str] = None
    notes: Optional[str] = None


class JobApplicationResponse(BaseModel):
    """Response schema for job applications."""
    id: int
    user_id: int
    job_id: int
    status: JobApplicationStatus
    cover_letter: Optional[str] = None
    cv_version_used: Optional[str] = None
    applied_at: Optional[datetime] = None
    response_received_at: Optional[datetime] = None
    interview_scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    rejection_feedback: Optional[str] = None
    match_score: Optional[float] = None
    match_reasons: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Portfolio Schemas
class PortfolioSectionRequest(BaseModel):
    """Portfolio section request."""
    type: str  # projects, certifications, achievements, etc.
    title: str
    content: Dict[str, Any]
    order: int
    is_visible: bool = True


class CreatePortfolioRequest(BaseModel):
    """Request to create a portfolio."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    visibility: PortfolioVisibility = PortfolioVisibility.PRIVATE
    sections: List[PortfolioSectionRequest]
    theme_settings: Optional[Dict[str, Any]] = None


class UpdatePortfolioRequest(BaseModel):
    """Request to update a portfolio."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    visibility: Optional[PortfolioVisibility] = None
    sections: Optional[List[PortfolioSectionRequest]] = None
    theme_settings: Optional[Dict[str, Any]] = None


class PortfolioResponse(BaseModel):
    """Response schema for portfolios."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    visibility: PortfolioVisibility
    sections: List[Dict[str, Any]]
    theme_settings: Optional[Dict[str, Any]] = None
    shareable_url: Optional[str] = None
    pdf_url: Optional[str] = None
    view_count: int
    unique_visitors: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Gamification Schemas
class AchievementResponse(BaseModel):
    """Response schema for achievements."""
    id: int
    name: str
    description: str
    category: str
    icon_url: str
    badge_color: str
    rarity: str
    points_value: int
    requirements: Dict[str, Any]
    
    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """Response schema for user achievements."""
    id: int
    achievement_id: int
    achievement: AchievementResponse
    earned_at: datetime
    points_earned: int
    is_displayed: bool
    
    class Config:
        from_attributes = True


class WeeklyChallengeResponse(BaseModel):
    """Response schema for weekly challenges."""
    id: int
    title: str
    description: str
    challenge_type: str
    requirements: Dict[str, Any]
    points_reward: int
    bonus_rewards: Optional[Dict[str, Any]] = None
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    max_participants: Optional[int] = None
    current_participants: int = 0
    
    class Config:
        from_attributes = True


class ChallengeParticipationResponse(BaseModel):
    """Response schema for challenge participation."""
    id: int
    challenge_id: int
    challenge: WeeklyChallengeResponse
    joined_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: int
    score: Optional[float] = None
    points_earned: int
    
    class Config:
        from_attributes = True


class UserPointsResponse(BaseModel):
    """Response schema for user points."""
    user_id: int
    total_points: int
    available_points: int
    lifetime_points: int
    current_level: int
    points_to_next_level: int
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Dashboard and Overview Schemas
class DashboardStatsResponse(BaseModel):
    """Dashboard statistics overview."""
    learning_progress: Dict[str, Any]
    simulation_stats: Dict[str, Any]
    job_search_stats: Dict[str, Any]
    portfolio_stats: Dict[str, Any]
    gamification_stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]


class UserActivityResponse(BaseModel):
    """User activity feed item."""
    id: int
    activity_type: str  # learning_completed, simulation_started, job_applied, etc.
    title: str
    description: str
    points_earned: Optional[int] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


# Additional platform schemas
class LearningPathResponse(BaseModel):
    """Learning path response schema."""
    id: str
    name: str
    description: str
    modules_count: int
    estimated_duration: int  # in minutes
    difficulty_level: int
    is_completed: bool
    progress_percentage: int


class SimulationResponse(BaseModel):
    """Simulation response schema."""
    id: int
    title: str
    description: str
    status: SimulationStatus
    progress_percentage: int
    completed_at: Optional[datetime] = None


class PlatformAnalyticsResponse(BaseModel):
    """Platform analytics response schema."""
    # Admin view fields
    total_users: Optional[int] = None
    active_users_today: Optional[int] = None
    total_learning_modules: Optional[int] = None
    total_simulations_completed: Optional[int] = None
    total_cvs_created: Optional[int] = None
    total_job_applications: Optional[int] = None
    popular_learning_paths: Optional[List[str]] = None
    user_engagement_stats: Optional[Dict[str, Any]] = None
    
    # User view fields
    user_id: Optional[int] = None
    modules_completed: Optional[int] = None
    total_learning_time: Optional[int] = None
    simulations_completed: Optional[int] = None
    cvs_created: Optional[int] = None
    job_applications_sent: Optional[int] = None
    current_learning_streak: Optional[int] = None
    achievements_earned: Optional[int] = None
    portfolio_views: Optional[int] = None