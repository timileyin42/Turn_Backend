"""
Gamification routes for TURN platform.
Handles badges, challenges, streaks, points, and leaderboards.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.database.user_models import User
from app.database.gamification_models import (
    Badge, Challenge, GameChallengeParticipation, UserStreak,
    PointTransaction, Leaderboard, LeaderboardEntry, UserLevel,
    ChallengeStatus
)
from app.services.gamification_service import GamificationService
from app.schemas.gamification_schemas import (
    # Badge schemas
    BadgeResponse, BadgeCreate, BadgeUpdate, UserBadgeResponse, BadgeProgressResponse,
    BadgeAwardResponse,
    
    # Challenge schemas
    ChallengeResponse, ChallengeCreate, ChallengeUpdate, ChallengeParticipationResponse,
    ChallengeJoinRequest, ChallengeJoinResponse, WeeklyChallengesSummary,
    
    # Streak schemas
    StreakResponse, StreakUpdateRequest,
    
    # Points schemas
    PointTransactionResponse, PointsAwardRequest,
    
    # Leaderboard schemas
    LeaderboardResponse, LeaderboardCreate, LeaderboardEntryResponse,
    
    # Level schemas
    UserLevelResponse,
    
    # Comprehensive schemas
    GamificationStatsResponse, GamificationDashboard, ActivityFeedResponse,
    GamificationSystemResponse
)

router = APIRouter(prefix="/gamification", tags=["gamification"])


# Helper function to get gamification service
def get_gamification_service() -> GamificationService:
    """Get gamification service instance."""
    return GamificationService()


@router.get("/badges", response_model=List[BadgeResponse])
async def get_all_badges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    badge_type: Optional[str] = None,
    rarity: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available badges with optional filtering."""
    gamification_service = get_gamification_service()
    badges = await gamification_service.get_all_badges(
        db, skip=skip, limit=limit, badge_type=badge_type, rarity=rarity
    )
    return badges


@router.get("/badges/{badge_id}", response_model=BadgeResponse)
async def get_badge_details(
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific badge."""
    gamification_service = get_gamification_service()
    badge = await gamification_service.get_badge_by_id(db, badge_id)
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")
    return badge


@router.get("/my-badges", response_model=List[UserBadgeResponse])
async def get_user_badges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    completed_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's badges and progress."""
    gamification_service = get_gamification_service()
    user_badges = await gamification_service.get_user_badges(
        db, user_id=current_user.id, earned_only=completed_only
    )
    return user_badges


@router.get("/badge-progress", response_model=List[BadgeProgressResponse])
async def get_badge_progress(
    badge_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's progress towards all badges."""
    gamification_service = get_gamification_service()
    progress = await gamification_service.get_badge_progress(
        db, user_id=current_user.id
    )
    return progress


@router.post("/badges", response_model=BadgeResponse)
async def create_badge(
    badge_data: BadgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new badge (admin only)."""
    # TODO: Add admin permission check
    gamification_service = get_gamification_service()
    badge = await gamification_service.create_badge(db, badge_data.model_dump())
    return badge


@router.get("/challenges", response_model=List[ChallengeResponse])
async def get_challenges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    challenge_type: Optional[str] = None,
    status: Optional[str] = None,
    featured_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available challenges with optional filtering."""
    gamification_service = get_gamification_service()
    challenges = await gamification_service.get_challenges(
        db, skip=skip, limit=limit, status=status, 
        challenge_type=challenge_type, featured_only=featured_only
    )
    return challenges


@router.get("/challenges/weekly", response_model=WeeklyChallengesSummary)
async def get_weekly_challenges(
    week_offset: int = Query(0, description="Weeks from current (0=this week, -1=last week)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weekly challenges summary for a specific week."""
    gamification_service = get_gamification_service()
    summary = await gamification_service.get_weekly_challenges_summary(
        db, user_id=current_user.id, week_offset=week_offset
    )
    return summary


@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge_details(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific challenge."""
    gamification_service = get_gamification_service()
    challenge = await gamification_service.get_challenge_by_id(db, challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@router.get("/my-challenges", response_model=List[ChallengeParticipationResponse])
async def get_user_challenges(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    completed_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's challenge participations."""
    gamification_service = get_gamification_service()
    participations = await gamification_service.get_user_challenge_participations(
        db, user_id=current_user.id, completed_only=completed_only if completed_only else None
    )
    return participations


@router.post("/challenges/{challenge_id}/join", response_model=ChallengeJoinResponse)
async def join_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Join a challenge."""
    gamification_service = get_gamification_service()
    
    try:
        participation = await gamification_service.join_challenge(
            db, user_id=current_user.id, challenge_id=challenge_id
        )
        return ChallengeJoinResponse(
            success=True,
            message="Successfully joined challenge",
            participation=participation
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to join challenge")


@router.post("/challenges/{challenge_id}/leave", response_model=GamificationSystemResponse)
async def leave_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Leave a challenge."""
    gamification_service = get_gamification_service()
    
    try:
        success = await gamification_service.leave_challenge(
            db, user_id=current_user.id, challenge_id=challenge_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Challenge participation not found")
        return GamificationSystemResponse(
            success=True,
            message="Successfully left challenge"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenges", response_model=ChallengeResponse)
async def create_challenge(
    challenge_data: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new challenge (admin only)."""
    # TODO: Add admin permission check
    gamification_service = get_gamification_service()
    challenge = await gamification_service.create_challenge(db, challenge_data.model_dump())
    return challenge


@router.get("/streaks", response_model=List[StreakResponse])
async def get_user_streaks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's streaks."""
    gamification_service = get_gamification_service()
    streaks = await gamification_service.get_user_streaks(db, user_id=current_user.id)
    return streaks


@router.post("/streaks/{streak_type}/update", response_model=StreakResponse)
async def update_streak(
    streak_type: str,
    streak_data: StreakUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific streak type for the user."""
    gamification_service = get_gamification_service()
    
    try:
        # Update streak in background for better performance
        background_tasks.add_task(
            gamification_service.update_streak,
            db,
            current_user.id,
            streak_type,
            streak_data.activity_date
        )
        
        # Return current streak immediately
        streak = await gamification_service.get_user_streak(db, current_user.id, streak_type)
        if not streak:
            raise HTTPException(status_code=404, detail="Streak not found")
        return streak
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/points/balance", response_model=Dict[str, int])
async def get_points_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's points balance."""
    gamification_service = get_gamification_service()
    stats = await gamification_service.get_user_stats(db, current_user.id)
    return {
        "total_points": stats.get("total_points", 0),
        "available_points": stats.get("available_points", 0)
    }


@router.get("/points/transactions", response_model=List[PointTransactionResponse])
async def get_point_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's point transaction history."""
    gamification_service = get_gamification_service()
    transactions = await gamification_service.get_point_transactions(
        db, user_id=current_user.id, skip=skip, limit=limit, transaction_type=transaction_type
    )
    return transactions


@router.post("/points/award", response_model=PointTransactionResponse)
async def award_points(
    points_data: PointsAwardRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Award points to user for an activity."""
    gamification_service = get_gamification_service()
    
    try:
        # Award points
        points_awarded, level_up = await gamification_service.award_points(
            db,
            user_id=current_user.id,
            activity_type=points_data.activity_type,
            points=points_data.points,
            source_id=points_data.source_id,
            description=points_data.description
        )
        
        # Check for badge achievements in background
        background_tasks.add_task(
            gamification_service.check_and_award_badges,
            db,
            current_user.id,
            points_data.activity_type
        )
        
        # Get the transaction record
        transactions = await gamification_service.get_point_transactions(db, current_user.id, limit=1)
        return transactions[0] if transactions else None
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/leaderboards", response_model=List[LeaderboardResponse])
async def get_leaderboards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available leaderboards."""
    gamification_service = get_gamification_service()
    leaderboards = await gamification_service.get_leaderboards(db)
    return leaderboards


@router.get("/leaderboards/{leaderboard_id}", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard_entries(
    leaderboard_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leaderboard entries."""
    gamification_service = get_gamification_service()
    entries = await gamification_service.get_leaderboard_entries(
        db, leaderboard_id=leaderboard_id, skip=skip, limit=limit
    )
    return entries


@router.get("/leaderboards/{leaderboard_id}/my-position", response_model=LeaderboardEntryResponse)
async def get_my_leaderboard_position(
    leaderboard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's position in a specific leaderboard."""
    gamification_service = get_gamification_service()
    entry = await gamification_service.get_user_leaderboard_position(
        db, user_id=current_user.id, leaderboard_id=leaderboard_id
    )
    if not entry:
        raise HTTPException(status_code=404, detail="User not found in leaderboard")
    return entry



@router.get("/level", response_model=UserLevelResponse)
async def get_user_level(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's level and progression."""
    gamification_service = get_gamification_service()
    level = await gamification_service.get_user_level(db, current_user.id)
    if not level:
        raise HTTPException(status_code=404, detail="User level not found. Please initialize gamification first.")
    return level


@router.post("/level/update", response_model=UserLevelResponse)
async def update_user_level(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate and update user's level progression."""
    gamification_service = get_gamification_service()
    
    # Update level progression in background
    background_tasks.add_task(
        gamification_service.update_user_level,
        db,
        current_user.id
    )
    
    # Return current level immediately
    level = await gamification_service.get_user_level(db, current_user.id)
    if not level:
        raise HTTPException(status_code=404, detail="User level not found")
    return level


@router.get("/stats", response_model=GamificationStatsResponse)
async def get_gamification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive gamification statistics for the user."""
    gamification_service = get_gamification_service()
    stats = await gamification_service.get_comprehensive_stats(db, current_user.id)
    return stats


@router.get("/dashboard", response_model=GamificationDashboard)
async def get_gamification_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get gamification dashboard data."""
    gamification_service = get_gamification_service()
    dashboard = await gamification_service.get_dashboard_data(db, current_user.id)
    return dashboard


@router.get("/activity-feed", response_model=ActivityFeedResponse)
async def get_activity_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's gamification activity feed."""
    gamification_service = get_gamification_service()
    activity_feed = await gamification_service.get_activity_feed(
        db, user_id=current_user.id, skip=skip, limit=limit, activity_type=activity_type
    )
    return activity_feed



@router.post("/initialize", response_model=GamificationSystemResponse)
async def initialize_user_gamification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize gamification system for the current user."""
    gamification_service = get_gamification_service()
    
    try:
        await gamification_service.initialize_user(db, current_user.id)
        return GamificationSystemResponse(
            success=True,
            message="Gamification system initialized successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to initialize gamification system")


@router.post("/refresh-achievements", response_model=GamificationSystemResponse)
async def refresh_user_achievements(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh and recalculate user's achievements, badges, and progress."""
    gamification_service = get_gamification_service()
    
    # Refresh achievements in background
    background_tasks.add_task(
        gamification_service.refresh_user_achievements,
        db,
        current_user.id
    )
    
    return GamificationSystemResponse(
        success=True,
        message="Achievement refresh initiated"
    )



@router.post("/hooks/activity", response_model=GamificationSystemResponse)
async def activity_hook(
    activity_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Hook for other services to trigger gamification events.
    Called when users complete activities (CV updates, project uploads, etc.)
    """
    gamification_service = get_gamification_service()
    
    # Process gamification events in background
    background_tasks.add_task(
        gamification_service.process_activity_event,
        db,
        current_user.id,
        activity_data
    )
    
    return GamificationSystemResponse(
        success=True,
        message="Activity processed for gamification"
    )
