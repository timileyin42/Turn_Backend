"""
Comprehensive gamification database models for TURN platform.
Includes badges, challenges, streaks, leaderboards, and reward systems.
"""
from datetime import datetime, date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Float, Enum as SQLEnum, Date, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User


class BadgeType(str, enum.Enum):
    """Badge type enumeration."""
    LEARNING = "learning"
    PROJECT = "project"
    CV = "cv"
    JOB = "job"
    PORTFOLIO = "portfolio"
    STREAK = "streak"
    COMMUNITY = "community"
    MILESTONE = "milestone"


class BadgeRarity(str, enum.Enum):
    """Badge rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class ChallengeType(str, enum.Enum):
    """Challenge type enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SPECIAL = "special"
    ACHIEVEMENT = "achievement"


class ChallengeStatus(str, enum.Enum):
    """Challenge status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    DRAFT = "draft"


class StreakType(str, enum.Enum):
    """Streak type enumeration."""
    DAILY_LOGIN = "daily_login"
    LEARNING = "learning"
    PROJECT_WORK = "project_work"
    JOB_APPLICATIONS = "job_applications"
    CV_UPDATES = "cv_updates"


class Badge(Base):
    """Badge definitions and metadata."""
    
    __tablename__ = "badges"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Badge identification
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Badge categorization
    badge_type: Mapped[BadgeType] = mapped_column(SQLEnum(BadgeType), nullable=False, index=True)
    rarity: Mapped[BadgeRarity] = mapped_column(SQLEnum(BadgeRarity), default=BadgeRarity.COMMON, nullable=False, index=True)
    
    # Visual elements
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color_hex: Mapped[str] = mapped_column(String(7), default="#ffd700", nullable=False)
    background_color_hex: Mapped[str] = mapped_column(String(7), default="#ffffff", nullable=False)
    
    # Requirements
    points_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    prerequisites: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of badge IDs
    criteria: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON object with achievement criteria
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)  # Hidden until unlocked
    can_be_earned_multiple: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Statistics
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user_badges: Mapped[List["UserBadge"]] = relationship("UserBadge", back_populates="badge")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_badge_type_rarity', 'badge_type', 'rarity'),
        Index('idx_badge_active_type', 'is_active', 'badge_type'),
        Index('idx_badge_hidden_active', 'is_hidden', 'is_active'),
        Index('idx_badge_points_type', 'points_required', 'badge_type'),
        Index('idx_badge_earned_rarity', 'total_earned', 'rarity'),
    )


class UserBadge(Base):
    """User earned badges tracking."""
    
    __tablename__ = "user_badges"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    
    # Progress tracking
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Earning details
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    earned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Display settings
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")


class Challenge(Base):
    """Weekly and special challenges."""
    
    __tablename__ = "challenges"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Challenge identification
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[str] = mapped_column(String(300), nullable=False)
    
    # Challenge categorization
    challenge_type: Mapped[ChallengeType] = mapped_column(SQLEnum(ChallengeType), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # learning, project, cv, job
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # easy, medium, hard
    
    # Requirements and criteria
    criteria: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON object with completion criteria
    target_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Rewards
    points_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    badge_rewards: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of badge IDs
    bonus_rewards: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON object with bonus rewards
    
    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Settings
    status: Mapped[ChallengeStatus] = mapped_column(SQLEnum(ChallengeStatus), default=ChallengeStatus.DRAFT, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Visual elements
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color_theme: Mapped[str] = mapped_column(String(20), default="blue", nullable=False)
    
    # Statistics
    total_participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_completions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    participations: Mapped[List["GameChallengeParticipation"]] = relationship("GameChallengeParticipation", back_populates="challenge")


class GameChallengeParticipation(Base):
    """User participation in challenges."""
    
    __tablename__ = "game_challenge_participations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    
    # Progress tracking
    current_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_progress: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Completion details
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Ranking among participants
    
    # Participation metadata
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="participations")


class UserStreak(Base):
    """User streak tracking for various activities."""
    
    __tablename__ = "user_streaks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Streak identification
    streak_type: Mapped[StreakType] = mapped_column(SQLEnum(StreakType), nullable=False)
    
    # Current streak tracking
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Date tracking
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    streak_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    longest_streak_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    longest_streak_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Milestones
    streak_milestones: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of achieved milestones
    
    # Settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")


class PointTransaction(Base):
    """Track all point gains and expenditures."""
    
    __tablename__ = "point_transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # earned, spent, bonus, penalty
    points: Mapped[int] = mapped_column(Integer, nullable=False)  # Can be negative for spending
    
    # Source/reason
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # project, cv, job, challenge, streak, etc.
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # ID of the source object
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Transaction metadata
    transaction_metadata: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Additional transaction data
    
    # Balance tracking
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")


class Leaderboard(Base):
    """Leaderboard tracking for various metrics."""
    
    __tablename__ = "leaderboards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Leaderboard identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Leaderboard settings
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # points, badges, projects, etc.
    time_period: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, all_time
    
    # Display settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_entries: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    
    # Update settings
    auto_update: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    entries: Mapped[List["LeaderboardEntry"]] = relationship("LeaderboardEntry", back_populates="leaderboard")


class LeaderboardEntry(Base):
    """Individual leaderboard entries."""
    
    __tablename__ = "leaderboard_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    leaderboard_id: Mapped[int] = mapped_column(ForeignKey("leaderboards.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Ranking details
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    previous_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rank_change: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional metrics
    additional_metrics: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON with extra data
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    leaderboard: Mapped["Leaderboard"] = relationship("Leaderboard", back_populates="entries")


class UserLevel(Base):
    """User level progression system."""
    
    __tablename__ = "user_levels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Level progression
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_to_next_level: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    
    # Level categories
    learning_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    project_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cv_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    job_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Titles and achievements
    current_title: Mapped[str] = mapped_column(String(100), default="Aspiring PM", nullable=False)
    unlocked_titles: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of unlocked titles
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="level_progression")