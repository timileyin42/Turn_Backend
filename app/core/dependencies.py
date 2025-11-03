"""
FastAPI dependencies for authentication, database access, and common utilities.
"""
from typing import Optional, List, AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.services.auth_service import auth_service
from app.database.user_models import User, UserRole

# Use OAuth2PasswordBearer for OpenAPI schema integration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency that provides async session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from OAuth2 password bearer
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user = await auth_service.get_current_user(db, token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user with active check).
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: Current active user
    """
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        token: Optional JWT token from OAuth2 password bearer
        db: Database session
        
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    if not token:
        return None
    
    try:
        user = await auth_service.get_current_user(db, token)
        return user if user and user.is_active else None
    except:
        return None


def require_roles(*allowed_roles: UserRole):
    """
    Create a dependency that requires specific user roles.
    
    Args:
        *allowed_roles: List of allowed UserRole enums
        
    Returns:
        Dependency function that checks user roles
        
    Example:
        @app.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = [role.value for role in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(role_names)}. Your role: {current_user.role.value}"
            )
        return current_user
    
    return role_checker


def require_any_role(*allowed_roles: UserRole):
    """
    Alternative syntax for require_roles - checks if user has ANY of the specified roles.
    
    Args:
        *allowed_roles: List of allowed UserRole enums
        
    Returns:
        Dependency function that checks user roles
    """
    return require_roles(*allowed_roles)


def require_all_roles(*required_roles: UserRole):
    """
    Requires user to have ALL specified roles (for multi-role scenarios).
    Note: Current implementation supports single role per user, but prepared for future.
    
    Args:
        *required_roles: List of required UserRole enums
        
    Returns:
        Dependency function that checks user roles
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # For now, just check if user has at least one of the roles
        # In future, if implementing multi-role support, check all roles
        if current_user.role not in required_roles:
            role_names = [role.value for role in required_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. You must have all of these roles: {', '.join(role_names)}"
            )
        return current_user
    
    return role_checker


# Pre-defined role dependencies for convenience
require_admin = require_roles(UserRole.ADMIN)
require_recruiter = require_roles(UserRole.RECRUITER, UserRole.ADMIN)
require_company = require_roles(UserRole.COMPANY, UserRole.ADMIN)
require_mentor = require_roles(UserRole.MENTOR, UserRole.ADMIN)
require_user = require_roles(UserRole.USER, UserRole.MENTOR, UserRole.RECRUITER, UserRole.COMPANY, UserRole.ADMIN)

# Specific permission combinations
require_recruiter_or_company = require_roles(UserRole.RECRUITER, UserRole.COMPANY, UserRole.ADMIN)
require_mentor_or_admin = require_roles(UserRole.MENTOR, UserRole.ADMIN)