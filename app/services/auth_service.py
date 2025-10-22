"""
Authentication service for user registration, login, and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.database.user_models import User
from app.services.email_service import email_service
from app.services.otp_service import otp_service
from app.schemas.user_schemas import (
    UserCreate, LoginRequest, UserResponse, TokenResponse,
    RefreshTokenRequest, PasswordResetRequest, ChangePasswordRequest
)


class AuthenticationService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def register_user(
        self, 
        db: AsyncSession, 
        user_data: UserCreate
    ) -> UserResponse:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Created user response
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user exists
        existing_user = await self._get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Check username uniqueness
        existing_username = await self._get_user_by_username(db, user_data.username)
        if existing_username:
            raise ValueError("Username already taken")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
            is_active=True,
            email_verified=True,  # Auto-verify for now to save costs
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Send welcome email to new user
        try:
            await email_service.send_welcome_email(
                email=db_user.email,
                name=f"{db_user.first_name} {db_user.last_name}"
            )
            print(f"✅ Welcome email sent successfully to: {db_user.email}")
        except Exception as e:
            # Log error but don't fail registration
            print(f"⚠️ Failed to send welcome email to {db_user.email}: {e}")
            # Email failure should not block user registration
        
        return UserResponse.model_validate(db_user)
    
    async def authenticate_user(
        self, 
        db: AsyncSession, 
        login_data: LoginRequest
    ) -> Optional[User]:
        """
        Authenticate user with email/username and password.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            User if authentication successful, None otherwise
        """
        # Try to find user by email or username
        user = await self._get_user_by_email(db, login_data.email_or_username)
        if not user:
            user = await self._get_user_by_username(db, login_data.email_or_username)
        
        if not user:
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise ValueError("User account is deactivated")
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
    
    async def login_user(
        self, 
        db: AsyncSession, 
        login_data: LoginRequest
    ) -> TokenResponse:
        """
        Login user and generate JWT tokens.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            JWT tokens response
            
        Raises:
            ValueError: If authentication fails
        """
        user = await self.authenticate_user(db, login_data)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Generate tokens
        access_token = self._create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        refresh_token = self._create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def refresh_access_token(
        self, 
        db: AsyncSession, 
        refresh_data: RefreshTokenRequest
    ) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            db: Database session
            refresh_data: Refresh token request
            
        Returns:
            New JWT tokens
            
        Raises:
            ValueError: If refresh token is invalid
        """
        try:
            payload = jwt.decode(
                refresh_data.refresh_token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise ValueError("Invalid refresh token")
        except JWTError:
            raise ValueError("Invalid refresh token")
        
        # Get user
        user = await self._get_user_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Generate new tokens
        access_token = self._create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        new_refresh_token = self._create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT access token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            return None
    
    async def get_current_user(
        self, 
        db: AsyncSession, 
        token: str
    ) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            Current user if token is valid
        """
        payload = await self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await self._get_user_by_id(db, int(user_id))
    
    async def change_password(
        self, 
        db: AsyncSession, 
        user_id: int,
        password_data: ChangePasswordRequest
    ) -> bool:
        """
        Change user password.
        
        Args:
            db: Database session
            user_id: User ID
            password_data: Password change request
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If current password is incorrect
        """
        user = await self._get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        return True
    
    async def request_password_reset(
        self, 
        db: AsyncSession, 
        reset_data: PasswordResetRequest
    ) -> str:
        """
        Generate password reset token.
        
        Args:
            db: Database session
            reset_data: Password reset request
            
        Returns:
            Password reset token
            
        Raises:
            ValueError: If user not found
        """
        user = await self._get_user_by_email(db, reset_data.email)
        if not user:
            raise ValueError("User with this email not found")
        
        # Generate reset token (expires in 1 hour)
        reset_token = self._create_reset_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Send password reset email
        try:
            await email_service.send_password_reset_email(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                reset_token=reset_token
            )
        except Exception as e:
            # Log error but don't fail the reset request
            print(f"Failed to send password reset email: {e}")
        
        return reset_token
    
    async def verify_email(
        self, 
        db: AsyncSession, 
        token: str
    ) -> bool:
        """
        Verify user email with verification token.
        
        Args:
            db: Database session
            token: Email verification token
            
        Returns:
            True if email verified successfully
        """
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            user_id = payload.get("sub")
            if not user_id:
                return False
        except JWTError:
            return False
        
        user = await self._get_user_by_id(db, int(user_id))
        if not user:
            return False
        
        user.email_verified = True
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        return True
    
    async def resend_verification_email(
        self, 
        db: AsyncSession, 
        email: str
    ) -> bool:
        """
        Resend email verification.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            True if verification email sent successfully
            
        Raises:
            ValueError: If user not found or already verified
        """
        user = await self._get_user_by_email(db, email)
        if not user:
            raise ValueError("User with this email not found")
        
        if user.email_verified:
            raise ValueError("Email already verified")
        
        # Generate verification token
        verification_token = self._create_verification_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Send verification email
        try:
            await email_service.send_verification_email(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                verification_token=verification_token
            )
            return True
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False
    
    async def send_login_otp(
        self, 
        db: AsyncSession, 
        email: str
    ) -> bool:
        """
        Send OTP for passwordless login.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            True if OTP sent successfully
            
        Raises:
            ValueError: If user not found
        """
        user = await self._get_user_by_email(db, email)
        if not user:
            raise ValueError("User with this email not found")
        
        try:
            await otp_service.send_email_otp(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                purpose="login"
            )
            return True
        except Exception as e:
            print(f"Failed to send login OTP: {e}")
            return False
    
    async def verify_login_otp(
        self, 
        db: AsyncSession, 
        email: str, 
        otp: str
    ) -> Optional[TokenResponse]:
        """
        Verify OTP and return login tokens.
        
        Args:
            db: Database session
            email: User email
            otp: OTP code to verify
            
        Returns:
            Token response if OTP is valid, None otherwise
        """
        user = await self._get_user_by_email(db, email)
        if not user:
            return None
        
        if not otp_service.verify_otp(email, otp, "login"):
            return None
        
        # Create tokens
        access_token = self._create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = self._create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
    
    async def send_password_reset_otp(
        self, 
        db: AsyncSession, 
        email: str
    ) -> bool:
        """
        Send OTP for password reset.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            True if OTP sent successfully
            
        Raises:
            ValueError: If user not found
        """
        user = await self._get_user_by_email(db, email)
        if not user:
            raise ValueError("User with this email not found")
        
        try:
            await otp_service.send_email_otp(
                email=user.email,
                name=f"{user.first_name} {user.last_name}",
                purpose="reset"
            )
            return True
        except Exception as e:
            print(f"Failed to send password reset OTP: {e}")
            return False
    
    async def verify_password_reset_otp(
        self, 
        db: AsyncSession, 
        email: str, 
        otp: str, 
        new_password: str
    ) -> bool:
        """
        Verify OTP and reset password.
        
        Args:
            db: Database session
            email: User email
            otp: OTP code to verify
            new_password: New password to set
            
        Returns:
            True if password reset successfully
        """
        user = await self._get_user_by_email(db, email)
        if not user:
            return False
        
        if not otp_service.verify_otp(email, otp, "reset"):
            return False
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        await db.commit()
        return True
    
    def _create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def _create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token (expires in 7 days)."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def _create_reset_token(self, data: Dict[str, Any]) -> str:
        """Create password reset token (expires in 1 hour)."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update({"exp": expire, "type": "reset"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    def _create_verification_token(self, data: Dict[str, Any]) -> str:
        """Create email verification token (expires in 24 hours)."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode.update({"exp": expire, "type": "verification"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    async def _get_user_by_email(
        self, 
        db: AsyncSession, 
        email: str
    ) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_username(
        self, 
        db: AsyncSession, 
        username: str
    ) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[User]:
        """Get user by ID with profile loaded."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# Global authentication service instance
auth_service = AuthenticationService()