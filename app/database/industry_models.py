"""
Industry tracks and domain-specific content models.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.project_models import ProjectSimulation, ProjectTemplate


class IndustryTrack(Base):
    """Industry-specific learning tracks."""
    
    __tablename__ = "industry_tracks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Track details
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color_theme: Mapped[str] = mapped_column(String(20), default="#007bff", nullable=False, index=True)
    
    # Content organization
    difficulty_levels: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of available difficulty levels
    methodologies_focus: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of emphasized methodologies
    
    # Learning path
    learning_objectives: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of learning goals
    prerequisite_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of required skills
    career_outcomes: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of potential career paths
    
    # Statistics
    total_projects: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    total_learners: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    average_completion_rate: Mapped[Optional[float]] = mapped_column(nullable=True, index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # SEO and marketing
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    
    # Relationships
    projects: Mapped[List["ProjectSimulation"]] = relationship("ProjectSimulation", back_populates="industry_track")
    project_templates: Mapped[List["ProjectTemplate"]] = relationship("ProjectTemplate", back_populates="industry_track")
    specializations: Mapped[List["IndustrySpecialization"]] = relationship("IndustrySpecialization", back_populates="industry_track", cascade="all, delete-orphan")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_industry_active_featured', 'is_active', 'is_featured'),
        Index('idx_industry_stats', 'total_learners', 'average_completion_rate'),
        Index('idx_industry_projects_learners', 'total_projects', 'total_learners'),
        Index('idx_industry_created_active', 'created_at', 'is_active'),
    )


class IndustrySpecialization(Base):
    """Specialized sub-areas within industry tracks."""
    
    __tablename__ = "industry_specializations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    industry_track_id: Mapped[int] = mapped_column(ForeignKey("industry_tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Specialization details
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Skills and tools focus
    key_skills: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of skills
    tools_and_software: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of tools
    certification_paths: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of relevant certifications
    
    # Market information
    job_market_demand: Mapped[str] = mapped_column(String(20), default="medium", nullable=False, index=True)  # low, medium, high
    average_salary_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "$60k-80k"
    growth_projection: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)  # growing, stable, declining
    
    # Learning resources
    recommended_resources: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of resources
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    industry_track: Mapped["IndustryTrack"] = relationship("IndustryTrack", back_populates="specializations")


class SkillCategory(Base):
    """Categories for organizing skills across industries."""
    
    __tablename__ = "skill_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Category details
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category_type: Mapped[str] = mapped_column(String(20), nullable=False)  # technical, soft, methodology, tool
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    skills: Mapped[List["Skill"]] = relationship("Skill", back_populates="category")


class Skill(Base):
    """Master list of skills across all industries."""
    
    __tablename__ = "skills"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("skill_categories.id"), nullable=False)
    
    # Skill details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Skill metadata
    aliases: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of alternative names
    related_skills: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of related skill IDs
    
    # Learning information
    difficulty_to_learn: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1-5 scale
    market_demand: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    category: Mapped["SkillCategory"] = relationship("SkillCategory", back_populates="skills")


class LearningPath(Base):
    """Structured learning paths within industry tracks."""
    
    __tablename__ = "learning_paths"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    industry_track_id: Mapped[int] = mapped_column(ForeignKey("industry_tracks.id"), nullable=False)
    
    # Path details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Path structure
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_progression: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array showing difficulty curve
    
    # Learning objectives
    learning_outcomes: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of outcomes
    assessment_criteria: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of assessment points
    
    # Prerequisites and requirements
    prerequisites: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of required skills/paths
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships - Note: will be defined when we create the other models
    # path_steps: Mapped[List["LearningPathStep"]] = relationship("LearningPathStep", back_populates="learning_path")


class CertificationPath(Base):
    """Industry certifications and their requirements."""
    
    __tablename__ = "certification_paths"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Certification details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Certification metadata
    certification_level: Mapped[str] = mapped_column(String(20), nullable=False)  # entry, associate, professional, expert
    industry_relevance: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of relevant industry track IDs
    
    # Requirements and process
    prerequisites: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of requirements
    exam_details: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON object with exam info
    study_materials: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of study resources
    
    # Costs and timing
    cost_usd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    preparation_time_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    validity_period_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Value proposition
    career_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_impact_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # External links
    official_website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    registration_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)