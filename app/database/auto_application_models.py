"""
Auto-Application specific database models for TURN Platform.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User
    from app.database.job_models import JobListing, JobApplication


class AutoApplicationStatus(str, enum.Enum):
    """Auto-application status enumeration."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    FAILED = "failed"
    EXPIRED = "expired"


class JobMatchNotificationType(str, enum.Enum):
    """Job match notification type."""
    NEW_MATCH = "new_match"
    APPLICATION_READY = "application_ready"
    APPROVAL_REQUIRED = "approval_required"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_FAILED = "application_failed"


class PendingAutoApplication(Base):
    """Pending auto-applications awaiting user approval."""
    
    __tablename__ = "pending_auto_applications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_listing_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_listings.id"), nullable=True, index=True)
    
    # Job details (in case external job not in our DB)
    external_job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Matching details
    match_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    match_reasons: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of reasons
    auto_apply_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    
    # Generated application materials
    generated_cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cv_customizations: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    application_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status and timing
    status: Mapped[AutoApplicationStatus] = mapped_column(SQLEnum(AutoApplicationStatus), default=AutoApplicationStatus.PENDING_APPROVAL, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)  # Auto-expire if not acted upon
    
    # User actions
    user_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)  # approved, rejected, modified
    user_decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Application results (if approved and submitted)
    submitted_application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_applications.id"), nullable=True)
    submission_result: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    submission_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    job_listing: Mapped[Optional["JobListing"]] = relationship("JobListing")
    submitted_application: Mapped[Optional["JobApplication"]] = relationship("JobApplication")

    # Composite indexes for performance
    __table_args__ = (
        Index('idx_pending_user_status', 'user_id', 'status'),
        Index('idx_pending_user_created', 'user_id', 'created_at'),
        Index('idx_pending_expires_status', 'expires_at', 'status'),
        Index('idx_pending_match_score', 'match_score', 'status'),
        Index('idx_pending_company_user', 'company_name', 'user_id'),
        Index('idx_pending_decision_time', 'user_decision', 'user_decision_at'),
    )


class AutoApplicationLog(Base):
    """Log of all auto-application activities."""
    
    __tablename__ = "auto_application_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pending_application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pending_auto_applications.id"), nullable=True)
    job_application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_applications.id"), nullable=True)
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # job_matched, application_generated, user_approved, etc.
    activity_description: Mapped[str] = mapped_column(Text, nullable=False)
    activity_data: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Additional structured data
    
    # Context
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # Outcome
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    pending_application: Mapped[Optional["PendingAutoApplication"]] = relationship("PendingAutoApplication")
    job_application: Mapped[Optional["JobApplication"]] = relationship("JobApplication")

    # Composite indexes for analytics
    __table_args__ = (
        Index('idx_log_user_activity', 'user_id', 'activity_type'),
        Index('idx_log_user_created', 'user_id', 'created_at'),
        Index('idx_log_success_activity', 'success', 'activity_type'),
        Index('idx_log_company_activity', 'company_name', 'activity_type'),
        Index('idx_log_match_score', 'match_score', 'success'),
    )


class JobMatchNotification(Base):
    """Notifications for job matches and auto-application activities."""
    
    __tablename__ = "job_match_notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pending_application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pending_auto_applications.id"), nullable=True)
    
    # Notification details
    notification_type: Mapped[JobMatchNotificationType] = mapped_column(SQLEnum(JobMatchNotificationType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Job details for quick reference
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_actioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Email notification
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    pending_application: Mapped[Optional["PendingAutoApplication"]] = relationship("PendingAutoApplication")

    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_notification_user_type', 'user_id', 'notification_type'),
        Index('idx_notification_user_unread', 'user_id', 'is_read'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
        Index('idx_notification_expires', 'expires_at', 'is_actioned'),
        Index('idx_notification_email', 'email_sent', 'created_at'),
        Index('idx_notification_company_type', 'company_name', 'notification_type'),
    )


class AutoApplicationSettings(Base):
    """User-specific auto-application settings (extends profile settings)."""
    
    __tablename__ = "auto_application_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Advanced matching criteria
    keyword_preferences: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Weighted keywords
    industry_preferences: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Preferred industries with weights
    company_size_preferences: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # startup, mid, large, enterprise
    
    # Application timing
    auto_apply_window_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Hour of day (0-23)
    auto_apply_window_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Hour of day (0-23)
    auto_apply_days: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Days of week
    
    # Advanced filters
    require_visa_sponsorship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avoid_third_party_recruiters: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    minimum_company_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Glassdoor rating
    require_benefits: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Required benefits
    
    # Application customization
    cover_letter_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Custom template
    application_persona: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # professional, creative, technical
    emphasize_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Skills to always highlight
    
    # Quality controls
    max_applications_per_company: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_days_between_applications: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    require_job_description_completeness: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Tracking and analytics
    total_auto_applications: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_applications: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interview_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Last activity
    last_job_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_application_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")

    # Composite indexes
    __table_args__ = (
        Index('idx_settings_scan_time', 'last_job_scan_at', 'user_id'),
        Index('idx_settings_application_time', 'last_application_at', 'user_id'),
        Index('idx_settings_success_rate', 'interview_rate', 'total_auto_applications'),
    )


class JobApplicationTemplate(Base):
    """Reusable templates for auto-applications."""
    
    __tablename__ = "job_application_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Template details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # cover_letter, cv_summary, etc.
    
    # Template content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Available template variables
    
    # Usage and targeting
    target_industries: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    target_job_types: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    target_experience_levels: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")

    # Composite indexes
    __table_args__ = (
        Index('idx_template_user_type', 'user_id', 'template_type'),
        Index('idx_template_user_active', 'user_id', 'is_active'),
        Index('idx_template_success_rate', 'success_rate', 'usage_count'),
        Index('idx_template_last_used', 'last_used_at', 'user_id'),
    )