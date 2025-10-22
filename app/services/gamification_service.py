"""
Comprehensive gamification service for TURN platform.
Handles badges, challenges, streaks, points, leaderboards, and user progression.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload

from app.database.gamification_models import (
    Badge, UserBadge, Challenge, GameChallengeParticipation, UserStreak,
    PointTransaction, Leaderboard, LeaderboardEntry, UserLevel,
    BadgeType, BadgeRarity, ChallengeType, ChallengeStatus, StreakType
)
from app.database.platform_models import UserPoints
from app.schemas.gamification_schemas import (
    BadgeResponse, UserBadgeResponse, ChallengeResponse, 
    ChallengeParticipationResponse, StreakResponse, LeaderboardResponse,
    UserLevelResponse, PointTransactionResponse, GamificationStatsResponse
)


class GamificationService:
    """Service for all gamification features."""
    
    # Points awarded for different activities
    POINT_VALUES = {
        'daily_login': 5,
        'complete_lesson': 10,
        'complete_project': 50,
        'create_cv': 25,
        'apply_to_job': 15,
        'complete_challenge': 100,
        'streak_milestone': 20,
        'earn_badge': 30,
        'portfolio_update': 10,
        'profile_complete': 40
    }
    
    # XP calculation
    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate total XP required to reach a specific level."""
        return level * 100 + (level - 1) * 50  # Progressive XP requirement
    
    async def initialize_user_gamification(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Initialize gamification data for a new user."""
        try:
            # Create user points record
            user_points = UserPoints(
                user_id=user_id,
                total_points=0,
                available_points=0,
                lifetime_points=0,
                current_level=1,
                points_to_next_level=100,
                current_streak=0,
                longest_streak=0
            )
            db.add(user_points)
            
            # Create user level progression
            user_level = UserLevel(
                user_id=user_id,
                current_level=1,
                current_xp=0,
                total_xp=0,
                xp_to_next_level=100,
                current_title="Aspiring PM"
            )
            db.add(user_level)
            
            # Initialize basic streaks
            streak_types = [StreakType.DAILY_LOGIN, StreakType.LEARNING, StreakType.PROJECT_WORK]
            for streak_type in streak_types:
                user_streak = UserStreak(
                    user_id=user_id,
                    streak_type=streak_type,
                    current_streak=0,
                    longest_streak=0
                )
                db.add(user_streak)
            
            await db.commit()
            
            return {
                "message": "Gamification initialized successfully",
                "user_id": user_id,
                "initial_points": 0,
                "initial_level": 1,
                "streaks_initialized": len(streak_types)
            }
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def award_points(
        self,
        db: AsyncSession,
        user_id: int,
        activity_type: str,
        points: Optional[int] = None,
        source_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Tuple[int, bool]:
        """Award points to a user and check for level up."""
        try:
            # Get points to award
            points_to_award = points or self.POINT_VALUES.get(activity_type, 0)
            if points_to_award <= 0:
                return 0, False
            
            # Get user points record
            result = await db.execute(
                select(UserPoints).where(UserPoints.user_id == user_id)
            )
            user_points = result.scalar_one_or_none()
            
            if not user_points:
                await self.initialize_user_gamification(db, user_id)
                result = await db.execute(
                    select(UserPoints).where(UserPoints.user_id == user_id)
                )
                user_points = result.scalar_one()
            
            # Record the transaction
            transaction = PointTransaction(
                user_id=user_id,
                transaction_type="earned",
                points=points_to_award,
                source_type=activity_type,
                source_id=source_id,
                description=description or f"Points for {activity_type}",
                balance_before=user_points.total_points,
                balance_after=user_points.total_points + points_to_award
            )
            db.add(transaction)
            
            # Update user points
            old_level = user_points.current_level
            user_points.total_points += points_to_award
            user_points.available_points += points_to_award
            user_points.lifetime_points += points_to_award
            
            # Check for level up
            level_up = await self._check_level_progression(db, user_id, user_points)
            
            await db.commit()
            
            return points_to_award, level_up
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def _check_level_progression(
        self,
        db: AsyncSession,
        user_id: int,
        user_points: UserPoints
    ) -> bool:
        """Check and update user level progression."""
        current_level = user_points.current_level
        required_points = self.calculate_xp_for_level(current_level + 1)
        
        level_up = False
        while user_points.total_points >= required_points:
            current_level += 1
            level_up = True
            required_points = self.calculate_xp_for_level(current_level + 1)
        
        if level_up:
            user_points.current_level = current_level
            user_points.points_to_next_level = required_points - user_points.total_points
            
            # Update UserLevel record
            result = await db.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = result.scalar_one_or_none()
            
            if user_level:
                user_level.current_level = current_level
                user_level.total_xp = user_points.total_points
                user_level.xp_to_next_level = user_points.points_to_next_level
                
                # Update title based on level
                new_title = self._get_title_for_level(current_level)
                if new_title != user_level.current_title:
                    user_level.current_title = new_title
        
        return level_up
    
    def _get_title_for_level(self, level: int) -> str:
        """Get title based on user level."""
        if level >= 50:
            return "PM Master"
        elif level >= 40:
            return "Senior PM"
        elif level >= 30:
            return "Project Manager"
        elif level >= 20:
            return "Junior PM"
        elif level >= 10:
            return "PM Associate"
        elif level >= 5:
            return "PM Trainee"
        else:
            return "Aspiring PM"
    
    async def update_streak(
        self,
        db: AsyncSession,
        user_id: int,
        streak_type: StreakType,
        activity_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Update user streak for a specific activity."""
        try:
            if not activity_date:
                activity_date = date.today()
            
            # Get user streak record
            result = await db.execute(
                select(UserStreak).where(
                    and_(
                        UserStreak.user_id == user_id,
                        UserStreak.streak_type == streak_type
                    )
                )
            )
            user_streak = result.scalar_one_or_none()
            
            if not user_streak:
                user_streak = UserStreak(
                    user_id=user_id,
                    streak_type=streak_type,
                    current_streak=0,
                    longest_streak=0
                )
                db.add(user_streak)
            
            # Check if streak should continue
            streak_broken = False
            streak_extended = False
            
            if user_streak.last_activity_date:
                days_diff = (activity_date - user_streak.last_activity_date).days
                
                if days_diff == 1:
                    # Streak continues
                    user_streak.current_streak += 1
                    streak_extended = True
                elif days_diff == 0:
                    # Same day, no change
                    pass
                else:
                    # Streak broken
                    user_streak.current_streak = 1
                    user_streak.streak_start_date = activity_date
                    streak_broken = True
            else:
                # First activity
                user_streak.current_streak = 1
                user_streak.streak_start_date = activity_date
                streak_extended = True
            
            # Update longest streak
            if user_streak.current_streak > user_streak.longest_streak:
                user_streak.longest_streak = user_streak.current_streak
                user_streak.longest_streak_start = user_streak.streak_start_date
                user_streak.longest_streak_end = activity_date
            
            user_streak.last_activity_date = activity_date
            user_streak.updated_at = datetime.utcnow()
            
            # Award points for streak milestones
            milestone_reached = None
            if streak_extended and user_streak.current_streak in [7, 14, 30, 60, 100]:
                milestone_reached = user_streak.current_streak
                await self.award_points(
                    db, user_id, 'streak_milestone',
                    points=milestone_reached,
                    description=f"{streak_type.value} streak milestone: {milestone_reached} days"
                )
            
            await db.commit()
            
            return {
                "streak_type": streak_type.value,
                "current_streak": user_streak.current_streak,
                "longest_streak": user_streak.longest_streak,
                "streak_extended": streak_extended,
                "streak_broken": streak_broken,
                "milestone_reached": milestone_reached
            }
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def check_and_award_badge(
        self,
        db: AsyncSession,
        user_id: int,
        badge_slug: str,
        progress_increment: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Check if user should earn a badge and award it."""
        try:
            # Get badge definition
            badge_result = await db.execute(
                select(Badge).where(Badge.slug == badge_slug)
            )
            badge = badge_result.scalar_one_or_none()
            
            if not badge or not badge.is_active:
                return None
            
            # Get or create user badge progress
            user_badge_result = await db.execute(
                select(UserBadge).where(
                    and_(
                        UserBadge.user_id == user_id,
                        UserBadge.badge_id == badge.id
                    )
                )
            )
            user_badge = user_badge_result.scalar_one_or_none()
            
            if not user_badge:
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    progress=0,
                    target=badge.criteria.get('target', 1) if isinstance(badge.criteria, dict) else 1
                )
                db.add(user_badge)
            
            # Update progress
            if not user_badge.is_completed:
                user_badge.progress += progress_increment
                user_badge.updated_at = datetime.utcnow()
                
                # Check if badge is earned
                if user_badge.progress >= user_badge.target:
                    user_badge.is_completed = True
                    user_badge.earned_at = datetime.utcnow()
                    
                    # Award points
                    await self.award_points(
                        db, user_id, 'earn_badge',
                        points=badge.points_required,
                        source_id=badge.id,
                        description=f"Earned badge: {badge.name}"
                    )
                    
                    # Update badge statistics
                    badge.total_earned += 1
                    
                    await db.commit()
                    
                    return {
                        "badge_earned": True,
                        "badge_name": badge.name,
                        "badge_description": badge.description,
                        "points_awarded": badge.points_required,
                        "rarity": badge.rarity.value
                    }
            
            await db.commit()
            return None
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def create_challenge(
        self,
        db: AsyncSession,
        challenge_data: Dict[str, Any]
    ) -> ChallengeResponse:
        """Create a new challenge."""
        try:
            challenge = Challenge(**challenge_data)
            db.add(challenge)
            await db.commit()
            await db.refresh(challenge)
            
            return ChallengeResponse.model_validate(challenge)
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def join_challenge(
        self,
        db: AsyncSession,
        user_id: int,
        challenge_id: int
    ) -> ChallengeParticipationResponse:
        """Join a user to a challenge."""
        try:
            # Check if challenge exists and is active
            challenge_result = await db.execute(
                select(Challenge).where(Challenge.id == challenge_id)
            )
            challenge = challenge_result.scalar_one_or_none()
            
            if not challenge or challenge.status != ChallengeStatus.ACTIVE:
                raise ValueError("Challenge not found or not active")
            
            # Check if user already joined
            existing_result = await db.execute(
                select(GameChallengeParticipation).where(
                    and_(
                        GameChallengeParticipation.user_id == user_id,
                        GameChallengeParticipation.challenge_id == challenge_id
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                return ChallengeParticipationResponse.model_validate(existing)
            
            # Create participation
            participation = GameChallengeParticipation(
                user_id=user_id,
                challenge_id=challenge_id,
                target_progress=challenge.target_count
            )
            db.add(participation)
            
            # Update challenge participant count
            challenge.total_participants += 1
            
            await db.commit()
            await db.refresh(participation)
            
            return ChallengeParticipationResponse.model_validate(participation)
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def update_challenge_progress(
        self,
        db: AsyncSession,
        user_id: int,
        challenge_id: int,
        progress_increment: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Update user's progress in a challenge."""
        try:
            # Get participation record
            result = await db.execute(
                select(GameChallengeParticipation)
                .options(selectinload(GameChallengeParticipation.challenge))
                .where(
                    and_(
                        GameChallengeParticipation.user_id == user_id,
                        GameChallengeParticipation.challenge_id == challenge_id
                    )
                )
            )
            participation = result.scalar_one_or_none()
            
            if not participation or participation.is_completed:
                return None
            
            # Update progress
            participation.current_progress += progress_increment
            participation.completion_percentage = min(
                (participation.current_progress / participation.target_progress) * 100, 100
            )
            participation.last_activity_at = datetime.utcnow()
            
            # Check if challenge is completed
            if participation.current_progress >= participation.target_progress:
                participation.is_completed = True
                participation.completed_at = datetime.utcnow()
                
                # Award points
                challenge = participation.challenge
                await self.award_points(
                    db, user_id, 'complete_challenge',
                    points=challenge.points_reward,
                    source_id=challenge_id,
                    description=f"Completed challenge: {challenge.title}"
                )
                
                # Update challenge completion count
                challenge.total_completions += 1
                
                await db.commit()
                
                return {
                    "challenge_completed": True,
                    "challenge_title": challenge.title,
                    "points_awarded": challenge.points_reward,
                    "completion_time": participation.completed_at
                }
            
            await db.commit()
            return None
            
        except Exception as e:
            await db.rollback()
            raise e
    
    async def get_user_gamification_stats(
        self,
        db: AsyncSession,
        user_id: int
    ) -> GamificationStatsResponse:
        """Get comprehensive gamification stats for a user."""
        try:
            # Get user points and level
            points_result = await db.execute(
                select(UserPoints).where(UserPoints.user_id == user_id)
            )
            user_points = points_result.scalar_one_or_none()
            
            level_result = await db.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = level_result.scalar_one_or_none()
            
            # Get badges
            badges_result = await db.execute(
                select(UserBadge)
                .options(selectinload(UserBadge.badge))
                .where(
                    and_(
                        UserBadge.user_id == user_id,
                        UserBadge.is_completed == True
                    )
                )
            )
            earned_badges = badges_result.scalars().all()
            
            # Get streaks
            streaks_result = await db.execute(
                select(UserStreak).where(UserStreak.user_id == user_id)
            )
            streaks = streaks_result.scalars().all()
            
            # Get active challenges
            challenges_result = await db.execute(
                select(GameChallengeParticipation)
                .options(selectinload(GameChallengeParticipation.challenge))
                .where(
                    and_(
                        GameChallengeParticipation.user_id == user_id,
                        GameChallengeParticipation.is_completed == False
                    )
                )
            )
            active_challenges = challenges_result.scalars().all()
            
            return GamificationStatsResponse(
                user_id=user_id,
                total_points=user_points.total_points if user_points else 0,
                available_points=user_points.available_points if user_points else 0,
                current_level=user_level.current_level if user_level else 1,
                current_title=user_level.current_title if user_level else "Aspiring PM",
                xp_to_next_level=user_level.xp_to_next_level if user_level else 100,
                total_badges=len(earned_badges),
                badges_by_rarity={
                    rarity.value: len([b for b in earned_badges if b.badge.rarity == rarity])
                    for rarity in BadgeRarity
                },
                current_streaks={
                    streak.streak_type.value: streak.current_streak 
                    for streak in streaks
                },
                longest_streaks={
                    streak.streak_type.value: streak.longest_streak 
                    for streak in streaks
                },
                active_challenges_count=len(active_challenges),
                last_activity=user_points.last_activity_date if user_points else None
            )
            
        except Exception as e:
            raise e


# Create service instance
gamification_service = GamificationService()