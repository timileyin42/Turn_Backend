"""
Job search and application database models.
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
    from app.database.cv_models import CV


class JobApplicationStatus(str, enum.Enum):
    """Job application status enumeration."""
    APPLIED = "applied"
    PENDING = "pending"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"


class JobListing(Base):
    """Job listings scraped from various sources."""
    
    __tablename__ = "job_listings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic job information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Job details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Employment details
    employment_type: Mapped[str] = mapped_column(String(20), default="full-time", nullable=False, index=True)  # full-time, part-time, contract, freelance
    work_mode: Mapped[str] = mapped_column(String(20), default="onsite", nullable=False, index=True)  # remote, onsite, hybrid
    experience_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # entry, mid, senior, lead, executive
    
    # Salary information
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    salary_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    salary_period: Mapped[str] = mapped_column(String(10), default="yearly", nullable=False)  # yearly, monthly, hourly
    
    # Skills and technologies
    required_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of skills
    preferred_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of skills
    technologies: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of technologies
    methodologies: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of PM methodologies
    
    # Company information
    company_size: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # startup, small, medium, large, enterprise
    industry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Application information
    application_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hr_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hiring_manager_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Scraping metadata
    source_platform: Mapped[str] = mapped_column(String(50), nullable=False)  # linkedin, indeed, glassdoor, company_website
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    external_job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Job matching and ranking
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # AI-computed match score
    popularity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Based on applications/views
    
    # Status and metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_remote_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_entry_level_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # SEO and search
    keywords: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array for search optimization
    
    # Timestamps
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Original posting date
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    applications: Mapped[List["JobApplication"]] = relationship("JobApplication", back_populates="job_listing")
    matches: Mapped[List["JobMatch"]] = relationship("JobMatch", back_populates="job_listing")
    skill_requirements: Mapped[List["JobSkillRequirement"]] = relationship("JobSkillRequirement", back_populates="job_listing")


class JobApplication(Base):
    """User job applications tracking."""
    
    __tablename__ = "job_applications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_listing_id: Mapped[int] = mapped_column(ForeignKey("job_listings.id"), nullable=False)
    cv_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cvs.id"), nullable=True)
    
    # Application details
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)  # draft, submitted, reviewed, interview, rejected, accepted
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Application customization
    customized_cv_content: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON with customizations
    tailored_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of emphasized skills
    
    # Automated application details
    is_auto_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_application_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # one_click, bulk, scheduled
    
    # Email tracking
    hr_email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ceo_email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hr_email_opened: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ceo_email_opened: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Response tracking
    response_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # acknowledgment, interview, rejection, questions
    response_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Interview tracking
    interview_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # phone, video, onsite, technical
    
    # Outcome tracking
    final_outcome: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # hired, rejected, withdrawn, no_response
    feedback_received: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_offered: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    
    # User notes and tracking
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    priority_level: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)  # low, medium, high
    
    # Timestamps
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_applications")
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="applications")
    cv: Mapped[Optional["CV"]] = relationship("CV")


class JobMatch(Base):
    """AI-generated job matches for users."""
    
    __tablename__ = "job_matches"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_listing_id: Mapped[int] = mapped_column(ForeignKey("job_listings.id"), nullable=False)
    
    # Match scoring
    overall_match_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    skills_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    location_match_score: Mapped[float] = mapped_column(Float, nullable=False)
    salary_match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Match details
    matching_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of matching skills
    missing_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of missing skills
    
    # AI recommendations
    match_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_tips: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of tips
    skill_gap_recommendations: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of skills to learn
    
    # User feedback
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="matches")


class JobSearch(Base):
    """Saved job searches and alerts."""
    
    __tablename__ = "job_searches"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Search details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    search_terms: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Filters
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # remote, onsite, hybrid
    employment_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Alert settings
    is_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_frequency: Mapped[str] = mapped_column(String(10), default="daily", nullable=False)  # daily, weekly, monthly
    last_alert_sent: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Search results tracking
    last_search_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class CompanyProfile(Base):
    """Company profiles for better job matching."""
    
    __tablename__ = "company_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Company basic information
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Company details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Location and presence
    headquarters_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    locations: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of office locations
    remote_policy: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # remote_first, hybrid, onsite_only
    
    # Culture and benefits
    company_culture: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of benefits
    values: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of company values
    
    # Contact information
    hr_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    careers_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ceo_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Ratings and reviews
    glassdoor_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    employee_satisfaction_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Hiring information
    typical_hiring_process: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    average_interview_duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    response_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Technology and methodology preferences
    preferred_tech_stack: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    preferred_methodologies: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class JobSkillRequirement(Base):
    """Job skill requirements for linking jobs with required skills."""
    
    __tablename__ = "job_skill_requirements"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_listing_id: Mapped[int] = mapped_column(ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    skill_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # beginner, intermediate, advanced, expert
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    job_listing: Mapped["JobListing"] = relationship("JobListing", back_populates="skill_requirements")


class JobAlert(Base):
    """Job alerts and notifications for users."""
    
    __tablename__ = "job_alerts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Alert criteria
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    job_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # remote, onsite, hybrid
    
    # Alert settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)  # daily, weekly, instant
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Tracking
    last_triggered: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    jobs_found_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_alerts")


class SavedJob(Base):
    """User saved jobs for later reference."""
    
    __tablename__ = "saved_jobs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Job basic info (cached from external APIs)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Full job data as JSON (from external API)
    job_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Metadata
    source_platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # remoteok, remotive, etc.
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # User notes
    
    # Timestamps
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_jobs")
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_saved_jobs_user_id', 'user_id'),
        Index('idx_saved_jobs_saved_at', 'saved_at'),
        Index('idx_saved_jobs_source_platform', 'source_platform'),
        Index('idx_saved_jobs_company_name', 'company_name'),
        
        # Composite indexes for common filter combinations
        Index('idx_saved_jobs_user_saved', 'user_id', 'saved_at'),
        Index('idx_saved_jobs_user_company', 'user_id', 'company_name'),
        
        {"sqlite_autoincrement": True}
    )


# Aliases for compatibility
Job = JobListing
JobRecommendation = JobListing  # Placeholder alias
Company = JobListing  # Placeholder alias