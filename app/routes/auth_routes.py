"""
Authentication routes for user registration, login, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.services.auth_service import auth_service
from app.database.user_models import User
from app.schemas.user_schemas import (
    UserCreate, LoginRequest, UserResponse, TokenResponse,
    RefreshTokenRequest, PasswordChangeRequest, PasswordResetRequest
)
from app.core.rate_limiter import limiter, RateLimitTiers

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
@limiter.limit(RateLimitTiers.AUTH_REGISTER)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account."""
    try:
        return await auth_service.register_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login (OAuth2 Password Flow)",
    description="""
    Authenticate user and return JWT access and refresh tokens.
    
    **For Swagger UI:** Click "Authorize" button and enter:
    - Username: Your email address
    - Password: Your password
    
    **For API clients:** Send POST request with form data:
    - username (email or username)
    - password
    
    **Response:** JWT tokens for subsequent authenticated requests
    
    **Roles:**
    - user: Regular job seeker (default)
    - recruiter: Can post jobs
    - company: Company representative
    - mentor: Provides mentorship
    - admin: Platform administrator
    """
)
@limiter.limit(RateLimitTiers.AUTH_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user using OAuth2 password flow.
    Compatible with Swagger UI authorization and API clients.
    """
    try:
        # Convert OAuth2 form to LoginRequest
        login_data = LoginRequest(
            username=form_data.username,  # Can be email or username
            password=form_data.password
        )
        
        return await auth_service.login_user(db, login_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/login-json",
    response_model=TokenResponse,
    summary="User login (JSON format)",
    description="""
    Alternative login endpoint that accepts JSON instead of form data.
    Use this if you prefer JSON over OAuth2 password flow.
    """
)
@limiter.limit(RateLimitTiers.AUTH_LOGIN)
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user using JSON request body."""
    try:
        return await auth_service.login_user(db, login_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    try:
        return await auth_service.refresh_access_token(db, refresh_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user."""
    try:
        return UserResponse.model_validate(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post(
    "/change-password",
    summary="Change password",
    description="Change user password (requires authentication)"
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    try:
        # Change password
        success = await auth_service.change_password(db, current_user.id, password_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
        
        return {"message": "Password changed successfully"}
    
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
            detail="Password change failed"
        )


@router.post(
    "/forgot-password",
    summary="Request password reset",
    description="Send password reset token to user's email"
)
async def forgot_password(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset token."""
    try:
        reset_token = await auth_service.request_password_reset(db, reset_data)
        
        # TODO: Send email with reset token
        # For now, return success message (in production, don't reveal if email exists)
        return {
            "message": "If an account with this email exists, a password reset link has been sent"
        }
    
    except ValueError as e:
        # Don't reveal if email exists - always return success message for security
        return {
            "message": "If an account with this email exists, a password reset link has been sent"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post(
    "/verify-email",
    summary="Verify email address",
    description="Verify user's email address using verification token"
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify user's email address."""
    try:
        success = await auth_service.verify_email(db, token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        return {"message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post(
    "/send-login-otp",
    summary="Send login OTP",
    description="Send OTP for passwordless login"
)
async def send_login_otp(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Send OTP for passwordless login."""
    try:
        success = await auth_service.send_login_otp(db, email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send login OTP"
            )
        
        return {"message": "Login OTP sent successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send login OTP"
        )


@router.post(
    "/verify-login-otp",
    response_model=TokenResponse,
    summary="Verify login OTP",
    description="Verify OTP and return login tokens"
)
async def verify_login_otp(
    email: str,
    otp: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP and return login tokens."""
    try:
        token_response = await auth_service.verify_login_otp(db, email, otp)
        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        return token_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed"
        )


@router.post(
    "/send-password-reset-otp",
    summary="Send password reset OTP",
    description="Send OTP for password reset"
)
@limiter.limit(RateLimitTiers.AUTH_PASSWORD_RESET)
async def send_password_reset_otp(
    request: Request,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Send OTP for password reset."""
    try:
        success = await auth_service.send_password_reset_otp(db, email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send password reset OTP"
            )
        
        return {"message": "Password reset OTP sent successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset OTP"
        )


@router.post(
    "/reset-password-with-otp",
    summary="Reset password with OTP",
    description="Verify OTP and reset password"
)
async def reset_password_with_otp(
    email: str,
    otp: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify OTP and reset password."""
    try:
        success = await auth_service.verify_password_reset_otp(
            db, email, otp, new_password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        return {"message": "Password reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post(
    "/resend-verification-email",
    summary="Resend email verification",
    description="Resend verification email to user"
)
async def resend_verification_email(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Resend email verification."""
    try:
        success = await auth_service.resend_verification_email(db, email)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to send verification email"
            )
        
        return {"message": "Verification email sent successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post(
    "/logout",
    summary="User logout",
    description="Logout user (client should discard tokens)"
)
async def logout():
    """Logout user."""
    # Since we're using stateless JWT tokens, logout is handled client-side
    # In a production system, you might want to blacklist tokens in Redis
    return {"message": "Logged out successfully"}