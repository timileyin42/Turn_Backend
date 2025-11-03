"""
User-related Pydantic v2 schemas with from_attributes=True.
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

from app.database.user_models import UserRole, SkillLevel


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user. Role is always set to USER by default."""
    password: str = Field(..., min_length=8, max_length=72, description="Password (max 72 characters for bcrypt compatibility)")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's last name")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate and truncate password to 72 bytes for bcrypt compatibility."""
        import logging
        logger = logging.getLogger(__name__)
        
        password_bytes = v.encode('utf-8')
        logger.info(f"Password validation - Length: {len(v)} chars, {len(password_bytes)} bytes")
        
        # bcrypt has a hard limit of 72 bytes
        if len(password_bytes) > 72:
            # Truncate to 72 bytes, ensuring we don't cut in the middle of a multi-byte character
            truncated_bytes = password_bytes[:72]
            # Decode and ignore any incomplete characters at the end
            truncated = truncated_bytes.decode('utf-8', errors='ignore')
            # Re-encode to verify final byte count
            final_bytes = truncated.encode('utf-8')
            logger.warning(f"Password truncated from {len(password_bytes)} to {len(final_bytes)} bytes")
            return truncated
        
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response data."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    profile: Optional["UserProfile"] = None  # Include user profile


class UserProfile(BaseModel):
    """User profile response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    current_job_title: Optional[str] = None
    company: Optional[str] = None
    years_of_experience: Optional[int] = None
    career_goals: Optional[str] = None
    target_industries: Optional[List[str]] = None
    preferred_work_mode: Optional[str] = None
    learning_style: Optional[str] = None
    preferred_methodologies: Optional[List[str]] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    is_complete: bool
    completion_percentage: int
    created_at: datetime
    updated_at: datetime
    
    @field_validator('target_industries', 'preferred_methodologies', mode='before')
    @classmethod
    def parse_json_lists(cls, v):
        """Convert JSON string to list if needed."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v


class ProfileCreate(BaseModel):
    """Schema for creating user profile."""
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = None
    current_job_title: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)
    career_goals: Optional[str] = None
    target_industries: Optional[List[str]] = None
    preferred_work_mode: Optional[str] = Field(None, pattern="^(remote|onsite|hybrid)$")
    learning_style: Optional[str] = Field(None, pattern="^(visual|auditory|kinesthetic)$")
    preferred_methodologies: Optional[List[str]] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)


class ProfileUpdate(ProfileCreate):
    """Schema for updating user profile."""
    pass


class UserSkillBase(BaseModel):
    """Base schema for user skills."""
    skill_name: str = Field(..., min_length=1, max_length=50)
    skill_category: str = Field(..., pattern="^(technical|soft|methodology)$")
    proficiency_level: SkillLevel = SkillLevel.BEGINNER


class UserSkillCreate(UserSkillBase):
    """Schema for creating user skill."""
    pass


class UserSkillUpdate(BaseModel):
    """Schema for updating user skill."""
    skill_name: Optional[str] = Field(None, min_length=1, max_length=50)
    skill_category: Optional[str] = Field(None, pattern="^(technical|soft|methodology)$")
    proficiency_level: Optional[SkillLevel] = None


class UserSkillResponse(UserSkillBase):
    """Schema for user skill response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_verified: bool
    verified_by_project: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MentorProfileBase(BaseModel):
    """Base schema for mentor profile."""
    certifications: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    mentoring_experience_years: Optional[int] = Field(None, ge=0, le=50)
    is_available: bool = True
    max_mentees: int = Field(5, ge=1, le=20)
    hourly_rate: Optional[int] = Field(None, ge=0)  # in cents
    preferred_communication: Optional[str] = Field(None, pattern="^(video|text|both)$")
    available_time_slots: Optional[List[str]] = None
    mentor_bio: Optional[str] = None
    approach_description: Optional[str] = None


class MentorProfileCreate(MentorProfileBase):
    """Schema for creating mentor profile."""
    pass


class MentorProfileUpdate(BaseModel):
    """Schema for updating mentor profile."""
    certifications: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    mentoring_experience_years: Optional[int] = Field(None, ge=0, le=50)
    is_available: Optional[bool] = None
    max_mentees: Optional[int] = Field(None, ge=1, le=20)
    hourly_rate: Optional[int] = Field(None, ge=0)
    preferred_communication: Optional[str] = Field(None, pattern="^(video|text|both)$")
    available_time_slots: Optional[List[str]] = None
    mentor_bio: Optional[str] = None
    approach_description: Optional[str] = None


class MentorProfileResponse(MentorProfileBase):
    """Schema for mentor profile response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    current_mentees_count: int
    average_rating: Optional[float] = None
    total_reviews: int
    is_approved: bool
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserWithProfile(UserResponse):
    """User response with profile information."""
    profile: Optional[UserProfile] = None
    mentor_profile: Optional[MentorProfileResponse] = None


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


# Authentication schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=72, description="New password (max 72 characters)")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate and truncate password to 72 bytes for bcrypt compatibility."""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            truncated_bytes = password_bytes[:72]
            return truncated_bytes.decode('utf-8', errors='ignore')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=72, description="New password (max 72 characters)")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate and truncate password to 72 bytes for bcrypt compatibility."""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            truncated_bytes = password_bytes[:72]
            return truncated_bytes.decode('utf-8', errors='ignore')
        return v


class UserPreferencesUpdate(BaseModel):
    """User preferences update schema."""
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    notification_settings: Optional[Dict[str, bool]] = None
    privacy_settings: Optional[Dict[str, bool]] = None
    theme: Optional[str] = Field(None, pattern="^(light|dark|auto)$")


class UserSearchRequest(BaseModel):
    """User search request schema."""
    query: Optional[str] = Field(None, max_length=100)
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = Field(None, pattern="^(junior|mid|senior|lead)$")
    location: Optional[str] = Field(None, max_length=100)
    availability: Optional[bool] = None
    mentor_status: Optional[bool] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


# Aliases for backwards compatibility
PasswordChangeRequest = ChangePasswordRequest

# Update forward references for nested models
UserResponse.model_rebuild()
UserProfileUpdate = ProfileUpdate