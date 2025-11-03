"""
User management service for profile operations and user data handling.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.database.user_models import User, Profile, MentorProfile
from app.schemas.user_schemas import (
    UserResponse, UserUpdate, ProfileUpdate, UserPreferencesUpdate,
    MentorProfileCreate, MentorProfileUpdate, MentorProfileResponse,
    UserListResponse, UserSearchRequest
)


class UserService:
    """Service for user profile and account management operations."""
    
    async def get_user_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[UserResponse]:
        """
        Get user by ID with profile information.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User response with profile data
        """
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.mentor_profile)
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        return UserResponse.model_validate(user)
    
    async def update_user(
        self, 
        db: AsyncSession, 
        user_id: int, 
        user_data: UserUpdate
    ) -> Optional[UserResponse]:
        """
        Update user basic information.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: Updated user data
            
        Returns:
            Updated user response
        """
        # Get existing user
        user = await self._get_user_model_by_id(db, user_id)
        if not user:
            return None
        
        # Update fields that are provided
        update_data = user_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def update_user_profile(
        self, 
        db: AsyncSession, 
        user_id: int, 
        profile_data: ProfileUpdate
    ) -> Optional[UserResponse]:
        """
        Update user profile information.
        
        Args:
            db: Database session
            user_id: User ID
            profile_data: Updated profile data
            
        Returns:
            Updated user with profile
        """
        # Get or create user profile
        user = await self._get_user_model_by_id(db, user_id)
        if not user:
            return None
        
        if not user.profile:
            # Create new profile
            user.profile = Profile(user_id=user_id)
            db.add(user.profile)
        
        # Update profile fields
        update_data = profile_data.model_dump(exclude_unset=True)
        if update_data:
            import json
            # Convert list fields to JSON strings
            list_fields = ['target_industries', 'preferred_methodologies', 'preferred_job_types', 'excluded_companies']
            for field, value in update_data.items():
                if field in list_fields and isinstance(value, list):
                    # Convert list to JSON string
                    setattr(user.profile, field, json.dumps(value))
                else:
                    setattr(user.profile, field, value)
            
            user.profile.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def update_user_preferences(
        self, 
        db: AsyncSession, 
        user_id: int, 
        preferences_data: UserPreferencesUpdate
    ) -> Optional[UserResponse]:
        """
        Update user preferences.
        
        Args:
            db: Database session
            user_id: User ID
            preferences_data: Updated preferences
            
        Returns:
            Updated user with preferences
        """
        user = await self._get_user_model_by_id(db, user_id)
        if not user:
            return None
        
        if not user.profile:
            user.profile = Profile(user_id=user_id)
            db.add(user.profile)
        
        # Update preferences
        update_data = preferences_data.model_dump(exclude_unset=True)
        if update_data:
            # Handle timezone separately as it's a direct column
            if 'timezone' in update_data:
                user.profile.timezone = update_data.pop('timezone')
            
            # Merge remaining preferences with existing preferences
            if update_data:
                current_preferences = user.profile.preferences or {}
                current_preferences.update(update_data)
                user.profile.preferences = current_preferences
            
            user.profile.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(user)
        
        return UserResponse.model_validate(user)
    
    async def deactivate_user(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> bool:
        """
        Deactivate user account.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if user was deactivated
        """
        result = await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_active=False,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        return result.rowcount > 0
    
    async def reactivate_user(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> bool:
        """
        Reactivate user account.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if user was reactivated
        """
        result = await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                is_active=True,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        return result.rowcount > 0
    
    async def search_users(
        self, 
        db: AsyncSession, 
        search_params: UserSearchRequest,
        skip: int = 0,
        limit: int = 20
    ) -> UserListResponse:
        """
        Search users with filters.
        
        Args:
            db: Database session
            search_params: Search parameters
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Paginated user list
        """
        query = select(User).options(
            selectinload(User.profile),
            selectinload(User.mentor_profile)
        )
        
        # Apply filters
        conditions = []
        
        if search_params.query:
            search_term = f"%{search_params.query}%"
            conditions.append(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.username.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        if search_params.role:
            conditions.append(User.role == search_params.role)
        
        if search_params.is_active is not None:
            conditions.append(User.is_active == search_params.is_active)
        
        if search_params.email_verified is not None:
            conditions.append(User.email_verified == search_params.email_verified)
        
        if search_params.date_from:
            conditions.append(User.created_at >= search_params.date_from)
        
        if search_params.date_to:
            conditions.append(User.created_at <= search_params.date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total records
        count_result = await db.execute(
            select(User).where(and_(*conditions)) if conditions else select(User)
        )
        total = len(count_result.all())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    async def create_mentor_profile(
        self, 
        db: AsyncSession, 
        user_id: int, 
        mentor_data: MentorProfileCreate
    ) -> Optional[MentorProfileResponse]:
        """
        Create mentor profile for user.
        
        Args:
            db: Database session
            user_id: User ID
            mentor_data: Mentor profile data
            
        Returns:
            Created mentor profile
        """
        # Check if user exists and doesn't already have mentor profile
        user = await self._get_user_model_by_id(db, user_id)
        if not user:
            return None
        
        if user.mentor_profile:
            raise ValueError("User already has a mentor profile")
        
        # Create mentor profile
        mentor_profile = MentorProfile(
            user_id=user_id,
            **mentor_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Upgrade user role to MENTOR
        from app.database.user_models import UserRole
        user.role = UserRole.MENTOR
        user.updated_at = datetime.utcnow()
        
        db.add(mentor_profile)
        await db.commit()
        await db.refresh(mentor_profile)
        
        return MentorProfileResponse.model_validate(mentor_profile)
    
    async def update_mentor_profile(
        self, 
        db: AsyncSession, 
        user_id: int, 
        mentor_data: MentorProfileUpdate
    ) -> Optional[MentorProfileResponse]:
        """
        Update mentor profile.
        
        Args:
            db: Database session
            user_id: User ID
            mentor_data: Updated mentor data
            
        Returns:
            Updated mentor profile
        """
        # Get mentor profile
        result = await db.execute(
            select(MentorProfile).where(MentorProfile.user_id == user_id)
        )
        mentor_profile = result.scalar_one_or_none()
        
        if not mentor_profile:
            return None
        
        # Update fields
        update_data = mentor_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(mentor_profile, field, value)
            
            mentor_profile.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(mentor_profile)
        
        return MentorProfileResponse.model_validate(mentor_profile)
    
    async def get_mentor_profile(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[MentorProfileResponse]:
        """
        Get mentor profile by user ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Mentor profile if exists
        """
        result = await db.execute(
            select(MentorProfile).where(MentorProfile.user_id == user_id)
        )
        mentor_profile = result.scalar_one_or_none()
        
        if not mentor_profile:
            return None
        
        return MentorProfileResponse.model_validate(mentor_profile)
    
    async def delete_mentor_profile(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> bool:
        """
        Delete mentor profile.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if profile was deleted
        """
        result = await db.execute(
            select(MentorProfile).where(MentorProfile.user_id == user_id)
        )
        mentor_profile = result.scalar_one_or_none()
        
        if mentor_profile:
            await db.delete(mentor_profile)
            await db.commit()
            return True
        
        return False
    
    async def get_user_stats(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get user statistics and activity summary.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User statistics dictionary
        """
        user = await self._get_user_model_by_id(db, user_id)
        if not user:
            return {}
        
        # TODO: Implement stats aggregation queries
        # This would include project count, CV count, job applications, etc.
        # For now, return basic info
        
        return {
            "user_id": user_id,
            "account_created": user.created_at,
            "last_login": user.last_login_at,
            "email_verified": user.email_verified,
            "role": user.role,
            "is_active": user.is_active,
            "has_profile": user.profile is not None,
            "is_mentor": user.mentor_profile is not None
        }
    
    async def _get_user_model_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """Get user model with relationships loaded."""
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.mentor_profile)
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# Global user service instance
user_service = UserService()