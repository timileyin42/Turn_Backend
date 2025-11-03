"""
Community forum and mentorship database models.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User


class ForumPost(Base):
    """Community forum posts."""
    
    __tablename__ = "forum_posts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("forum_categories.id"), nullable=False)
    
    # Post content
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)
    
    # Post metadata
    post_type: Mapped[str] = mapped_column(String(20), default="discussion", nullable=False)  # discussion, question, showcase, announcement
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of tags
    
    # Engagement metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status and moderation
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Question-specific fields
    is_answered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepted_answer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_comments.id", use_alter=True, name="fk_forum_post_accepted_answer"), nullable=True)
    
    # SEO and search
    slug: Mapped[Optional[str]] = mapped_column(String(350), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="forum_posts")
    category: Mapped["ForumCategory"] = relationship("ForumCategory", back_populates="posts")
    comments: Mapped[List["ForumComment"]] = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan", foreign_keys="ForumComment.post_id")
    likes: Mapped[List["ForumLike"]] = relationship("ForumLike", back_populates="post", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_forum_posts_author_id', 'author_id'),
        Index('idx_forum_posts_category_id', 'category_id'), 
        Index('idx_forum_posts_post_type', 'post_type'),
        Index('idx_forum_posts_is_pinned', 'is_pinned'),
        Index('idx_forum_posts_is_locked', 'is_locked'),
        Index('idx_forum_posts_is_featured', 'is_featured'),
        Index('idx_forum_posts_is_deleted', 'is_deleted'),
        Index('idx_forum_posts_is_answered', 'is_answered'),
        Index('idx_forum_posts_view_count', 'view_count'),
        Index('idx_forum_posts_like_count', 'like_count'),
        Index('idx_forum_posts_comment_count', 'comment_count'),
        Index('idx_forum_posts_created_at', 'created_at'),
        Index('idx_forum_posts_updated_at', 'updated_at'),
        Index('idx_forum_posts_last_activity_at', 'last_activity_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_forum_posts_category_active', 'category_id', 'is_deleted'),
        Index('idx_forum_posts_category_type', 'category_id', 'post_type'),
        Index('idx_forum_posts_author_active', 'author_id', 'is_deleted'),
        Index('idx_forum_posts_featured_active', 'is_featured', 'is_deleted'),
        Index('idx_forum_posts_pinned_active', 'is_pinned', 'is_deleted'),
        Index('idx_forum_posts_type_answered', 'post_type', 'is_answered'),
        Index('idx_forum_posts_category_created', 'category_id', 'created_at'),
        Index('idx_forum_posts_category_activity', 'category_id', 'last_activity_at'),
        
        {"sqlite_autoincrement": True}
    )


class ForumCategory(Base):
    """Forum categories for organizing posts."""
    
    __tablename__ = "forum_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Category organization
    parent_category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_categories.id", use_alter=True, name="fk_forum_category_parent"), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Category metadata
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#007bff", nullable=False)
    
    # Statistics
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Permissions and moderation
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_anonymous_posts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    posts: Mapped[List["ForumPost"]] = relationship("ForumPost", back_populates="category")
    subcategories: Mapped[List["ForumCategory"]] = relationship("ForumCategory", remote_side=[id])

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_forum_categories_name', 'name'),
        Index('idx_forum_categories_parent_category_id', 'parent_category_id'),
        Index('idx_forum_categories_display_order', 'display_order'),
        Index('idx_forum_categories_is_public', 'is_public'),
        Index('idx_forum_categories_is_active', 'is_active'),
        Index('idx_forum_categories_post_count', 'post_count'),
        Index('idx_forum_categories_created_at', 'created_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_forum_categories_public_active', 'is_public', 'is_active'),
        Index('idx_forum_categories_parent_order', 'parent_category_id', 'display_order'),
        Index('idx_forum_categories_active_order', 'is_active', 'display_order'),
        
        {"sqlite_autoincrement": True}
    )


class ForumComment(Base):
    """Comments on forum posts."""
    
    __tablename__ = "forum_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("forum_comments.id", use_alter=True, name="fk_forum_comment_parent"), nullable=True)
    
    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)
    
    # Engagement
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status and moderation
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_accepted_answer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="comments", foreign_keys=[post_id])
    author: Mapped["User"] = relationship("User", back_populates="forum_comments")
    replies: Mapped[List["ForumComment"]] = relationship("ForumComment", remote_side=[parent_comment_id])
    likes: Mapped[List["ForumCommentLike"]] = relationship("ForumCommentLike", back_populates="comment", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_forum_comments_post_id', 'post_id'),
        Index('idx_forum_comments_author_id', 'author_id'),
        Index('idx_forum_comments_parent_comment_id', 'parent_comment_id'),
        Index('idx_forum_comments_is_deleted', 'is_deleted'),
        Index('idx_forum_comments_is_accepted_answer', 'is_accepted_answer'),
        Index('idx_forum_comments_like_count', 'like_count'),
        Index('idx_forum_comments_created_at', 'created_at'),
        Index('idx_forum_comments_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_forum_comments_post_active', 'post_id', 'is_deleted'),
        Index('idx_forum_comments_post_created', 'post_id', 'created_at'),
        Index('idx_forum_comments_author_active', 'author_id', 'is_deleted'),
        Index('idx_forum_comments_parent_active', 'parent_comment_id', 'is_deleted'),
        Index('idx_forum_comments_post_accepted', 'post_id', 'is_accepted_answer'),
        
        {"sqlite_autoincrement": True}
    )


class ForumLike(Base):
    """Likes on forum posts."""
    
    __tablename__ = "forum_likes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="likes")
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_forum_likes_post_id', 'post_id'),
        Index('idx_forum_likes_user_id', 'user_id'),
        Index('idx_forum_likes_created_at', 'created_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_forum_likes_post_user', 'post_id', 'user_id'),  # Unique check
        Index('idx_forum_likes_user_created', 'user_id', 'created_at'),
        
        {"sqlite_autoincrement": True}
    )


class ForumCommentLike(Base):
    """Likes on forum comments."""
    
    __tablename__ = "forum_comment_likes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("forum_comments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    comment: Mapped["ForumComment"] = relationship("ForumComment", back_populates="likes")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_forum_comment_likes_comment_id', 'comment_id'),
        Index('idx_forum_comment_likes_user_id', 'user_id'),
        Index('idx_forum_comment_likes_created_at', 'created_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_forum_comment_likes_comment_user', 'comment_id', 'user_id'),  # Unique check
        Index('idx_forum_comment_likes_user_created', 'user_id', 'created_at'),
        
        {"sqlite_autoincrement": True}
    )


class Mentorship(Base):
    """Mentorship relationships between users."""
    
    __tablename__ = "mentorships"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Mentorship details
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, active, completed, cancelled
    mentorship_type: Mapped[str] = mapped_column(String(20), default="general", nullable=False)  # general, project_specific, career_guidance
    
    # Goals and objectives
    goals: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of goals
    focus_areas: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of focus areas
    
    # Schedule and commitment
    meeting_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # weekly, biweekly, monthly
    session_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_sessions_planned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Communication preferences
    communication_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # video, voice, text, mixed
    
    # Progress tracking
    progress_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    milestones_achieved: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    
    # Feedback and rating
    mentor_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 from mentee
    mentee_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 from mentor
    mentor_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mentee_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    mentor: Mapped["User"] = relationship("User", foreign_keys=[mentor_id], back_populates="mentorships_as_mentor")
    mentee: Mapped["User"] = relationship("User", foreign_keys=[mentee_id], back_populates="mentorships_as_mentee")
    sessions: Mapped[List["MentorshipSession"]] = relationship("MentorshipSession", back_populates="mentorship", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_mentorships_mentor_id', 'mentor_id'),
        Index('idx_mentorships_mentee_id', 'mentee_id'),
        Index('idx_mentorships_status', 'status'),
        Index('idx_mentorships_mentorship_type', 'mentorship_type'),
        Index('idx_mentorships_sessions_completed', 'sessions_completed'),
        Index('idx_mentorships_requested_at', 'requested_at'),
        Index('idx_mentorships_accepted_at', 'accepted_at'),
        Index('idx_mentorships_completed_at', 'completed_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_mentorships_mentor_status', 'mentor_id', 'status'),
        Index('idx_mentorships_mentee_status', 'mentee_id', 'status'),
        Index('idx_mentorships_status_type', 'status', 'mentorship_type'),
        Index('idx_mentorships_mentor_requested', 'mentor_id', 'requested_at'),
        Index('idx_mentorships_mentee_requested', 'mentee_id', 'requested_at'),
        Index('idx_mentorships_active_progress', 'status', 'sessions_completed'),
        
        {"sqlite_autoincrement": True}
    )


class MentorshipSession(Base):
    """Individual mentorship sessions."""
    
    __tablename__ = "mentorship_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mentorship_id: Mapped[int] = mapped_column(ForeignKey("mentorships.id", ondelete="CASCADE"), nullable=False)
    
    # Session planning
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    agenda: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Session execution
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)  # scheduled, completed, cancelled, no_show
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Session content
    topics_covered: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    key_takeaways: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array
    
    # Session notes
    mentor_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mentee_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shared_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resources shared
    resources_shared: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of resources
    
    # Session feedback
    mentor_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    mentee_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    session_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Follow-up
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_session_suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    mentorship: Mapped["Mentorship"] = relationship("Mentorship", back_populates="sessions")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_mentorship_sessions_mentorship_id', 'mentorship_id'),
        Index('idx_mentorship_sessions_scheduled_date', 'scheduled_date'),
        Index('idx_mentorship_sessions_status', 'status'),
        Index('idx_mentorship_sessions_actual_start_time', 'actual_start_time'),
        Index('idx_mentorship_sessions_created_at', 'created_at'),
        Index('idx_mentorship_sessions_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_mentorship_sessions_mentorship_status', 'mentorship_id', 'status'),
        Index('idx_mentorship_sessions_mentorship_scheduled', 'mentorship_id', 'scheduled_date'),
        Index('idx_mentorship_sessions_status_scheduled', 'status', 'scheduled_date'),
        Index('idx_mentorship_sessions_mentorship_created', 'mentorship_id', 'created_at'),
        
        {"sqlite_autoincrement": True}
    )


class MentorshipRequest(Base):
    """Requests for mentorship."""
    
    __tablename__ = "mentorship_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    mentee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mentor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Null for open requests
    
    # Request details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Request specifics
    mentorship_type: Mapped[str] = mapped_column(String(20), default="general", nullable=False)
    focus_areas: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array
    goals: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array
    
    # Preferences
    preferred_duration: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # 1_month, 3_months, 6_months, ongoing
    preferred_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    preferred_communication: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Experience and background
    current_experience_level: Mapped[str] = mapped_column(String(20), nullable=False)
    background_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)  # open, matched, closed, expired
    
    # Matching
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Visible to all mentors
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_mentorship_requests_mentee_id', 'mentee_id'),
        Index('idx_mentorship_requests_mentor_id', 'mentor_id'),
        Index('idx_mentorship_requests_status', 'status'),
        Index('idx_mentorship_requests_mentorship_type', 'mentorship_type'),
        Index('idx_mentorship_requests_is_public', 'is_public'),
        Index('idx_mentorship_requests_current_experience_level', 'current_experience_level'),
        Index('idx_mentorship_requests_created_at', 'created_at'),
        Index('idx_mentorship_requests_expires_at', 'expires_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_mentorship_requests_status_public', 'status', 'is_public'),
        Index('idx_mentorship_requests_type_experience', 'mentorship_type', 'current_experience_level'),
        Index('idx_mentorship_requests_mentee_status', 'mentee_id', 'status'),
        Index('idx_mentorship_requests_public_created', 'is_public', 'created_at'),
        Index('idx_mentorship_requests_status_expires', 'status', 'expires_at'),
        Index('idx_mentorship_requests_open_public', 'status', 'is_public', 'created_at'),
        
        {"sqlite_autoincrement": True}
    )
    
    
class CommunityEvent(Base):
    """Community events and webinars."""
    
    __tablename__ = "community_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Event details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # webinar, workshop, networking, q_and_a
    
    # Event scheduling
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Event logistics
    max_attendees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    registration_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    
    # Event links
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    registration_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Content
    agenda: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of agenda items
    speakers: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of speaker info
    tags: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of tags
    
    # Engagement
    attendee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="upcoming", nullable=False)  # upcoming, live, completed, cancelled
    
    # Recording and resources
    recording_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resource_links: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of resources
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_community_events_organizer_id', 'organizer_id'),
        Index('idx_community_events_event_type', 'event_type'),
        Index('idx_community_events_start_date', 'start_date'),
        Index('idx_community_events_end_date', 'end_date'),
        Index('idx_community_events_status', 'status'),
        Index('idx_community_events_registration_required', 'registration_required'),
        Index('idx_community_events_is_free', 'is_free'),
        Index('idx_community_events_attendee_count', 'attendee_count'),
        Index('idx_community_events_created_at', 'created_at'),
        Index('idx_community_events_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_community_events_type_status', 'event_type', 'status'),
        Index('idx_community_events_status_start', 'status', 'start_date'),
        Index('idx_community_events_organizer_status', 'organizer_id', 'status'),
        Index('idx_community_events_free_status', 'is_free', 'status'),
        Index('idx_community_events_type_start', 'event_type', 'start_date'),
        Index('idx_community_events_status_created', 'status', 'created_at'),
        Index('idx_community_events_upcoming_start', 'status', 'start_date', 'is_free'),
        
        {"sqlite_autoincrement": True}
    )