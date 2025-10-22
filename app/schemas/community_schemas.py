"""
Community forum and mentorship Pydantic v2 schemas.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# Forum Category schemas
class ForumCategoryBase(BaseModel):
    """Base forum category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, max_length=100)
    parent_category_id: Optional[int] = Field(None, gt=0)
    display_order: int = Field(0, ge=0)
    icon_url: Optional[str] = Field(None, max_length=500)
    color: str = Field("#007bff", max_length=20)
    is_public: bool = True
    allow_anonymous_posts: bool = False
    requires_approval: bool = False
    is_active: bool = True


class ForumCategoryCreate(ForumCategoryBase):
    """Schema for creating forum category."""
    pass


class ForumCategoryUpdate(BaseModel):
    """Schema for updating forum category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category_id: Optional[int] = Field(None, gt=0)
    display_order: Optional[int] = Field(None, ge=0)
    icon_url: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=20)
    is_public: Optional[bool] = None
    allow_anonymous_posts: Optional[bool] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class ForumCategoryResponse(ForumCategoryBase):
    """Schema for forum category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    post_count: int
    created_at: datetime


# Forum Post schemas
class ForumPostBase(BaseModel):
    """Base forum post schema."""
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1)
    content_format: str = Field("markdown", pattern="^(markdown|html)$")
    post_type: str = Field("discussion", pattern="^(discussion|question|showcase|announcement)$")
    tags: Optional[List[str]] = None


class ForumPostCreate(ForumPostBase):
    """Schema for creating forum post."""
    category_id: int = Field(..., gt=0)
    slug: Optional[str] = Field(None, max_length=350)


class ForumPostUpdate(BaseModel):
    """Schema for updating forum post."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None
    content_format: Optional[str] = Field(None, pattern="^(markdown|html)$")
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None
    is_featured: Optional[bool] = None


class ForumPostResponse(ForumPostBase):
    """Schema for forum post response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    author_id: int
    category_id: int
    slug: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    is_pinned: bool
    is_locked: bool
    is_featured: bool
    is_deleted: bool
    is_answered: bool
    accepted_answer_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime


# Forum Comment schemas
class ForumCommentBase(BaseModel):
    """Base forum comment schema."""
    content: str = Field(..., min_length=1)
    content_format: str = Field("markdown", pattern="^(markdown|html)$")


class ForumCommentCreate(ForumCommentBase):
    """Schema for creating forum comment."""
    post_id: int = Field(..., gt=0)
    parent_comment_id: Optional[int] = Field(None, gt=0)


class ForumCommentUpdate(BaseModel):
    """Schema for updating forum comment."""
    content: Optional[str] = None
    content_format: Optional[str] = Field(None, pattern="^(markdown|html)$")
    is_accepted_answer: Optional[bool] = None


class ForumCommentResponse(ForumCommentBase):
    """Schema for forum comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    post_id: int
    author_id: int
    parent_comment_id: Optional[int] = None
    like_count: int
    is_deleted: bool
    is_edited: bool
    is_accepted_answer: bool
    created_at: datetime
    updated_at: datetime


# Mentorship schemas
class MentorshipBase(BaseModel):
    """Base mentorship schema."""
    mentorship_type: str = Field("general", pattern="^(general|project_specific|career_guidance)$")
    goals: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    meeting_frequency: Optional[str] = Field(None, pattern="^(weekly|biweekly|monthly)$")
    session_duration_minutes: Optional[int] = Field(None, ge=30, le=180)
    total_sessions_planned: Optional[int] = Field(None, ge=1, le=50)
    communication_method: Optional[str] = Field(None, pattern="^(video|voice|text|mixed)$")
    progress_notes: Optional[str] = None
    milestones_achieved: Optional[List[str]] = None


class MentorshipCreate(MentorshipBase):
    """Schema for creating mentorship."""
    mentor_id: int = Field(..., gt=0)


class MentorshipUpdate(BaseModel):
    """Schema for updating mentorship."""
    status: Optional[str] = Field(None, pattern="^(pending|active|completed|cancelled)$")
    goals: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None
    meeting_frequency: Optional[str] = Field(None, pattern="^(weekly|biweekly|monthly)$")
    session_duration_minutes: Optional[int] = Field(None, ge=30, le=180)
    total_sessions_planned: Optional[int] = Field(None, ge=1, le=50)
    communication_method: Optional[str] = Field(None, pattern="^(video|voice|text|mixed)$")
    progress_notes: Optional[str] = None
    milestones_achieved: Optional[List[str]] = None
    mentor_rating: Optional[int] = Field(None, ge=1, le=5)
    mentee_rating: Optional[int] = Field(None, ge=1, le=5)
    mentor_feedback: Optional[str] = None
    mentee_feedback: Optional[str] = None


class MentorshipResponse(MentorshipBase):
    """Schema for mentorship response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    mentor_id: int
    mentee_id: int
    status: str
    sessions_completed: int
    mentor_rating: Optional[int] = None
    mentee_rating: Optional[int] = None
    mentor_feedback: Optional[str] = None
    mentee_feedback: Optional[str] = None
    requested_at: datetime
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Mentorship Session schemas
class MentorshipSessionBase(BaseModel):
    """Base mentorship session schema."""
    scheduled_date: datetime
    duration_minutes: int = Field(60, ge=30, le=180)
    agenda: Optional[str] = None
    topics_covered: Optional[List[str]] = None
    key_takeaways: Optional[str] = None
    action_items: Optional[List[str]] = None
    mentor_notes: Optional[str] = None
    mentee_notes: Optional[str] = None
    shared_notes: Optional[str] = None
    resources_shared: Optional[List[Dict[str, str]]] = None
    follow_up_required: bool = False
    next_session_suggestions: Optional[str] = None


class MentorshipSessionCreate(MentorshipSessionBase):
    """Schema for creating mentorship session."""
    mentorship_id: int = Field(..., gt=0)


class MentorshipSessionUpdate(BaseModel):
    """Schema for updating mentorship session."""
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=30, le=180)
    agenda: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|no_show)$")
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    topics_covered: Optional[List[str]] = None
    key_takeaways: Optional[str] = None
    action_items: Optional[List[str]] = None
    mentor_notes: Optional[str] = None
    mentee_notes: Optional[str] = None
    shared_notes: Optional[str] = None
    resources_shared: Optional[List[Dict[str, str]]] = None
    mentor_rating: Optional[int] = Field(None, ge=1, le=5)
    mentee_rating: Optional[int] = Field(None, ge=1, le=5)
    session_feedback: Optional[str] = None
    follow_up_required: Optional[bool] = None
    next_session_suggestions: Optional[str] = None


class MentorshipSessionResponse(MentorshipSessionBase):
    """Schema for mentorship session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    mentorship_id: int
    status: str
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    mentor_rating: Optional[int] = None
    mentee_rating: Optional[int] = None
    session_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Mentorship Request schemas
class MentorshipRequestBase(BaseModel):
    """Base mentorship request schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    mentorship_type: str = Field("general", pattern="^(general|project_specific|career_guidance)$")
    focus_areas: List[str] = Field(..., min_length=1)
    goals: List[str] = Field(..., min_length=1)
    preferred_duration: Optional[str] = Field(None, pattern="^(1_month|3_months|6_months|ongoing)$")
    preferred_frequency: Optional[str] = Field(None, pattern="^(weekly|biweekly|monthly)$")
    preferred_communication: Optional[str] = Field(None, pattern="^(video|voice|text|mixed)$")
    current_experience_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    background_info: Optional[str] = None
    is_public: bool = True


class MentorshipRequestCreate(MentorshipRequestBase):
    """Schema for creating mentorship request."""
    mentor_id: Optional[int] = Field(None, gt=0)  # Null for open requests
    expires_at: Optional[datetime] = None


class MentorshipRequestUpdate(BaseModel):
    """Schema for updating mentorship request."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    preferred_duration: Optional[str] = Field(None, pattern="^(1_month|3_months|6_months|ongoing)$")
    preferred_frequency: Optional[str] = Field(None, pattern="^(weekly|biweekly|monthly)$")
    preferred_communication: Optional[str] = Field(None, pattern="^(video|voice|text|mixed)$")
    background_info: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|matched|closed|expired)$")
    is_public: Optional[bool] = None
    expires_at: Optional[datetime] = None


class MentorshipRequestResponse(MentorshipRequestBase):
    """Schema for mentorship request response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    mentee_id: int
    mentor_id: Optional[int] = None
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None


# Community Event schemas
class CommunityEventBase(BaseModel):
    """Base community event schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    event_type: str = Field(..., pattern="^(webinar|workshop|networking|q_and_a)$")
    start_date: datetime
    end_date: datetime
    timezone: str = Field(..., max_length=50)
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_required: bool = True
    is_free: bool = True
    price: Optional[int] = Field(None, ge=0)  # in cents
    meeting_url: Optional[str] = Field(None, max_length=500)
    registration_url: Optional[str] = Field(None, max_length=500)
    agenda: Optional[List[Dict[str, Any]]] = None
    speakers: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None


class CommunityEventCreate(CommunityEventBase):
    """Schema for creating community event."""
    pass


class CommunityEventUpdate(BaseModel):
    """Schema for updating community event."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    max_attendees: Optional[int] = Field(None, ge=1)
    registration_required: Optional[bool] = None
    is_free: Optional[bool] = None
    price: Optional[int] = Field(None, ge=0)
    meeting_url: Optional[str] = Field(None, max_length=500)
    registration_url: Optional[str] = Field(None, max_length=500)
    agenda: Optional[List[Dict[str, Any]]] = None
    speakers: Optional[List[Dict[str, str]]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(upcoming|live|completed|cancelled)$")
    recording_url: Optional[str] = Field(None, max_length=500)
    resource_links: Optional[List[Dict[str, str]]] = None


class CommunityEventResponse(CommunityEventBase):
    """Schema for community event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organizer_id: int
    attendee_count: int
    status: str
    recording_url: Optional[str] = None
    resource_links: Optional[List[Dict[str, str]]] = None
    created_at: datetime
    updated_at: datetime


# Complex responses with relationships
class ForumPostWithComments(ForumPostResponse):
    """Forum post with comments."""
    comments: List[ForumCommentResponse] = []
    author_username: Optional[str] = None
    category_name: Optional[str] = None


class ForumCommentWithReplies(ForumCommentResponse):
    """Forum comment with replies."""
    replies: List[ForumCommentResponse] = []
    author_username: Optional[str] = None


class MentorshipWithSessions(MentorshipResponse):
    """Mentorship with sessions."""
    sessions: List[MentorshipSessionResponse] = []
    mentor_username: Optional[str] = None
    mentee_username: Optional[str] = None


# List responses
class ForumPostListResponse(BaseModel):
    """Paginated forum post list response."""
    posts: List[ForumPostResponse]
    total: int
    page: int
    size: int
    pages: int


class ForumCategoryListResponse(BaseModel):
    """Forum category list response."""
    categories: List[ForumCategoryResponse]


class MentorshipListResponse(BaseModel):
    """Paginated mentorship list response."""
    mentorships: List[MentorshipResponse]
    total: int
    page: int
    size: int
    pages: int


class CommunityEventListResponse(BaseModel):
    """Paginated community event list response."""
    events: List[CommunityEventResponse]
    total: int
    page: int
    size: int
    pages: int


# Search and filter schemas
class ForumSearchRequest(BaseModel):
    """Search request for forum posts."""
    query: Optional[str] = None
    category_id: Optional[int] = Field(None, gt=0)
    post_type: Optional[str] = Field(None, pattern="^(discussion|question|showcase|announcement)$")
    tags: Optional[List[str]] = None
    author_id: Optional[int] = Field(None, gt=0)
    is_answered: Optional[bool] = None  # For questions
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class MentorSearchRequest(BaseModel):
    """Search request for mentors."""
    specializations: Optional[List[str]] = None
    industry_experience: Optional[List[str]] = None
    certification_focus: Optional[List[str]] = None
    availability: Optional[bool] = None
    max_rate: Optional[int] = Field(None, ge=0)  # in cents per hour
    communication_preference: Optional[str] = Field(None, pattern="^(video|text|both)$")
    rating_min: Optional[float] = Field(None, ge=0.0, le=5.0)


# Like schemas
class ForumLikeResponse(BaseModel):
    """Schema for forum like response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    post_id: int
    user_id: int
    created_at: datetime


class ForumCommentLikeResponse(BaseModel):
    """Schema for forum comment like response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    comment_id: int
    user_id: int
    created_at: datetime