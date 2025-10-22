"""
Portfolio and achievement database models.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User


class Portfolio(Base):
    """User portfolio collection."""
    
    __tablename__ = "portfolios"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Portfolio metadata
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    theme: Mapped[str] = mapped_column(String(20), default="professional", nullable=False)
    
    # Portfolio settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_url_slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    
    # Content organization
    sections_order: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array defining section order
    custom_sections: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of custom sections
    
    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color_scheme: Mapped[str] = mapped_column(String(20), default="blue", nullable=False)
    font_style: Mapped[str] = mapped_column(String(30), default="professional", nullable=False)
    
    # Contact information
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Export tracking
    last_exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    share_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    items: Mapped[List["PortfolioItem"]] = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")
    achievements: Mapped[List["Achievement"]] = relationship("Achievement", back_populates="portfolio", cascade="all, delete-orphan")
    testimonials: Mapped[List["Testimonial"]] = relationship("Testimonial", back_populates="portfolio", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_portfolios_user_id', 'user_id'),
        Index('idx_portfolios_is_public', 'is_public'),
        Index('idx_portfolios_is_default', 'is_default'),
        Index('idx_portfolios_theme', 'theme'),
        Index('idx_portfolios_view_count', 'view_count'),
        Index('idx_portfolios_share_count', 'share_count'),
        Index('idx_portfolios_created_at', 'created_at'),
        Index('idx_portfolios_updated_at', 'updated_at'),
        Index('idx_portfolios_last_exported_at', 'last_exported_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_portfolios_user_public', 'user_id', 'is_public'),
        Index('idx_portfolios_user_default', 'user_id', 'is_default'),
        Index('idx_portfolios_public_theme', 'is_public', 'theme'),
        Index('idx_portfolios_user_created', 'user_id', 'created_at'),
        Index('idx_portfolios_public_views', 'is_public', 'view_count'),
        Index('idx_portfolios_user_updated', 'user_id', 'updated_at'),
        
        {"sqlite_autoincrement": True}
    )


class PortfolioItem(Base):
    """Individual items in a portfolio."""
    
    __tablename__ = "portfolio_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    
    # Item details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)  # project, certificate, skill, achievement, artifact
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Rich text content
    content_format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)
    
    # Media attachments
    featured_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    gallery_images: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of image URLs
    attachments: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of file attachments
    
    # Project-specific fields
    technologies_used: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    methodologies_used: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    project_duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results and impact
    key_outcomes: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of outcomes
    metrics_achieved: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of metrics
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # External links
    project_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source tracking
    source_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # simulation, manual, imported
    source_simulation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_simulations.id"), nullable=True)
    source_artifact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_artifacts.id"), nullable=True)
    
    # Display settings
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Tags and categories
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of tags
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="items")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_portfolio_items_portfolio_id', 'portfolio_id'),
        Index('idx_portfolio_items_item_type', 'item_type'),
        Index('idx_portfolio_items_source_type', 'source_type'),
        Index('idx_portfolio_items_source_simulation_id', 'source_simulation_id'),
        Index('idx_portfolio_items_display_order', 'display_order'),
        Index('idx_portfolio_items_is_featured', 'is_featured'),
        Index('idx_portfolio_items_is_visible', 'is_visible'),
        Index('idx_portfolio_items_category', 'category'),
        Index('idx_portfolio_items_created_at', 'created_at'),
        Index('idx_portfolio_items_updated_at', 'updated_at'),
        Index('idx_portfolio_items_completion_date', 'completion_date'),
        
        # Composite indexes for common filter combinations
        Index('idx_portfolio_items_portfolio_type', 'portfolio_id', 'item_type'),
        Index('idx_portfolio_items_portfolio_visible', 'portfolio_id', 'is_visible'),
        Index('idx_portfolio_items_portfolio_order', 'portfolio_id', 'display_order'),
        Index('idx_portfolio_items_featured_visible', 'is_featured', 'is_visible'),
        Index('idx_portfolio_items_type_category', 'item_type', 'category'),
        Index('idx_portfolio_items_portfolio_featured', 'portfolio_id', 'is_featured'),
        Index('idx_portfolio_items_visible_order', 'is_visible', 'display_order'),
        
        {"sqlite_autoincrement": True}
    )


class Achievement(Base):
    """User achievements and badges."""
    
    __tablename__ = "achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    
    # Achievement details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    achievement_type: Mapped[str] = mapped_column(String(30), nullable=False)  # certification, project_completion, skill_mastery, milestone
    
    # Achievement metadata
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # technical, leadership, methodology, learning
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    
    # Badge and visual
    badge_icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    badge_color: Mapped[str] = mapped_column(String(20), default="#ffd700", nullable=False)
    
    # Verification and credibility
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Source tracking
    earned_from_simulation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_simulation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_simulations.id"), nullable=True)
    
    # Achievement criteria
    criteria_met: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of criteria
    
    # Points and gamification
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Display settings
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    portfolio: Mapped[Optional["Portfolio"]] = relationship("Portfolio", back_populates="achievements")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_achievements_user_id', 'user_id'),
        Index('idx_achievements_portfolio_id', 'portfolio_id'),
        Index('idx_achievements_achievement_type', 'achievement_type'),
        Index('idx_achievements_category', 'category'),
        Index('idx_achievements_difficulty_level', 'difficulty_level'),
        Index('idx_achievements_is_verified', 'is_verified'),
        Index('idx_achievements_earned_from_simulation', 'earned_from_simulation'),
        Index('idx_achievements_source_simulation_id', 'source_simulation_id'),
        Index('idx_achievements_points_awarded', 'points_awarded'),
        Index('idx_achievements_is_featured', 'is_featured'),
        Index('idx_achievements_is_public', 'is_public'),
        Index('idx_achievements_display_order', 'display_order'),
        Index('idx_achievements_earned_at', 'earned_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_achievements_user_type', 'user_id', 'achievement_type'),
        Index('idx_achievements_user_category', 'user_id', 'category'),
        Index('idx_achievements_user_public', 'user_id', 'is_public'),
        Index('idx_achievements_portfolio_featured', 'portfolio_id', 'is_featured'),
        Index('idx_achievements_type_difficulty', 'achievement_type', 'difficulty_level'),
        Index('idx_achievements_verified_public', 'is_verified', 'is_public'),
        Index('idx_achievements_user_earned', 'user_id', 'earned_at'),
        
        {"sqlite_autoincrement": True}
    )


class Testimonial(Base):
    """Testimonials and recommendations."""
    
    __tablename__ = "testimonials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    
    # Testimonial content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    
    # Recommender information
    recommender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    recommender_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommender_company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommender_relationship: Mapped[str] = mapped_column(String(50), nullable=False)  # supervisor, colleague, client, mentor, peer
    
    # Contact and verification
    recommender_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    recommender_linkedin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Context
    project_context: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    collaboration_duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Testimonial metadata
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)  # manual, linkedin, imported
    
    # Display settings
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    date_of_collaboration: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    portfolio: Mapped[Optional["Portfolio"]] = relationship("Portfolio", back_populates="testimonials")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_testimonials_user_id', 'user_id'),
        Index('idx_testimonials_portfolio_id', 'portfolio_id'),
        Index('idx_testimonials_rating', 'rating'),
        Index('idx_testimonials_recommender_relationship', 'recommender_relationship'),
        Index('idx_testimonials_is_verified', 'is_verified'),
        Index('idx_testimonials_source', 'source'),
        Index('idx_testimonials_is_featured', 'is_featured'),
        Index('idx_testimonials_is_public', 'is_public'),
        Index('idx_testimonials_display_order', 'display_order'),
        Index('idx_testimonials_created_at', 'created_at'),
        Index('idx_testimonials_date_of_collaboration', 'date_of_collaboration'),
        
        # Composite indexes for common filter combinations
        Index('idx_testimonials_user_public', 'user_id', 'is_public'),
        Index('idx_testimonials_portfolio_featured', 'portfolio_id', 'is_featured'),
        Index('idx_testimonials_verified_public', 'is_verified', 'is_public'),
        Index('idx_testimonials_user_verified', 'user_id', 'is_verified'),
        Index('idx_testimonials_rating_public', 'rating', 'is_public'),
        Index('idx_testimonials_relationship_verified', 'recommender_relationship', 'is_verified'),
        
        {"sqlite_autoincrement": True}
    )


class SkillAssessment(Base):
    """AI-driven skill assessments and progress tracking."""
    
    __tablename__ = "skill_assessments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Assessment details
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    skill_category: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # Assessment results
    current_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 (beginner to expert)
    previous_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    
    # Assessment method
    assessment_type: Mapped[str] = mapped_column(String(30), nullable=False)  # ai_analysis, project_performance, self_assessment, quiz
    evidence_sources: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of evidence
    
    # AI analysis
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvement_suggestions: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of suggestions
    recommended_resources: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of learning resources
    
    # Progress tracking
    progress_trend: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # improving, stable, declining
    next_milestone: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Validation
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("project_simulations.id"), nullable=True)
    
    # Timestamps
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_skill_assessments_user_id', 'user_id'),
        Index('idx_skill_assessments_skill_name', 'skill_name'),
        Index('idx_skill_assessments_skill_category', 'skill_category'),
        Index('idx_skill_assessments_current_level', 'current_level'),
        Index('idx_skill_assessments_assessment_type', 'assessment_type'),
        Index('idx_skill_assessments_confidence_score', 'confidence_score'),
        Index('idx_skill_assessments_progress_trend', 'progress_trend'),
        Index('idx_skill_assessments_is_verified', 'is_verified'),
        Index('idx_skill_assessments_verification_project_id', 'verification_project_id'),
        Index('idx_skill_assessments_assessed_at', 'assessed_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_skill_assessments_user_skill', 'user_id', 'skill_name'),
        Index('idx_skill_assessments_user_category', 'user_id', 'skill_category'),
        Index('idx_skill_assessments_user_level', 'user_id', 'current_level'),
        Index('idx_skill_assessments_category_level', 'skill_category', 'current_level'),
        Index('idx_skill_assessments_type_verified', 'assessment_type', 'is_verified'),
        Index('idx_skill_assessments_user_assessed', 'user_id', 'assessed_at'),
        
        {"sqlite_autoincrement": True}
    )
    
    
class LearningGoal(Base):
    """User learning goals and objectives."""
    
    __tablename__ = "learning_goals"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Goal details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    goal_type: Mapped[str] = mapped_column(String(30), nullable=False)  # skill_acquisition, certification, project_completion, career_milestone
    
    # Goal targets
    target_skill: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    target_certification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timeline
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    milestones: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of milestones
    completed_milestones: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of completed milestone IDs
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, completed, paused, abandoned
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)  # low, medium, high
    
    # AI recommendations
    recommended_path: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of recommended steps
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_learning_goals_user_id', 'user_id'),
        Index('idx_learning_goals_goal_type', 'goal_type'),
        Index('idx_learning_goals_target_skill', 'target_skill'),
        Index('idx_learning_goals_target_level', 'target_level'),
        Index('idx_learning_goals_target_date', 'target_date'),
        Index('idx_learning_goals_progress_percentage', 'progress_percentage'),
        Index('idx_learning_goals_status', 'status'),
        Index('idx_learning_goals_priority', 'priority'),
        Index('idx_learning_goals_created_at', 'created_at'),
        Index('idx_learning_goals_updated_at', 'updated_at'),
        Index('idx_learning_goals_completed_at', 'completed_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_learning_goals_user_status', 'user_id', 'status'),
        Index('idx_learning_goals_user_priority', 'user_id', 'priority'),
        Index('idx_learning_goals_user_type', 'user_id', 'goal_type'),
        Index('idx_learning_goals_status_priority', 'status', 'priority'),
        Index('idx_learning_goals_status_target_date', 'status', 'target_date'),
        Index('idx_learning_goals_user_progress', 'user_id', 'progress_percentage'),
        Index('idx_learning_goals_active_target_date', 'status', 'target_date', 'priority'),
        
        {"sqlite_autoincrement": True}
    )