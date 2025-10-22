"""
Pydantic schemas for auto-application system.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.database.auto_application_models import (
    AutoApplicationStatus, JobMatchNotificationType
)


# Auto-Application Settings Schemas
class AutoApplicationPreferencesBase(BaseModel):
    """Base auto-application preferences."""
    auto_apply_enabled: bool = Field(default=False)
    job_alerts_enabled: bool = Field(default=True)
    max_daily_auto_applications: int = Field(default=3, ge=1, le=10)
    min_match_score_threshold: float = Field(default=0.75, ge=0.5, le=1.0)
    auto_apply_only_remote: bool = Field(default=False)
    require_manual_approval: bool = Field(default=True)


class AutoApplicationPreferencesCreate(AutoApplicationPreferencesBase):
    """Create auto-application preferences."""
    preferred_job_types: Optional[List[str]] = Field(default=None, max_items=10)
    preferred_locations: Optional[List[str]] = Field(default=None, max_items=10)
    required_skills: Optional[List[str]] = Field(default=None, max_items=15)
    excluded_companies: Optional[List[str]] = Field(default=None, max_items=20)
    salary_expectations_min: Optional[int] = Field(default=None, ge=0)
    salary_expectations_max: Optional[int] = Field(default=None, ge=0)
    
    @validator('salary_expectations_max')
    def validate_salary_range(cls, v, values):
        if v is not None and 'salary_expectations_min' in values:
            min_salary = values['salary_expectations_min']
            if min_salary is not None and v < min_salary:
                raise ValueError('Maximum salary must be greater than minimum salary')
        return v


class AutoApplicationPreferencesUpdate(BaseModel):
    """Update auto-application preferences."""
    auto_apply_enabled: Optional[bool] = None
    job_alerts_enabled: Optional[bool] = None
    max_daily_auto_applications: Optional[int] = Field(None, ge=1, le=10)
    min_match_score_threshold: Optional[float] = Field(None, ge=0.5, le=1.0)
    preferred_job_types: Optional[List[str]] = Field(None, max_items=10)
    preferred_locations: Optional[List[str]] = Field(None, max_items=10)
    required_skills: Optional[List[str]] = Field(None, max_items=15)
    excluded_companies: Optional[List[str]] = Field(None, max_items=20)
    salary_expectations_min: Optional[int] = Field(None, ge=0)
    salary_expectations_max: Optional[int] = Field(None, ge=0)
    auto_apply_only_remote: Optional[bool] = None
    require_manual_approval: Optional[bool] = None


class AutoApplicationPreferencesResponse(AutoApplicationPreferencesBase):
    """Response with auto-application preferences."""
    user_id: int
    preferred_job_types: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    salary_expectations_min: Optional[int] = None
    salary_expectations_max: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Pending Application Schemas
class PendingApplicationBase(BaseModel):
    """Base pending application schema."""
    job_title: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    salary_range: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, max_length=50)


class PendingApplicationCreate(PendingApplicationBase):
    """Create pending application."""
    external_job_id: Optional[str] = Field(None, max_length=255)
    job_url: Optional[str] = Field(None, max_length=500)
    job_description: Optional[str] = None
    match_score: float = Field(..., ge=0.0, le=1.0)
    auto_apply_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: Optional[List[str]] = Field(None, max_items=10)
    generated_cover_letter: Optional[str] = None
    cv_customizations: Optional[Dict[str, Any]] = None
    application_summary: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class PendingApplicationUpdate(BaseModel):
    """Update pending application."""
    status: Optional[AutoApplicationStatus] = None
    user_decision: Optional[str] = Field(None, pattern="^(approved|rejected|modified)$")
    user_feedback: Optional[str] = None
    generated_cover_letter: Optional[str] = None
    cv_customizations: Optional[Dict[str, Any]] = None


class PendingApplicationResponse(PendingApplicationBase):
    """Response with pending application details."""
    id: int
    user_id: int
    external_job_id: Optional[str] = None
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    match_score: float
    auto_apply_score: float
    match_reasons: Optional[List[str]] = None
    generated_cover_letter: Optional[str] = None
    cv_customizations: Optional[Dict[str, Any]] = None
    application_summary: Optional[str] = None
    confidence_score: float
    status: AutoApplicationStatus
    expires_at: datetime
    user_decision: Optional[str] = None
    user_decision_at: Optional[datetime] = None
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Job Match Notification Schemas
class JobMatchNotificationBase(BaseModel):
    """Base job match notification schema."""
    notification_type: JobMatchNotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    action_url: Optional[str] = Field(None, max_length=500)


class JobMatchNotificationCreate(JobMatchNotificationBase):
    """Create job match notification."""
    job_title: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    expires_at: Optional[datetime] = None


class JobMatchNotificationResponse(JobMatchNotificationBase):
    """Response with job match notification details."""
    id: int
    user_id: int
    pending_application_id: Optional[int] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    match_score: Optional[float] = None
    is_read: bool
    is_actioned: bool
    expires_at: Optional[datetime] = None
    email_sent: bool
    email_sent_at: Optional[datetime] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    actioned_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Application Decision Schemas
class ApplicationDecisionRequest(BaseModel):
    """Request to make decision on pending application."""
    decision: str = Field(..., pattern="^(approved|rejected|modified)$")
    feedback: Optional[str] = Field(None, max_length=1000)
    modifications: Optional[Dict[str, Any]] = None
    
    @validator('modifications')
    def validate_modifications(cls, v, values):
        if values.get('decision') == 'modified' and not v:
            raise ValueError('Modifications are required when decision is "modified"')
        return v


class ApplicationDecisionResponse(BaseModel):
    """Response after making application decision."""
    success: bool
    decision: str
    pending_application_id: int
    status: AutoApplicationStatus
    message: str
    will_submit: bool = False


# Job Matching Schemas
class JobMatchingRequest(BaseModel):
    """Request for manual job matching."""
    limit: int = Field(default=20, ge=1, le=50)
    min_match_score: float = Field(default=0.6, ge=0.3, le=1.0)
    include_already_applied: bool = Field(default=False)
    force_refresh: bool = Field(default=False)


class JobMatchSummary(BaseModel):
    """Summary of a job match."""
    job_title: str
    company: str
    location: Optional[str] = None
    match_score: float
    auto_apply_score: float
    reasons: List[str]
    job_url: Optional[str] = None
    salary_range: Optional[str] = None
    posted_date: Optional[str] = None


class JobMatchingResponse(BaseModel):
    """Response with job matching results."""
    success: bool
    matches_found: int
    matches: List[JobMatchSummary]
    auto_apply_enabled: bool
    will_auto_process: bool
    criteria_used: Dict[str, Any]
    timestamp: datetime


# AI Application Generation Schemas
class AIApplicationGenerationRequest(BaseModel):
    """Request to generate AI application materials."""
    job_title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    job_description: str = Field(..., min_length=10)
    job_url: Optional[str] = Field(None, max_length=500)
    use_custom_template: bool = Field(default=False)
    template_id: Optional[int] = None


class AIApplicationGenerationResponse(BaseModel):
    """Response with generated AI application materials."""
    success: bool
    job_title: str
    company: str
    cover_letter: str
    cv_customizations: Dict[str, Any]
    application_summary: str
    confidence_score: float
    generation_time: float
    template_used: Optional[str] = None
    generated_at: datetime


# Analytics Schemas
class AutoApplicationAnalytics(BaseModel):
    """Auto-application analytics response."""
    period_days: int
    total_matches_found: int
    pending_applications: int
    approved_applications: int
    rejected_applications: int
    submitted_applications: int
    failed_applications: int
    average_match_score: float
    average_confidence_score: float
    unread_notifications: int
    auto_apply_enabled: bool
    profile_completeness: int
    success_metrics: Dict[str, Any]
    recommendations: List[str]


class DashboardSummary(BaseModel):
    """Dashboard summary for auto-applications."""
    pending_count: int
    notifications_count: int
    recent_matches: List[JobMatchSummary]
    settings_status: str  # "complete", "incomplete", "needs_attention"
    next_actions: List[str]
    performance_summary: Dict[str, Any]


# Template Schemas
class ApplicationTemplateBase(BaseModel):
    """Base application template schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    template_type: str = Field(..., pattern="^(cover_letter|cv_summary|email)$")
    content: str = Field(..., min_length=10)


class ApplicationTemplateCreate(ApplicationTemplateBase):
    """Create application template."""
    variables: Optional[Dict[str, str]] = None
    target_industries: Optional[List[str]] = Field(None, max_items=10)
    target_job_types: Optional[List[str]] = Field(None, max_items=10)
    target_experience_levels: Optional[List[str]] = Field(None, max_items=5)
    is_default: bool = Field(default=False)


class ApplicationTemplateUpdate(BaseModel):
    """Update application template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=10)
    variables: Optional[Dict[str, str]] = None
    target_industries: Optional[List[str]] = Field(None, max_items=10)
    target_job_types: Optional[List[str]] = Field(None, max_items=10)
    target_experience_levels: Optional[List[str]] = Field(None, max_items=5)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ApplicationTemplateResponse(ApplicationTemplateBase):
    """Response with application template details."""
    id: int
    user_id: int
    variables: Optional[Dict[str, str]] = None
    target_industries: Optional[List[str]] = None
    target_job_types: Optional[List[str]] = None
    target_experience_levels: Optional[List[str]] = None
    is_default: bool
    is_active: bool
    usage_count: int
    success_rate: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Advanced Settings Schemas
class AdvancedAutoApplicationSettings(BaseModel):
    """Advanced auto-application settings."""
    keyword_preferences: Optional[Dict[str, float]] = None  # keyword -> weight
    industry_preferences: Optional[Dict[str, float]] = None  # industry -> weight
    company_size_preferences: Optional[List[str]] = None  # startup, mid, large, enterprise
    auto_apply_window_start: Optional[int] = Field(None, ge=0, le=23)  # hour of day
    auto_apply_window_end: Optional[int] = Field(None, ge=0, le=23)    # hour of day
    auto_apply_days: Optional[List[str]] = None  # days of week
    require_visa_sponsorship: bool = Field(default=False)
    avoid_third_party_recruiters: bool = Field(default=True)
    minimum_company_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    require_benefits: Optional[List[str]] = None
    max_applications_per_company: int = Field(default=1, ge=1, le=5)
    min_days_between_applications: int = Field(default=30, ge=1, le=365)
    require_job_description_completeness: bool = Field(default=True)


# Health Check Schema
class AutoApplicationHealthResponse(BaseModel):
    """Health check response for auto-application service."""
    service: str
    status: str
    features: List[str]
    ai_service_available: bool
    job_search_service_available: bool
    email_service_available: bool
    database_connection: bool
    timestamp: datetime