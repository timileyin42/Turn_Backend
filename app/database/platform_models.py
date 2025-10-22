"""
Platform feature models for Turn - AI PM Teacher, Simulations, CV Builder, etc.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Float, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User


class LearningPath(str, enum.Enum):
    """Learning path enumeration."""
    BEGINNER_PM = "beginner_pm"
    AGILE_SCRUM = "agile_scrum" 
    DIGITAL_TRANSFORMATION = "digital_transformation"
    RISK_MANAGEMENT = "risk_management"
    STAKEHOLDER_MANAGEMENT = "stakeholder_management"
    PRODUCT_MANAGEMENT = "product_management"


class PortfolioVisibility(str, enum.Enum):
    """Portfolio visibility options."""
    PRIVATE = "private"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class SimulationStatus(str, enum.Enum):
    """Project simulation status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CVStatus(str, enum.Enum):
    """CV status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class JobApplicationStatus(str, enum.Enum):
    """Job application status."""
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


# AI PM Teacher Models
class LearningModule(Base):
    """Learning modules for AI PM Teacher."""
    
    __tablename__ = "learning_modules"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    learning_path: Mapped[LearningPath] = mapped_column(SQLEnum(LearningPath), nullable=False, index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # JSON content structure
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Ordering and prerequisites
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prerequisites: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # List of module IDs
    
    # Metadata
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)  # 1-5
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    
    # Relationships
    user_progress: Mapped[List["UserModuleProgress"]] = relationship("UserModuleProgress", back_populates="module")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_module_path_order', 'learning_path', 'order_index'),
        Index('idx_module_path_active', 'learning_path', 'is_active'),
        Index('idx_module_difficulty_path', 'difficulty_level', 'learning_path'),
        Index('idx_module_duration_difficulty', 'duration_minutes', 'difficulty_level'),
    )


class UserModuleProgress(Base):
    """User progress through learning modules."""
    
    __tablename__ = "user_module_progress"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False)
    
    # Progress tracking
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Completion data
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    quiz_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    certificate_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    module: Mapped["LearningModule"] = relationship("LearningModule", back_populates="user_progress")


# Gamified Learning Models
class WeeklyChallenge(Base):
    """Weekly community challenges."""
    
    __tablename__ = "weekly_challenges"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Challenge details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Requirements and rewards
    requirements: Mapped[str] = mapped_column(JSON, nullable=False)
    points_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_rewards: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Timeline
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    participations: Mapped[List["ChallengeParticipation"]] = relationship("ChallengeParticipation", back_populates="challenge")


class ChallengeParticipation(Base):
    """User participation in weekly challenges."""
    
    __tablename__ = "challenge_participations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("weekly_challenges.id", ondelete="CASCADE"), nullable=False)
    
    # Participation tracking
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Progress and results
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submission_data: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Rewards
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_earned: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    challenge: Mapped["WeeklyChallenge"] = relationship("WeeklyChallenge", back_populates="participations")


class UserPoints(Base):
    """User points tracking for gamification."""
    
    __tablename__ = "user_points"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Points tracking
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # For spending
    lifetime_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Level and streaks
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    points_to_next_level: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Activity tracking
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")


class UserAchievement(Base):
    """User achievements and badges."""
    
    __tablename__ = "user_achievements"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Achievement details
    achievement_type: Mapped[str] = mapped_column(String(50), nullable=False)  # skill_master, project_completed, etc.
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    badge_icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Achievement data
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="bronze", nullable=False)  # bronze, silver, gold
    
    # Progress tracking
    current_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_progress: Mapped[int] = mapped_column(Integer, nullable=False)
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="achievements")