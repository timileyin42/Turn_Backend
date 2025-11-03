"""
Admin routes for user management, role assignment, and system administration.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel, EmailStr

from app.core.dependencies import (
    get_db, 
    get_current_user,
    require_admin,
    UserRole
)
from app.database.user_models import User
from app.schemas.user_schemas import UserResponse, UserListResponse
from app.core.rbac import rbac_service, Permission

router = APIRouter(prefix="/admin", tags=["Admin"])


class RoleUpdateRequest(BaseModel):
    """Request to update user role."""
    user_id: int
    new_role: UserRole


class BulkRoleUpdateRequest(BaseModel):
    """Request to update multiple users' roles."""
    user_ids: List[int]
    new_role: UserRole


class UserActivationRequest(BaseModel):
    """Request to activate/deactivate users."""
    user_id: int
    is_active: bool


class SystemStatsResponse(BaseModel):
    """System statistics response."""
    total_users: int
    active_users: int
    users_by_role: dict
    verified_users: int
    unverified_users: int
    total_mentors: int
    total_recruiters: int
    total_companies: int


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (Admin only)",
    description="Get paginated list of all users with filtering options"
)
async def list_all_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with filtering and pagination.
    
    **Permissions:** Admin only
    
    **Filters:**
    - role: Filter by user role
    - is_active: Filter by active status
    - is_verified: Filter by verification status
    - search: Search in username or email
    """
    # Build query
    query = select(User)
    
    # Apply filters
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)
    if search:
        query = query.where(
            (User.username.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%"))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
    description="Get detailed information about a specific user"
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID. Admin only."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role (Admin only)",
    description="Change a user's role (user, recruiter, company, mentor, admin)"
)
async def update_user_role(
    user_id: int,
    role_data: RoleUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user role.
    
    **Permissions:** Admin only
    
    **Available Roles:**
    - user: Regular job seeker/learner
    - recruiter: Can post jobs and review applications
    - company: Company representative with extended access
    - mentor: Provides mentorship and guidance
    - admin: Platform administrator
    """
    if user_id != role_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and body must match"
        )
    
    # Prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update role
    user.role = role_data.new_role
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.patch(
    "/users/bulk-role-update",
    summary="Bulk update user roles (Admin only)",
    description="Update roles for multiple users at once"
)
async def bulk_update_roles(
    bulk_data: BulkRoleUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update roles for multiple users.
    
    **Permissions:** Admin only
    
    **Warning:** This operation cannot be undone. Use with caution.
    """
    # Prevent admin from including themselves
    if current_user.id in bulk_data.user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role in bulk update"
        )
    
    # Update roles
    stmt = (
        update(User)
        .where(User.id.in_(bulk_data.user_ids))
        .values(role=bulk_data.new_role)
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    return {
        "message": f"Updated roles for {result.rowcount} users",
        "updated_count": result.rowcount,
        "new_role": bulk_data.new_role.value
    }


@router.patch(
    "/users/{user_id}/activation",
    response_model=UserResponse,
    summary="Activate/deactivate user (Admin only)",
    description="Enable or disable a user account"
)
async def update_user_activation(
    user_id: int,
    activation_data: UserActivationRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate or deactivate a user account.
    
    **Permissions:** Admin only
    
    **Note:** Deactivated users cannot login or access the platform.
    """
    if user_id != activation_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path and body must match"
        )
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate your own account"
        )
    
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update activation status
    user.is_active = activation_data.is_active
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    summary="Delete user permanently (Admin only)",
    description="Permanently delete a user and all their data"
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete a user.
    
    **Permissions:** Admin only
    
    **Warning:** This action cannot be undone. All user data will be deleted.
    """
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Delete user (cascade will handle related records)
    await db.delete(user)
    await db.commit()
    
    return {
        "message": f"User {user.username} (ID: {user_id}) deleted successfully",
        "deleted_user_id": user_id
    }


@router.get(
    "/stats",
    response_model=SystemStatsResponse,
    summary="Get system statistics (Admin only)",
    description="Get overall platform statistics and metrics"
)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide statistics.
    
    **Permissions:** Admin only
    
    **Returns:**
    - Total users
    - Active users
    - Users by role
    - Verification statistics
    """
    # Total users
    total_query = select(func.count(User.id))
    total_result = await db.execute(total_query)
    total_users = total_result.scalar_one()
    
    # Active users
    active_query = select(func.count(User.id)).where(User.is_active == True)
    active_result = await db.execute(active_query)
    active_users = active_result.scalar_one()
    
    # Verified users
    verified_query = select(func.count(User.id)).where(User.is_verified == True)
    verified_result = await db.execute(verified_query)
    verified_users = verified_result.scalar_one()
    
    # Users by role
    users_by_role = {}
    for role in UserRole:
        role_query = select(func.count(User.id)).where(User.role == role)
        role_result = await db.execute(role_query)
        users_by_role[role.value] = role_result.scalar_one()
    
    return SystemStatsResponse(
        total_users=total_users,
        active_users=active_users,
        users_by_role=users_by_role,
        verified_users=verified_users,
        unverified_users=total_users - verified_users,
        total_mentors=users_by_role.get("mentor", 0),
        total_recruiters=users_by_role.get("recruiter", 0),
        total_companies=users_by_role.get("company", 0)
    )


@router.get(
    "/permissions/{user_id}",
    summary="Get user permissions (Admin only)",
    description="Get all permissions for a specific user based on their role"
)
async def get_user_permissions(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all permissions for a user.
    
    **Permissions:** Admin only
    
    **Returns:** List of permissions the user has based on their role
    """
    # Get user
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    permissions = rbac_service.get_user_permissions(user)
    
    return {
        "user_id": user_id,
        "username": user.username,
        "role": user.role.value,
        "permissions": permissions,
        "permission_count": len(permissions)
    }


@router.post(
    "/verify-email/{user_id}",
    summary="Manually verify user email (Admin only)",
    description="Admin can manually verify a user's email"
)
async def manually_verify_email(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually verify a user's email.
    
    **Permissions:** Admin only
    
    **Use case:** Help users who have email verification issues
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    if user.is_verified:
        return {
            "message": "User email already verified",
            "user_id": user_id
        }
    
    user.is_verified = True
    await db.commit()
    
    return {
        "message": f"Email verified for user {user.username}",
        "user_id": user_id
    }
