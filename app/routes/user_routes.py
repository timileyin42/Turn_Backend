"""
User management routes for profile operations and account settings.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_admin
from app.services.user_service import user_service
from app.database.user_models import User
from app.schemas.user_schemas import (
    UserResponse, UserUpdate, UserProfileUpdate, UserPreferencesUpdate,
    MentorProfileCreate, MentorProfileUpdate, MentorProfileResponse,
    UserListResponse, UserSearchRequest
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get detailed profile information for the authenticated user"
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile."""
    try:
        user_response = await user_service.get_user_by_id(db, current_user.id)
        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update basic information for the authenticated user"
)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's basic information."""
    try:
        updated_user = await user_service.update_user(db, current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.put(
    "/me/profile",
    response_model=UserResponse,
    summary="Update user profile details",
    description="Update detailed profile information for the authenticated user"
)
async def update_my_profile_details(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile details."""
    try:
        updated_user = await user_service.update_user_profile(db, current_user.id, profile_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile details"
        )


@router.put(
    "/me/preferences",
    response_model=UserResponse,
    summary="Update user preferences",
    description="Update preferences and settings for the authenticated user"
)
async def update_my_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's preferences."""
    try:
        updated_user = await user_service.update_user_preferences(db, current_user.id, preferences_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )


@router.post(
    "/me/deactivate",
    summary="Deactivate account",
    description="Deactivate the authenticated user's account"
)
async def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate current user's account."""
    try:
        success = await user_service.deactivate_user(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to deactivate account"
            )
        return {"message": "Account deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


@router.get(
    "/me/stats",
    summary="Get user statistics",
    description="Get statistics and activity summary for the authenticated user"
)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's statistics."""
    try:
        stats = await user_service.get_user_stats(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


# Mentor Profile Routes

@router.post(
    "/me/mentor-profile",
    response_model=MentorProfileResponse,
    summary="Create mentor profile",
    description="Create mentor profile for the authenticated user"
)
async def create_my_mentor_profile(
    mentor_data: MentorProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create mentor profile for current user."""
    try:
        mentor_profile = await user_service.create_mentor_profile(db, current_user.id, mentor_data)
        if not mentor_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create mentor profile"
            )
        return mentor_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mentor profile"
        )


@router.get(
    "/me/mentor-profile",
    response_model=MentorProfileResponse,
    summary="Get mentor profile",
    description="Get mentor profile for the authenticated user"
)
async def get_my_mentor_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's mentor profile."""
    try:
        mentor_profile = await user_service.get_mentor_profile(db, current_user.id)
        if not mentor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor profile not found"
            )
        return mentor_profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mentor profile"
        )


@router.put(
    "/me/mentor-profile",
    response_model=MentorProfileResponse,
    summary="Update mentor profile",
    description="Update mentor profile for the authenticated user"
)
async def update_my_mentor_profile(
    mentor_data: MentorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's mentor profile."""
    try:
        mentor_profile = await user_service.update_mentor_profile(db, current_user.id, mentor_data)
        if not mentor_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor profile not found"
            )
        return mentor_profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mentor profile"
        )


@router.delete(
    "/me/mentor-profile",
    summary="Delete mentor profile",
    description="Delete mentor profile for the authenticated user"
)
async def delete_my_mentor_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user's mentor profile."""
    try:
        success = await user_service.delete_mentor_profile(db, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mentor profile not found"
            )
        return {"message": "Mentor profile deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete mentor profile"
        )


# Admin Routes

@router.get(
    "/",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
    description="Get paginated list of all users with search and filtering"
)
async def list_users(
    query: Optional[str] = Query(None, description="Search query"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    email_verified: Optional[bool] = Query(None, description="Filter by email verification status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)."""
    try:
        search_params = UserSearchRequest(
            query=query,
            role=role,
            is_active=is_active,
            email_verified=email_verified
        )
        
        return await user_service.search_users(db, search_params, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
    description="Get detailed user information by ID"
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)."""
    try:
        user_response = await user_service.get_user_by_id(db, user_id)
        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.post(
    "/{user_id}/reactivate",
    summary="Reactivate user (Admin only)",
    description="Reactivate a deactivated user account"
)
async def reactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Reactivate user account (admin only)."""
    try:
        success = await user_service.reactivate_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User reactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate user"
        )


@router.post(
    "/{user_id}/deactivate",
    summary="Deactivate user (Admin only)",
    description="Deactivate a user account"
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account (admin only)."""
    try:
        success = await user_service.deactivate_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )