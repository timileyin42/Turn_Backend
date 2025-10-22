"""
CV Builder database models.
"""
from datetime import datetime, date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Date, JSON, Float, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User


class CVStatus(str, enum.Enum):
    """CV status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class CV(Base):
    """Main CV/Resume document."""
    
    __tablename__ = "cvs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # CV metadata
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # onsite, remote, hybrid, creative
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    target_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Personal information
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    professional_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Professional summary
    professional_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objective_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Online presence
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    personal_website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # CV settings
    include_photo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color_scheme: Mapped[str] = mapped_column(String(20), default="blue", nullable=False)
    font_style: Mapped[str] = mapped_column(String(30), default="professional", nullable=False)
    
    # Generation and export
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # File exports
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    docx_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cvs")
    work_experiences: Mapped[List["WorkExperience"]] = relationship("WorkExperience", back_populates="cv", cascade="all, delete-orphan")
    educations: Mapped[List["Education"]] = relationship("Education", back_populates="cv", cascade="all, delete-orphan")
    cv_skills: Mapped[List["CVSkill"]] = relationship("CVSkill", back_populates="cv", cascade="all, delete-orphan")
    projects: Mapped[List["CVProject"]] = relationship("CVProject", back_populates="cv", cascade="all, delete-orphan")
    certifications: Mapped[List["Certification"]] = relationship("Certification", back_populates="cv", cascade="all, delete-orphan")
    languages: Mapped[List["Language"]] = relationship("Language", back_populates="cv", cascade="all, delete-orphan")
    references: Mapped[List["Reference"]] = relationship("Reference", back_populates="cv", cascade="all, delete-orphan")
    custom_sections: Mapped[List["CVSection"]] = relationship("CVSection", back_populates="cv", cascade="all, delete-orphan")
    exports: Mapped[List["CVExport"]] = relationship("CVExport", back_populates="cv", cascade="all, delete-orphan")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_cv_user_status', 'user_id', 'is_public'),
        Index('idx_cv_user_default', 'user_id', 'is_default'),
        Index('idx_cv_template_role', 'template_type', 'target_role'),
        Index('idx_cv_industry_role', 'target_industry', 'target_role'),
        Index('idx_cv_ai_generated', 'is_ai_generated', 'created_at'),
        Index('idx_cv_user_created', 'user_id', 'created_at'),
    )


class WorkExperience(Base):
    """Work experience entries for CV."""
    
    __tablename__ = "work_experiences"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Job details
    job_title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    employment_type: Mapped[str] = mapped_column(String(20), default="full-time", nullable=False, index=True)  # full-time, part-time, contract, freelance, internship
    
    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)  # Null if current job
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    key_achievements: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of achievements
    technologies_used: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of technologies
    
    # Metrics and impact
    team_size_managed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    budget_managed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    projects_delivered: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="work_experiences")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_work_cv_order', 'cv_id', 'display_order'),
        Index('idx_work_cv_current', 'cv_id', 'is_current'),
        Index('idx_work_company_title', 'company_name', 'job_title'),
        Index('idx_work_dates_range', 'start_date', 'end_date'),
        Index('idx_work_type_location', 'employment_type', 'location'),
        Index('idx_work_cv_include', 'cv_id', 'include_in_cv'),
    )


class Education(Base):
    """Education entries for CV."""
    
    __tablename__ = "educations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Institution details
    institution_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    degree_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # bachelor, master, phd, certificate, diploma
    field_of_study: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Academic details
    gpa: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    honors: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # magna cum laude, etc.
    relevant_coursework: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of courses
    
    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Additional information
    thesis_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="educations")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_education_cv_order', 'cv_id', 'display_order'),
        Index('idx_education_cv_current', 'cv_id', 'is_current'),
        Index('idx_education_degree_field', 'degree_type', 'field_of_study'),
        Index('idx_education_institution_degree', 'institution_name', 'degree_type'),
        Index('idx_education_dates_range', 'start_date', 'end_date'),
        Index('idx_education_cv_include', 'cv_id', 'include_in_cv'),
    )


class CVSkill(Base):
    """Skills section in CV."""
    
    __tablename__ = "cv_skills"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Skill details
    skill_name: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_category: Mapped[str] = mapped_column(String(30), nullable=False)  # technical, soft, methodology, language, tool
    proficiency_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # beginner, intermediate, advanced, expert
    proficiency_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Years of experience
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    highlight_skill: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="cv_skills")


class CVProject(Base):
    """Projects section in CV."""
    
    __tablename__ = "cv_projects"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Project details
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)  # work, personal, academic, volunteer, simulation
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Project metadata
    technologies_used: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    methodologies_used: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    role_in_project: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dates and duration
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    duration_description: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "3 months", "ongoing"
    
    # Results and impact
    key_achievements: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    metrics_and_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Links
    project_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source tracking (if from TURN simulation)
    source_simulation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_simulations.id"), nullable=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="projects")


class Certification(Base):
    """Certifications and licenses section in CV."""
    
    __tablename__ = "certifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Certification details
    certification_name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(100), nullable=False)
    credential_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dates
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    does_not_expire: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Verification
    verification_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="certifications")


class Language(Base):
    """Languages section in CV."""
    
    __tablename__ = "languages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Language details
    language_name: Mapped[str] = mapped_column(String(50), nullable=False)
    proficiency_level: Mapped[str] = mapped_column(String(20), nullable=False)  # native, fluent, advanced, intermediate, beginner
    
    # Certifications
    certification_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    certification_score: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="languages")


class Reference(Base):
    """References section in CV."""
    
    __tablename__ = "references"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Reference details
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # supervisor, colleague, client, mentor
    
    # Contact information
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Reference details
    years_known: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    permission_to_contact: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Display options
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    include_in_cv: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="references")


class CVSection(Base):
    """Generic CV sections for custom content and formatting."""
    
    __tablename__ = "cv_sections"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    
    # Section details
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)  # custom, awards, publications, etc.
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Formatting options
    is_bulleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    include_dates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Visibility
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="custom_sections")


class CVTemplate(Base):
    """CV templates for different industries and roles."""
    
    __tablename__ = "cv_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Template metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)  # onsite, remote, hybrid, creative
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Template structure
    template_data: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON structure of template
    preview_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Usage and ratings
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class CVExport(Base):
    """CV export history and files."""
    
    __tablename__ = "cv_exports"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cvs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Export details
    format: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    
    # Export settings
    include_photo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_styling: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # File lifecycle
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    cv: Mapped["CV"] = relationship("CV", back_populates="exports")
    user: Mapped["User"] = relationship("User", back_populates="cv_exports")