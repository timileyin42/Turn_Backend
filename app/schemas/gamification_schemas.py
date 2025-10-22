"""
Gamification Pydantic v2 schemas for TURN platform.
Includes badges, challenges, streaks, points, and leaderboards.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.database.gamification_models import (
    BadgeType, BadgeRarity, ChallengeType, ChallengeStatus, StreakType
)


# Badge Schemas
class BadgeBase(BaseModel):
    """Base badge schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    badge_type: BadgeType
    rarity: BadgeRarity = BadgeRarity.COMMON
    icon_url: Optional[str] = Field(None, max_length=500)
    color_hex: str = Field("#ffd700", max_length=7)
    background_color_hex: str = Field("#ffffff", max_length=7)
    points_required: int = Field(0, ge=0)
    is_active: bool = True
    is_hidden: bool = False
    can_be_earned_multiple: bool = False


class BadgeCreate(BadgeBase):
    """Schema for creating a badge."""
    slug: str = Field(..., min_length=1, max_length=100)
    criteria: Dict[str, Any] = Field(..., description="Achievement criteria as JSON")
    prerequisites: Optional[List[int]] = None


class BadgeUpdate(BaseModel):
    """Schema for updating a badge."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_hidden: Optional[bool] = None
    points_required: Optional[int] = Field(None, ge=0)
    criteria: Optional[Dict[str, Any]] = None


class BadgeResponse(BadgeBase):
    """Badge response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    criteria: Dict[str, Any]
    prerequisites: Optional[List[int]] = None
    total_earned: int
    created_at: datetime
    updated_at: datetime


class UserBadgeResponse(BaseModel):
    """User badge progress and status."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    badge_id: int
    progress: int
    target: int
    is_completed: bool
    points_earned: int
    earned_at: Optional[datetime] = None
    is_visible: bool
    is_featured: bool
    started_at: datetime
    updated_at: datetime
    
    # Include badge details
    badge: Optional[BadgeResponse] = None


# Challenge Schemas
class ChallengeBase(BaseModel):
    """Base challenge schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    short_description: str = Field(..., min_length=1, max_length=300)
    challenge_type: ChallengeType
    category: str = Field(..., max_length=50)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    target_count: int = Field(1, ge=1)
    points_reward: int = Field(..., ge=0)
    start_date: datetime
    end_date: datetime
    is_featured: bool = False
    max_participants: Optional[int] = Field(None, ge=1)
    icon_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    color_theme: str = Field("blue", max_length=20)


class ChallengeCreate(ChallengeBase):
    """Schema for creating a challenge."""
    criteria: Dict[str, Any] = Field(..., description="Challenge completion criteria")
    badge_rewards: Optional[List[int]] = None
    bonus_rewards: Optional[Dict[str, Any]] = None


class ChallengeUpdate(BaseModel):
    """Schema for updating a challenge."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ChallengeStatus] = None
    is_featured: Optional[bool] = None
    max_participants: Optional[int] = Field(None, ge=1)


class ChallengeResponse(ChallengeBase):
    """Challenge response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    criteria: Dict[str, Any]
    badge_rewards: Optional[List[int]] = None
    bonus_rewards: Optional[Dict[str, Any]] = None
    status: ChallengeStatus
    total_participants: int
    total_completions: int
    created_at: datetime
    updated_at: datetime


class ChallengeParticipationResponse(BaseModel):
    """Challenge participation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    challenge_id: int
    current_progress: int
    target_progress: int
    is_completed: bool
    completion_percentage: float
    completed_at: Optional[datetime] = None
    points_earned: int
    rank: Optional[int] = None
    started_at: datetime
    last_activity_at: datetime
    
    # Include challenge details
    challenge: Optional[ChallengeResponse] = None


# Streak Schemas
class StreakResponse(BaseModel):
    """Streak response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    streak_type: StreakType
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[date] = None
    streak_start_date: Optional[date] = None
    longest_streak_start: Optional[date] = None
    longest_streak_end: Optional[date] = None
    streak_milestones: Optional[List[int]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StreakUpdateRequest(BaseModel):
    """Request to update a streak."""
    activity_date: Optional[date] = None


# Points and Transactions
class PointTransactionResponse(BaseModel):
    """Point transaction response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    transaction_type: str
    points: int
    source_type: str
    source_id: Optional[int] = None
    description: str
    metadata: Optional[Dict[str, Any]] = None
    balance_before: int
    balance_after: int
    created_at: datetime


class PointsAwardRequest(BaseModel):
    """Request to award points."""
    activity_type: str
    points: Optional[int] = None
    source_id: Optional[int] = None
    description: Optional[str] = None


# Leaderboard Schemas
class LeaderboardBase(BaseModel):
    """Base leaderboard schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    metric_type: str = Field(..., max_length=50)
    time_period: str = Field(..., pattern="^(daily|weekly|monthly|all_time)$")
    is_active: bool = True
    is_public: bool = True
    max_entries: int = Field(100, ge=1, le=1000)
    auto_update: bool = True


class LeaderboardCreate(LeaderboardBase):
    """Schema for creating a leaderboard."""
    slug: str = Field(..., min_length=1, max_length=100)


class LeaderboardResponse(LeaderboardBase):
    """Leaderboard response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    last_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    leaderboard_id: int
    user_id: int
    rank: int
    score: float
    previous_rank: Optional[int] = None
    rank_change: int
    additional_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # User info (would be populated by join)
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None


# User Level and Progression
class UserLevelResponse(BaseModel):
    """User level progression response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    current_level: int
    current_xp: int
    total_xp: int
    xp_to_next_level: int
    learning_level: int
    project_level: int
    cv_level: int
    job_level: int
    current_title: str
    unlocked_titles: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


# Comprehensive Stats
class GamificationStatsResponse(BaseModel):
    """Comprehensive gamification statistics."""
    user_id: int
    
    # Points and Level
    total_points: int
    available_points: int
    current_level: int
    current_title: str
    xp_to_next_level: int
    
    # Badges
    total_badges: int
    badges_by_rarity: Dict[str, int]
    recent_badges: Optional[List[UserBadgeResponse]] = None
    
    # Streaks
    current_streaks: Dict[str, int]
    longest_streaks: Dict[str, int]
    
    # Challenges
    active_challenges_count: int
    completed_challenges_count: Optional[int] = None
    
    # Activity
    last_activity: Optional[datetime] = None
    total_activities: Optional[int] = None
    
    # Rankings
    global_rank: Optional[int] = None
    monthly_rank: Optional[int] = None


# Dashboard and Summary Schemas
class GamificationDashboard(BaseModel):
    """Gamification dashboard data."""
    user_stats: GamificationStatsResponse
    featured_challenges: List[ChallengeResponse]
    recent_activities: List[PointTransactionResponse]
    upcoming_milestones: List[Dict[str, Any]]
    leaderboard_position: Optional[LeaderboardEntryResponse] = None
    suggested_actions: List[Dict[str, Any]]


class BadgeProgressResponse(BaseModel):
    """Badge progress tracking."""
    badge: BadgeResponse
    user_progress: Optional[UserBadgeResponse] = None
    completion_percentage: float
    next_milestone: Optional[int] = None
    is_achievable: bool


class WeeklyChallengesSummary(BaseModel):
    """Weekly challenges summary."""
    week_start: date
    week_end: date
    total_challenges: int
    active_challenges: List[ChallengeResponse]
    user_participations: List[ChallengeParticipationResponse]
    completed_count: int
    total_points_available: int
    total_points_earned: int


# Activity Feed
class ActivityFeedItem(BaseModel):
    """Individual activity feed item."""
    id: str
    activity_type: str
    title: str
    description: str
    points_earned: Optional[int] = None
    badge_earned: Optional[BadgeResponse] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ActivityFeedResponse(BaseModel):
    """Activity feed response."""
    activities: List[ActivityFeedItem]
    total_count: int
    page: int
    per_page: int
    has_more: bool


# Challenge Join/Leave
class ChallengeJoinRequest(BaseModel):
    """Request to join a challenge."""
    challenge_id: int = Field(..., gt=0)


class ChallengeJoinResponse(BaseModel):
    """Response for joining a challenge."""
    success: bool
    message: str
    participation: Optional[ChallengeParticipationResponse] = None


# Badge Award Response
class BadgeAwardResponse(BaseModel):
    """Response for badge award."""
    badge_earned: bool
    badge: Optional[BadgeResponse] = None
    points_awarded: int
    message: str
    milestone_reached: Optional[int] = None


# System Responses
class GamificationSystemResponse(BaseModel):
    """System-wide gamification response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None