"""
Security utilities for authentication and authorization.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        subject: Token subject (usually user ID or username)
        expires_delta: Custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        TokenData: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        username: str = payload.get("sub")
        if username is None:
            return None
            
        exp = payload.get("exp")
        exp_datetime = None
        if exp:
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            
        return TokenData(
            username=username,
            exp=exp_datetime
        )
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using bcrypt.
    
    Truncates password to 72 bytes before verification to match bcrypt's behavior.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Truncate to 72 bytes for bcrypt compatibility
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # bcrypt.checkpw requires bytes for both arguments
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password with bcrypt, automatically handling length limits.
    
    bcrypt has a hard limit of 72 bytes. This function ensures the password
    is properly truncated before hashing.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password (as string, not bytes)
    """
    try:
        # Pre-truncate password to 72 bytes for bcrypt compatibility
        password_bytes = password.encode('utf-8')
        
        if len(password_bytes) > 72:
            # Truncate to exactly 72 bytes
            password_bytes = password_bytes[:72]
            logger.warning(f"Password truncated to {len(password_bytes)} bytes for bcrypt")
        
        # Generate salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string (decode from bytes)
        return hashed.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError(f"Failed to hash password: {str(e)}")


def create_refresh_token(subject: Union[str, Any]) -> str:
    """
    Create a refresh token with longer expiration.
    
    Args:
        subject: Token subject
        
    Returns:
        str: Encoded refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days for refresh
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt