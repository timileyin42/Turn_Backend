"""
Role-Based Access Control (RBAC) utilities and permission system.

This module provides:
- Role hierarchy and permissions
- Permission decorators for endpoints
- Resource ownership checks
- Fine-grained access control
"""
from typing import List, Callable, Optional
from functools import wraps
from fastapi import HTTPException, status

from app.database.user_models import User, UserRole


class Permission:
    """Permission constants for RBAC."""
    
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Job permissions
    JOB_READ = "job:read"
    JOB_CREATE = "job:create"
    JOB_UPDATE = "job:update"
    JOB_DELETE = "job:delete"
    JOB_APPLY = "job:apply"
    
    # Application permissions
    APPLICATION_READ = "application:read"
    APPLICATION_WRITE = "application:write"
    APPLICATION_REVIEW = "application:review"
    
    # CV permissions
    CV_READ = "cv:read"
    CV_WRITE = "cv:write"
    CV_DELETE = "cv:delete"
    
    # Project permissions
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    
    # Mentor permissions
    MENTOR_READ = "mentor:read"
    MENTOR_WRITE = "mentor:write"
    MENTORSHIP_CREATE = "mentorship:create"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    SYSTEM_SETTINGS = "system:settings"
    
    # Company permissions
    COMPANY_READ = "company:read"
    COMPANY_WRITE = "company:write"
    COMPANY_PROFILE = "company:profile"


# Role-based permission mapping
ROLE_PERMISSIONS = {
    UserRole.USER: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.JOB_READ,
        Permission.JOB_APPLY,
        Permission.APPLICATION_READ,
        Permission.APPLICATION_WRITE,
        Permission.CV_READ,
        Permission.CV_WRITE,
        Permission.CV_DELETE,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.PROJECT_DELETE,
        Permission.MENTOR_READ,
    ],
    
    UserRole.RECRUITER: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.JOB_READ,
        Permission.JOB_CREATE,
        Permission.JOB_UPDATE,
        Permission.JOB_DELETE,
        Permission.APPLICATION_READ,
        Permission.APPLICATION_REVIEW,
        Permission.CV_READ,
        Permission.COMPANY_READ,
        Permission.COMPANY_WRITE,
    ],
    
    UserRole.COMPANY: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.JOB_READ,
        Permission.JOB_CREATE,
        Permission.JOB_UPDATE,
        Permission.JOB_DELETE,
        Permission.APPLICATION_READ,
        Permission.APPLICATION_REVIEW,
        Permission.CV_READ,
        Permission.COMPANY_READ,
        Permission.COMPANY_WRITE,
        Permission.COMPANY_PROFILE,
    ],
    
    UserRole.MENTOR: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.JOB_READ,
        Permission.APPLICATION_READ,
        Permission.CV_READ,
        Permission.PROJECT_READ,
        Permission.MENTOR_READ,
        Permission.MENTOR_WRITE,
        Permission.MENTORSHIP_CREATE,
    ],
    
    UserRole.ADMIN: [
        # Admin has all permissions
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.USER_DELETE,
        Permission.JOB_READ,
        Permission.JOB_CREATE,
        Permission.JOB_UPDATE,
        Permission.JOB_DELETE,
        Permission.APPLICATION_READ,
        Permission.APPLICATION_WRITE,
        Permission.APPLICATION_REVIEW,
        Permission.CV_READ,
        Permission.CV_WRITE,
        Permission.CV_DELETE,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.PROJECT_DELETE,
        Permission.MENTOR_READ,
        Permission.MENTOR_WRITE,
        Permission.MENTORSHIP_CREATE,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.ADMIN_DELETE,
        Permission.SYSTEM_SETTINGS,
        Permission.COMPANY_READ,
        Permission.COMPANY_WRITE,
        Permission.COMPANY_PROFILE,
    ],
}


def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User object
        permission: Permission string (e.g., "job:create")
        
    Returns:
        bool: True if user has permission
    """
    if not user or not user.role:
        return False
    
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[str]) -> bool:
    """
    Check if user has ANY of the specified permissions.
    
    Args:
        user: User object
        permissions: List of permission strings
        
    Returns:
        bool: True if user has at least one permission
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[str]) -> bool:
    """
    Check if user has ALL specified permissions.
    
    Args:
        user: User object
        permissions: List of permission strings
        
    Returns:
        bool: True if user has all permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def is_resource_owner(user: User, resource_user_id: int) -> bool:
    """
    Check if user owns the resource.
    
    Args:
        user: Current user
        resource_user_id: User ID of resource owner
        
    Returns:
        bool: True if user owns the resource
    """
    return user.id == resource_user_id


def can_access_resource(
    user: User, 
    resource_user_id: int, 
    required_permission: Optional[str] = None
) -> bool:
    """
    Check if user can access a resource (owns it or has permission).
    
    Args:
        user: Current user
        resource_user_id: User ID of resource owner
        required_permission: Optional permission needed for non-owners
        
    Returns:
        bool: True if user can access resource
    """
    # Owner can always access their resources
    if is_resource_owner(user, resource_user_id):
        return True
    
    # Admin can access anything
    if user.role == UserRole.ADMIN:
        return True
    
    # Check specific permission if provided
    if required_permission:
        return has_permission(user, required_permission)
    
    return False


def require_permission(*permissions: str):
    """
    Decorator to require specific permissions for an endpoint.
    
    Usage:
        @require_permission(Permission.JOB_CREATE)
        async def create_job(user: User = Depends(get_current_user)):
            ...
    
    Args:
        *permissions: Required permissions (user needs ALL of them)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (should be dependency-injected)
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check all permissions
            if not has_all_permissions(user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator to require ANY of the specified permissions.
    
    Usage:
        @require_any_permission(Permission.JOB_CREATE, Permission.ADMIN_WRITE)
        async def create_job(user: User = Depends(get_current_user)):
            ...
    
    Args:
        *permissions: Required permissions (user needs at least ONE)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not has_any_permission(user, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions. Need one of: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_ownership_or_permission(permission: str):
    """
    Decorator to require resource ownership OR specific permission.
    
    Usage:
        @require_ownership_or_permission(Permission.ADMIN_READ)
        async def get_cv(cv_id: int, user: User = Depends(get_current_user)):
            # Check ownership in endpoint logic
            ...
    
    Args:
        permission: Permission required if not owner
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # This decorator assumes endpoint will check ownership
            # It only verifies user has permission OR is admin
            if user.role != UserRole.ADMIN and not has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to access this resource"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RBACService:
    """Service class for RBAC operations."""
    
    @staticmethod
    def get_user_permissions(user: User) -> List[str]:
        """Get all permissions for a user."""
        return ROLE_PERMISSIONS.get(user.role, [])
    
    @staticmethod
    def can_user_perform_action(user: User, action: str) -> bool:
        """Check if user can perform an action."""
        return has_permission(user, action)
    
    @staticmethod
    def get_accessible_roles(user: User) -> List[UserRole]:
        """
        Get roles that user can manage/view.
        
        Returns:
            List of accessible roles based on user's role
        """
        if user.role == UserRole.ADMIN:
            return list(UserRole)
        elif user.role == UserRole.RECRUITER:
            return [UserRole.USER]
        elif user.role == UserRole.COMPANY:
            return [UserRole.USER, UserRole.RECRUITER]
        else:
            return [user.role]
    
    @staticmethod
    def can_manage_user(manager: User, target_user: User) -> bool:
        """
        Check if manager can manage target user.
        
        Args:
            manager: User attempting to manage
            target_user: User being managed
            
        Returns:
            bool: True if manager can manage target user
        """
        # Users can manage themselves
        if manager.id == target_user.id:
            return True
        
        # Admin can manage anyone
        if manager.role == UserRole.ADMIN:
            return True
        
        # Recruiters can manage regular users
        if manager.role == UserRole.RECRUITER and target_user.role == UserRole.USER:
            return True
        
        # Company can manage recruiters and users
        if manager.role == UserRole.COMPANY and target_user.role in [UserRole.RECRUITER, UserRole.USER]:
            return True
        
        return False
    
    @staticmethod
    def get_role_hierarchy_level(role: UserRole) -> int:
        """
        Get numeric hierarchy level for role.
        Higher number = more privileges.
        """
        hierarchy = {
            UserRole.USER: 1,
            UserRole.MENTOR: 2,
            UserRole.RECRUITER: 3,
            UserRole.COMPANY: 4,
            UserRole.ADMIN: 5,
        }
        return hierarchy.get(role, 0)


# Convenience instances
rbac_service = RBACService()
