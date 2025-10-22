"""
Industry tracks and domain-specific content Pydantic v2 schemas.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Industry Track schemas
class IndustryTrackBase(BaseModel):
    """Base industry track schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    icon_url: Optional[str] = Field(None, max_length=500)
    color_theme: str = Field("#007bff", max_length=20)
    difficulty_levels: List[int] = Field(..., min_length=1)
    methodologies_focus: List[str] = Field(..., min_length=1)
    learning_objectives: List[str] = Field(..., min_length=1)
    prerequisite_skills: Optional[List[str]] = None
    career_outcomes: List[str] = Field(..., min_length=1)
    slug: str = Field(..., min_length=1, max_length=100)
    meta_description: Optional[str] = Field(None, max_length=160)


class IndustryTrackCreate(IndustryTrackBase):
    """Schema for creating industry track."""
    pass


class IndustryTrackUpdate(BaseModel):
    """Schema for updating industry track."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=500)
    color_theme: Optional[str] = Field(None, max_length=20)
    difficulty_levels: Optional[List[int]] = None
    methodologies_focus: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    prerequisite_skills: Optional[List[str]] = None
    career_outcomes: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_description: Optional[str] = Field(None, max_length=160)


class IndustryTrackResponse(IndustryTrackBase):
    """Schema for industry track response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    total_projects: int
    total_learners: int
    average_completion_rate: Optional[float] = None
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime


class IndustrySpecializationBase(BaseModel):
    """Base industry specialization schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    key_skills: List[str] = Field(..., min_length=1)
    tools_and_software: List[str] = Field(..., min_length=1)
    certification_paths: Optional[List[str]] = None
    job_market_demand: str = Field("medium", pattern="^(low|medium|high)$")
    average_salary_range: Optional[str] = Field(None, max_length=50)
    growth_projection: Optional[str] = Field(None, pattern="^(growing|stable|declining)$")
    recommended_resources: Optional[List[Dict[str, str]]] = None


class IndustrySpecializationCreate(IndustrySpecializationBase):
    """Schema for creating industry specialization."""
    industry_track_id: int = Field(..., gt=0)


class IndustrySpecializationUpdate(BaseModel):
    """Schema for updating industry specialization."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    key_skills: Optional[List[str]] = None
    tools_and_software: Optional[List[str]] = None
    certification_paths: Optional[List[str]] = None
    job_market_demand: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    average_salary_range: Optional[str] = Field(None, max_length=50)
    growth_projection: Optional[str] = Field(None, pattern="^(growing|stable|declining)$")
    recommended_resources: Optional[List[Dict[str, str]]] = None
    is_active: Optional[bool] = None


class IndustrySpecializationResponse(IndustrySpecializationBase):
    """Schema for industry specialization response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    industry_track_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Skill schemas
class SkillCategoryBase(BaseModel):
    """Base skill category schema."""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    category_type: str = Field(..., pattern="^(technical|soft|methodology|tool)$")


class SkillCategoryCreate(SkillCategoryBase):
    """Schema for creating skill category."""
    pass


class SkillCategoryResponse(SkillCategoryBase):
    """Schema for skill category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class SkillBase(BaseModel):
    """Base skill schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    related_skills: Optional[List[int]] = None
    difficulty_to_learn: int = Field(3, ge=1, le=5)
    market_demand: str = Field("medium", pattern="^(low|medium|high)$")


class SkillCreate(SkillBase):
    """Schema for creating skill."""
    category_id: int = Field(..., gt=0)


class SkillUpdate(BaseModel):
    """Schema for updating skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    related_skills: Optional[List[int]] = None
    difficulty_to_learn: Optional[int] = Field(None, ge=1, le=5)
    market_demand: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    is_active: Optional[bool] = None


class SkillResponse(SkillBase):
    """Schema for skill response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Learning Path schemas
class LearningPathBase(BaseModel):
    """Base learning path schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    sequence_order: int = Field(..., ge=0)
    estimated_duration_hours: int = Field(..., ge=1)
    difficulty_progression: List[int] = Field(..., min_length=1)
    learning_outcomes: List[str] = Field(..., min_length=1)
    assessment_criteria: List[str] = Field(..., min_length=1)
    prerequisites: Optional[List[str]] = None


class LearningPathCreate(LearningPathBase):
    """Schema for creating learning path."""
    industry_track_id: int = Field(..., gt=0)


class LearningPathUpdate(BaseModel):
    """Schema for updating learning path."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    estimated_duration_hours: Optional[int] = Field(None, ge=1)
    difficulty_progression: Optional[List[int]] = None
    learning_outcomes: Optional[List[str]] = None
    assessment_criteria: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    is_active: Optional[bool] = None


class LearningPathResponse(LearningPathBase):
    """Schema for learning path response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    industry_track_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Certification schemas
class CertificationPathBase(BaseModel):
    """Base certification path schema."""
    name: str = Field(..., min_length=1, max_length=200)
    issuing_organization: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    certification_level: str = Field(..., pattern="^(entry|associate|professional|expert)$")
    industry_relevance: List[int] = Field(..., min_length=1)
    prerequisites: Optional[List[str]] = None
    exam_details: Optional[Dict[str, Any]] = None
    study_materials: Optional[List[Dict[str, str]]] = None
    cost_usd: Optional[int] = Field(None, ge=0)  # in cents
    preparation_time_hours: Optional[int] = Field(None, ge=0)
    validity_period_months: Optional[int] = Field(None, ge=0)
    career_impact: Optional[str] = None
    salary_impact_percentage: Optional[int] = Field(None, ge=0, le=100)
    official_website: Optional[str] = Field(None, max_length=500)
    registration_url: Optional[str] = Field(None, max_length=500)


class CertificationPathCreate(CertificationPathBase):
    """Schema for creating certification path."""
    pass


class CertificationPathUpdate(BaseModel):
    """Schema for updating certification path."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    exam_details: Optional[Dict[str, Any]] = None
    study_materials: Optional[List[Dict[str, str]]] = None
    cost_usd: Optional[int] = Field(None, ge=0)
    preparation_time_hours: Optional[int] = Field(None, ge=0)
    validity_period_months: Optional[int] = Field(None, ge=0)
    career_impact: Optional[str] = None
    salary_impact_percentage: Optional[int] = Field(None, ge=0, le=100)
    official_website: Optional[str] = Field(None, max_length=500)
    registration_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_recommended: Optional[bool] = None


class CertificationPathResponse(CertificationPathBase):
    """Schema for certification path response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_recommended: bool
    created_at: datetime
    updated_at: datetime


# Complex responses with relationships
class IndustryTrackWithSpecializations(IndustryTrackResponse):
    """Industry track with specializations."""
    specializations: List[IndustrySpecializationResponse] = []


class SkillCategoryWithSkills(SkillCategoryResponse):
    """Skill category with skills."""
    skills: List[SkillResponse] = []


# List responses
class IndustryTrackListResponse(BaseModel):
    """Paginated industry track list response."""
    tracks: List[IndustryTrackResponse]
    total: int
    page: int
    size: int
    pages: int


class SkillListResponse(BaseModel):
    """Paginated skill list response."""
    skills: List[SkillResponse]
    total: int
    page: int
    size: int
    pages: int


class CertificationPathListResponse(BaseModel):
    """Paginated certification path list response."""
    certifications: List[CertificationPathResponse]
    total: int
    page: int
    size: int
    pages: int


# Search and filter schemas
class IndustryTrackSearchRequest(BaseModel):
    """Search request for industry tracks."""
    query: Optional[str] = None
    difficulty_levels: Optional[List[int]] = None
    methodologies: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


class SkillSearchRequest(BaseModel):
    """Search request for skills."""
    query: Optional[str] = None
    category_id: Optional[int] = None
    category_type: Optional[str] = Field(None, pattern="^(technical|soft|methodology|tool)$")
    market_demand: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    difficulty_range: Optional[List[int]] = Field(None, min_length=2, max_length=2)


class CertificationSearchRequest(BaseModel):
    """Search request for certifications."""
    query: Optional[str] = None
    certification_level: Optional[str] = Field(None, pattern="^(entry|associate|professional|expert)$")
    industry_track_ids: Optional[List[int]] = None
    cost_range: Optional[List[int]] = Field(None, min_length=2, max_length=2)  # in cents
    is_recommended: Optional[bool] = None