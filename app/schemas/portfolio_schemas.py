"""
Portfolio and achievement Pydantic v2 schemas.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# Portfolio schemas
class PortfolioBase(BaseModel):
    """Base portfolio schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    theme: str = Field("professional", max_length=20)
    is_public: bool = False
    is_default: bool = False
    public_url_slug: Optional[str] = Field(None, min_length=3, max_length=100)
    sections_order: Optional[List[str]] = None
    custom_sections: Optional[List[Dict[str, Any]]] = None
    color_scheme: str = Field("blue", max_length=20)
    font_style: str = Field("professional", max_length=30)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)


class PortfolioCreate(PortfolioBase):
    """Schema for creating portfolio."""
    logo_url: Optional[str] = Field(None, max_length=500)


class PortfolioUpdate(BaseModel):
    """Schema for updating portfolio."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    theme: Optional[str] = Field(None, max_length=20)
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None
    public_url_slug: Optional[str] = Field(None, min_length=3, max_length=100)
    sections_order: Optional[List[str]] = None
    custom_sections: Optional[List[Dict[str, Any]]] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    color_scheme: Optional[str] = Field(None, max_length=20)
    font_style: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    logo_url: Optional[str] = None
    last_exported_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
    view_count: int
    share_count: int
    created_at: datetime
    updated_at: datetime


# Portfolio Item schemas
class PortfolioItemBase(BaseModel):
    """Base portfolio item schema."""
    title: str = Field(..., min_length=1, max_length=200)
    item_type: str = Field(..., pattern="^(project|certificate|skill|achievement|artifact)$")
    description: str = Field(..., min_length=1)
    content: Optional[str] = None
    content_format: str = Field("markdown", pattern="^(markdown|html|json)$")
    featured_image_url: Optional[str] = Field(None, max_length=500)
    gallery_images: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, str]]] = None
    technologies_used: Optional[List[str]] = None
    methodologies_used: Optional[List[str]] = None
    project_duration: Optional[str] = Field(None, max_length=50)
    team_size: Optional[int] = Field(None, ge=1)
    role_description: Optional[str] = None
    key_outcomes: Optional[List[str]] = None
    metrics_achieved: Optional[List[Dict[str, Any]]] = None
    lessons_learned: Optional[str] = None
    project_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    documentation_url: Optional[str] = Field(None, max_length=500)
    display_order: int = Field(0, ge=0)
    is_featured: bool = False
    is_visible: bool = True
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)


class PortfolioItemCreate(PortfolioItemBase):
    """Schema for creating portfolio item."""
    portfolio_id: int = Field(..., gt=0)
    source_type: Optional[str] = Field(None, pattern="^(simulation|manual|imported)$")
    source_simulation_id: Optional[int] = Field(None, gt=0)
    source_artifact_id: Optional[int] = Field(None, gt=0)
    completion_date: Optional[datetime] = None


class PortfolioItemUpdate(BaseModel):
    """Schema for updating portfolio item."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    item_type: Optional[str] = Field(None, pattern="^(project|certificate|skill|achievement|artifact)$")
    description: Optional[str] = None
    content: Optional[str] = None
    content_format: Optional[str] = Field(None, pattern="^(markdown|html|json)$")
    featured_image_url: Optional[str] = Field(None, max_length=500)
    gallery_images: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, str]]] = None
    technologies_used: Optional[List[str]] = None
    methodologies_used: Optional[List[str]] = None
    project_duration: Optional[str] = Field(None, max_length=50)
    team_size: Optional[int] = Field(None, ge=1)
    role_description: Optional[str] = None
    key_outcomes: Optional[List[str]] = None
    metrics_achieved: Optional[List[Dict[str, Any]]] = None
    lessons_learned: Optional[str] = None
    project_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    documentation_url: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_visible: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=50)
    completion_date: Optional[datetime] = None


class PortfolioItemResponse(PortfolioItemBase):
    """Schema for portfolio item response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    portfolio_id: int
    source_type: Optional[str] = None
    source_simulation_id: Optional[int] = None
    source_artifact_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completion_date: Optional[datetime] = None


# Achievement schemas
class AchievementBase(BaseModel):
    """Base achievement schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    achievement_type: str = Field(..., pattern="^(certification|project_completion|skill_mastery|milestone)$")
    category: str = Field(..., max_length=50)
    difficulty_level: int = Field(1, ge=1, le=5)
    badge_icon_url: Optional[str] = Field(None, max_length=500)
    badge_color: str = Field("#ffd700", max_length=20)
    is_verified: bool = False
    verification_source: Optional[str] = Field(None, max_length=100)
    verification_url: Optional[str] = Field(None, max_length=500)
    earned_from_simulation: bool = False
    criteria_met: Optional[List[str]] = None
    points_awarded: int = Field(0, ge=0)
    is_featured: bool = False
    is_public: bool = True
    display_order: int = Field(0, ge=0)


class AchievementCreate(AchievementBase):
    """Schema for creating achievement."""
    portfolio_id: Optional[int] = Field(None, gt=0)
    source_simulation_id: Optional[int] = Field(None, gt=0)


class AchievementUpdate(BaseModel):
    """Schema for updating achievement."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_verified: Optional[bool] = None
    verification_source: Optional[str] = Field(None, max_length=100)
    verification_url: Optional[str] = Field(None, max_length=500)
    is_featured: Optional[bool] = None
    is_public: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class AchievementResponse(AchievementBase):
    """Schema for achievement response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    portfolio_id: Optional[int] = None
    source_simulation_id: Optional[int] = None
    earned_at: datetime


# Testimonial schemas
class TestimonialBase(BaseModel):
    """Base testimonial schema."""
    content: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    recommender_name: str = Field(..., min_length=1, max_length=100)
    recommender_title: Optional[str] = Field(None, max_length=100)
    recommender_company: Optional[str] = Field(None, max_length=100)
    recommender_relationship: str = Field(..., pattern="^(supervisor|colleague|client|mentor|peer)$")
    recommender_email: Optional[EmailStr] = None
    recommender_linkedin: Optional[str] = Field(None, max_length=255)
    project_context: Optional[str] = Field(None, max_length=200)
    collaboration_duration: Optional[str] = Field(None, max_length=50)
    source: str = Field("manual", pattern="^(manual|linkedin|imported)$")
    is_featured: bool = False
    is_public: bool = True
    display_order: int = Field(0, ge=0)


class TestimonialCreate(TestimonialBase):
    """Schema for creating testimonial."""
    portfolio_id: Optional[int] = Field(None, gt=0)
    is_verified: bool = False
    date_of_collaboration: Optional[datetime] = None


class TestimonialUpdate(BaseModel):
    """Schema for updating testimonial."""
    content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    recommender_title: Optional[str] = Field(None, max_length=100)
    recommender_company: Optional[str] = Field(None, max_length=100)
    recommender_email: Optional[EmailStr] = None
    recommender_linkedin: Optional[str] = Field(None, max_length=255)
    project_context: Optional[str] = Field(None, max_length=200)
    collaboration_duration: Optional[str] = Field(None, max_length=50)
    is_verified: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_public: Optional[bool] = None
    display_order: Optional[int] = Field(None, ge=0)


class TestimonialResponse(TestimonialBase):
    """Schema for testimonial response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    portfolio_id: Optional[int] = None
    is_verified: bool
    created_at: datetime
    date_of_collaboration: Optional[datetime] = None


# Skill Assessment schemas
class SkillAssessmentBase(BaseModel):
    """Base skill assessment schema."""
    skill_name: str = Field(..., min_length=1, max_length=100)
    skill_category: str = Field(..., max_length=30)
    current_level: int = Field(..., ge=1, le=5)
    previous_level: Optional[int] = Field(None, ge=1, le=5)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    assessment_type: str = Field(..., pattern="^(ai_analysis|project_performance|self_assessment|quiz)$")
    evidence_sources: Optional[List[str]] = None
    ai_feedback: Optional[str] = None
    improvement_suggestions: Optional[List[str]] = None
    recommended_resources: Optional[List[Dict[str, str]]] = None
    progress_trend: Optional[str] = Field(None, pattern="^(improving|stable|declining)$")
    next_milestone: Optional[str] = Field(None, max_length=200)


class SkillAssessmentCreate(SkillAssessmentBase):
    """Schema for creating skill assessment."""
    is_verified: bool = False
    verification_project_id: Optional[int] = Field(None, gt=0)


class SkillAssessmentResponse(SkillAssessmentBase):
    """Schema for skill assessment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_verified: bool
    verification_project_id: Optional[int] = None
    assessed_at: datetime


# Learning Goal schemas
class LearningGoalBase(BaseModel):
    """Base learning goal schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    goal_type: str = Field(..., pattern="^(skill_acquisition|certification|project_completion|career_milestone)$")
    target_skill: Optional[str] = Field(None, max_length=100)
    target_level: Optional[int] = Field(None, ge=1, le=5)
    target_certification: Optional[str] = Field(None, max_length=100)
    target_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    progress_percentage: int = Field(0, ge=0, le=100)
    milestones: Optional[List[Dict[str, Any]]] = None
    completed_milestones: Optional[List[str]] = None
    status: str = Field("active", pattern="^(active|completed|paused|abandoned)$")
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    recommended_path: Optional[List[Dict[str, Any]]] = None


class LearningGoalCreate(LearningGoalBase):
    """Schema for creating learning goal."""
    pass


class LearningGoalUpdate(BaseModel):
    """Schema for updating learning goal."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target_skill: Optional[str] = Field(None, max_length=100)
    target_level: Optional[int] = Field(None, ge=1, le=5)
    target_certification: Optional[str] = Field(None, max_length=100)
    target_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    milestones: Optional[List[Dict[str, Any]]] = None
    completed_milestones: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|paused|abandoned)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    recommended_path: Optional[List[Dict[str, Any]]] = None


class LearningGoalResponse(LearningGoalBase):
    """Schema for learning goal response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# Complex responses with relationships
class PortfolioDetailed(PortfolioResponse):
    """Detailed portfolio with all content."""
    items: List[PortfolioItemResponse] = []
    achievements: List[AchievementResponse] = []
    testimonials: List[TestimonialResponse] = []


# List responses
class PortfolioListResponse(BaseModel):
    """Paginated portfolio list response."""
    portfolios: List[PortfolioResponse]
    total: int
    page: int
    size: int
    pages: int


class AchievementListResponse(BaseModel):
    """Paginated achievement list response."""
    achievements: List[AchievementResponse]
    total: int
    page: int
    size: int
    pages: int


class LearningGoalListResponse(BaseModel):
    """Paginated learning goal list response."""
    goals: List[LearningGoalResponse]
    total: int
    page: int
    size: int
    pages: int


# Portfolio export and sharing
class PortfolioExportRequest(BaseModel):
    """Request schema for portfolio export."""
    portfolio_id: int = Field(..., gt=0)
    format: str = Field(..., pattern="^(pdf|json|html)$")
    include_private_items: bool = False
    custom_styling: Optional[Dict[str, Any]] = None


class PortfolioExportResponse(BaseModel):
    """Response schema for portfolio export."""
    portfolio_id: int
    format: str
    file_url: str
    file_size: int
    generated_at: datetime
    expires_at: Optional[datetime] = None


class PortfolioShareRequest(BaseModel):
    """Request schema for portfolio sharing."""
    portfolio_id: int = Field(..., gt=0)
    share_type: str = Field(..., pattern="^(public_link|email|social)$")
    recipients: Optional[List[EmailStr]] = None
    message: Optional[str] = None
    expiry_date: Optional[datetime] = None


class ImportFromSimulationRequest(BaseModel):
    """Request to import project artifacts to portfolio."""
    portfolio_id: int = Field(..., gt=0)
    simulation_id: int = Field(..., gt=0)
    import_artifacts: bool = True
    import_as_project: bool = True
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None


# Additional portfolio schemas
class PortfolioListResponse(BaseModel):
    """Response for listing portfolios."""
    portfolios: List[PortfolioResponse]
    total: int
    skip: int
    limit: int


class PortfolioAnalyticsResponse(BaseModel):
    """Portfolio analytics response schema."""
    portfolio_id: int
    view_count: int
    total_items: int
    total_achievements: int
    last_updated: datetime
    is_public: bool
    public_url: Optional[str] = None