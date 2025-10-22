"""
CV Builder Pydantic v2 schemas.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr

from app.database.cv_models import CVStatus


# Base CV schemas
class CVBase(BaseModel):
    """Base CV schema."""
    title: str = Field(..., min_length=1, max_length=200)
    template_type: str = Field(..., pattern="^(onsite|remote|hybrid|creative)$")
    target_role: Optional[str] = Field(None, max_length=100)
    target_industry: Optional[str] = Field(None, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)
    professional_title: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    professional_summary: Optional[str] = None
    objective_statement: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    personal_website: Optional[str] = Field(None, max_length=255)
    include_photo: bool = False
    color_scheme: str = Field("blue", max_length=20)
    font_style: str = Field("professional", max_length=30)


class CVCreate(CVBase):
    """Schema for creating CV."""
    is_ai_generated: bool = False
    generation_prompt: Optional[str] = None


# Aliases for compatibility
CreateCVRequest = CVCreate


class CVUpdate(BaseModel):
    """Schema for updating CV."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    template_type: Optional[str] = Field(None, pattern="^(onsite|remote|hybrid|creative)$")
    target_role: Optional[str] = Field(None, max_length=100)
    target_industry: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    professional_title: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    professional_summary: Optional[str] = None
    objective_statement: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    personal_website: Optional[str] = Field(None, max_length=255)
    include_photo: Optional[bool] = None
    photo_url: Optional[str] = Field(None, max_length=500)
    color_scheme: Optional[str] = Field(None, max_length=20)
    font_style: Optional[str] = Field(None, max_length=30)
    is_public: Optional[bool] = None
    is_default: Optional[bool] = None


# Aliases for compatibility  
UpdateCVRequest = CVUpdate


class CVResponse(CVBase):
    """Schema for CV response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_ai_generated: bool
    generation_prompt: Optional[str] = None
    last_exported_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    is_public: bool
    is_default: bool
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Work Experience schemas
class WorkExperienceBase(BaseModel):
    """Base work experience schema."""
    job_title: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    employment_type: str = Field("full-time", pattern="^(full-time|part-time|contract|freelance|internship)$")
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: str = Field(..., min_length=1)
    key_achievements: Optional[List[str]] = None
    technologies_used: Optional[List[str]] = None
    team_size_managed: Optional[int] = Field(None, ge=0)
    budget_managed: Optional[int] = Field(None, ge=0)  # in cents
    projects_delivered: Optional[int] = Field(None, ge=0)
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True


class WorkExperienceCreate(WorkExperienceBase):
    """Schema for creating work experience."""
    cv_id: int = Field(..., gt=0)


class WorkExperienceUpdate(BaseModel):
    """Schema for updating work experience."""
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|freelance|internship)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    key_achievements: Optional[List[str]] = None
    technologies_used: Optional[List[str]] = None
    team_size_managed: Optional[int] = Field(None, ge=0)
    budget_managed: Optional[int] = Field(None, ge=0)
    projects_delivered: Optional[int] = Field(None, ge=0)
    display_order: Optional[int] = Field(None, ge=0)
    include_in_cv: Optional[bool] = None


class WorkExperienceResponse(WorkExperienceBase):
    """Schema for work experience response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime
    updated_at: datetime


# Education schemas
class EducationBase(BaseModel):
    """Base education schema."""
    institution_name: str = Field(..., min_length=1, max_length=200)
    degree_type: str = Field(..., pattern="^(bachelor|master|phd|certificate|diploma)$")
    field_of_study: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    gpa: Optional[str] = Field(None, max_length=10)
    honors: Optional[str] = Field(None, max_length=100)
    relevant_coursework: Optional[List[str]] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    thesis_title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True


class EducationCreate(EducationBase):
    """Schema for creating education."""
    cv_id: int = Field(..., gt=0)


class EducationUpdate(BaseModel):
    """Schema for updating education."""
    institution_name: Optional[str] = Field(None, min_length=1, max_length=200)
    degree_type: Optional[str] = Field(None, pattern="^(bachelor|master|phd|certificate|diploma)$")
    field_of_study: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    gpa: Optional[str] = Field(None, max_length=10)
    honors: Optional[str] = Field(None, max_length=100)
    relevant_coursework: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    thesis_title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    include_in_cv: Optional[bool] = None


class EducationResponse(EducationBase):
    """Schema for education response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime
    updated_at: datetime


# Aliases for CV Education
CVEducationCreate = EducationCreate
CVEducationUpdate = EducationUpdate
CVEducationResponse = EducationResponse

# Aliases for CV Experience
CVExperienceCreate = WorkExperienceCreate
CVExperienceUpdate = WorkExperienceUpdate  
CVExperienceResponse = WorkExperienceResponse

# Additional CV aliases
CVSearchRequest = Dict[str, Any]  # Placeholder for CV search
CVAnalyticsResponse = Dict[str, Any]  # Placeholder for CV analytics


# CV Skill schemas
class CVSkillBase(BaseModel):
    """Base CV skill schema."""
    skill_name: str = Field(..., min_length=1, max_length=50)
    skill_category: str = Field(..., pattern="^(technical|soft|methodology|language|tool)$")
    proficiency_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced|expert)$")
    proficiency_percentage: Optional[int] = Field(None, ge=0, le=100)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True
    highlight_skill: bool = False


class CVSkillCreate(CVSkillBase):
    """Schema for creating CV skill."""
    cv_id: int = Field(..., gt=0)


class CVSkillUpdate(BaseModel):
    """Schema for updating CV skill."""
    skill_name: Optional[str] = Field(None, min_length=1, max_length=50)
    skill_category: Optional[str] = Field(None, pattern="^(technical|soft|methodology|language|tool)$")
    proficiency_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced|expert)$")
    proficiency_percentage: Optional[int] = Field(None, ge=0, le=100)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)
    display_order: Optional[int] = Field(None, ge=0)
    include_in_cv: Optional[bool] = None
    highlight_skill: Optional[bool] = None


class CVSkillResponse(CVSkillBase):
    """Schema for CV skill response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime


# CV Project schemas
class CVProjectBase(BaseModel):
    """Base CV project schema."""
    project_name: str = Field(..., min_length=1, max_length=200)
    project_type: str = Field(..., pattern="^(work|personal|academic|volunteer|simulation)$")
    description: str = Field(..., min_length=1)
    technologies_used: Optional[List[str]] = None
    methodologies_used: Optional[List[str]] = None
    team_size: Optional[int] = Field(None, ge=1)
    role_in_project: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_description: Optional[str] = Field(None, max_length=50)
    key_achievements: Optional[List[str]] = None
    metrics_and_impact: Optional[str] = None
    project_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True
    is_featured: bool = False


class CVProjectCreate(CVProjectBase):
    """Schema for creating CV project."""
    cv_id: int = Field(..., gt=0)
    source_simulation_id: Optional[int] = Field(None, gt=0)


class CVProjectUpdate(BaseModel):
    """Schema for updating CV project."""
    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    project_type: Optional[str] = Field(None, pattern="^(work|personal|academic|volunteer|simulation)$")
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = None
    methodologies_used: Optional[List[str]] = None
    team_size: Optional[int] = Field(None, ge=1)
    role_in_project: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_description: Optional[str] = Field(None, max_length=50)
    key_achievements: Optional[List[str]] = None
    metrics_and_impact: Optional[str] = None
    project_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=0)
    include_in_cv: Optional[bool] = None
    is_featured: Optional[bool] = None


class CVProjectResponse(CVProjectBase):
    """Schema for CV project response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    source_simulation_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Certification schemas
class CertificationBase(BaseModel):
    """Base certification schema."""
    certification_name: str = Field(..., min_length=1, max_length=200)
    issuing_organization: str = Field(..., min_length=1, max_length=100)
    credential_id: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    does_not_expire: bool = False
    verification_url: Optional[str] = Field(None, max_length=500)
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True


class CertificationCreate(CertificationBase):
    """Schema for creating certification."""
    cv_id: int = Field(..., gt=0)


class CertificationUpdate(BaseModel):
    """Schema for updating certification."""
    certification_name: Optional[str] = Field(None, min_length=1, max_length=200)
    issuing_organization: Optional[str] = Field(None, min_length=1, max_length=100)
    credential_id: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    does_not_expire: Optional[bool] = None
    verification_url: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=0)
    include_in_cv: Optional[bool] = None


class CertificationResponse(CertificationBase):
    """Schema for certification response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime


# Language and Reference schemas
class LanguageBase(BaseModel):
    """Base language schema."""
    language_name: str = Field(..., min_length=1, max_length=50)
    proficiency_level: str = Field(..., pattern="^(native|fluent|advanced|intermediate|beginner)$")
    certification_name: Optional[str] = Field(None, max_length=100)
    certification_score: Optional[str] = Field(None, max_length=20)
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True


class LanguageCreate(LanguageBase):
    """Schema for creating language."""
    cv_id: int = Field(..., gt=0)


class LanguageResponse(LanguageBase):
    """Schema for language response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime


class ReferenceBase(BaseModel):
    """Base reference schema."""
    full_name: str = Field(..., min_length=1, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    relationship: str = Field(..., pattern="^(supervisor|colleague|client|mentor)$")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    years_known: Optional[int] = Field(None, ge=0, le=50)
    permission_to_contact: bool = True
    display_order: int = Field(0, ge=0)
    include_in_cv: bool = True


class ReferenceCreate(ReferenceBase):
    """Schema for creating reference."""
    cv_id: int = Field(..., gt=0)


class ReferenceResponse(ReferenceBase):
    """Schema for reference response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cv_id: int
    created_at: datetime


# Complex CV responses with relationships
class CVDetailed(CVResponse):
    """Detailed CV with all sections."""
    work_experiences: List[WorkExperienceResponse] = []
    educations: List[EducationResponse] = []
    cv_skills: List[CVSkillResponse] = []
    projects: List[CVProjectResponse] = []
    certifications: List[CertificationResponse] = []
    languages: List[LanguageResponse] = []
    references: List[ReferenceResponse] = []


# List responses
class CVListResponse(BaseModel):
    """Paginated CV list response."""
    cvs: List[CVResponse]
    total: int
    page: int
    size: int
    pages: int


# CV Generation and Export
class GenerateCVRequest(BaseModel):
    """Request schema for AI CV generation."""
    template_type: str = Field(..., pattern="^(onsite|remote|hybrid|creative)$")
    target_role: str = Field(..., min_length=1)
    target_industry: Optional[str] = None
    emphasize_skills: Optional[List[str]] = None
    include_simulation_projects: bool = True
    custom_prompt: Optional[str] = None


class ExportCVRequest(BaseModel):
    """Request schema for CV export."""
    cv_id: int = Field(..., gt=0)
    format: str = Field(..., pattern="^(pdf|docx)$")
    include_photo: Optional[bool] = None
    custom_styling: Optional[Dict[str, Any]] = None


class ExportCVResponse(BaseModel):
    """Response schema for CV export."""
    cv_id: int
    format: str
    file_url: str
    file_size: int
    generated_at: datetime
    expires_at: Optional[datetime] = None


# CV Section schemas
class CVSectionBase(BaseModel):
    """Base CV section schema."""
    section_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    order_index: int = Field(0, ge=0)
    is_bulleted: bool = False
    include_dates: bool = False
    is_visible: bool = True


class CVSectionCreate(CVSectionBase):
    """Schema for creating CV section."""
    cv_id: int = Field(..., gt=0)


class CVSectionUpdate(BaseModel):
    """Schema for updating CV section."""
    section_type: Optional[str] = Field(None, min_length=1, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1)
    order_index: Optional[int] = Field(None, ge=0)
    is_bulleted: Optional[bool] = None
    include_dates: Optional[bool] = None
    is_visible: Optional[bool] = None


class CVSectionResponse(CVSectionBase):
    """Schema for CV section response."""
    id: int
    cv_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# CV Template schemas
class CVTemplateResponse(BaseModel):
    """Schema for CV template response."""
    id: int
    name: str
    description: Optional[str]
    template_type: str
    target_role: Optional[str]
    target_industry: Optional[str]
    preview_image_url: Optional[str]
    usage_count: int
    average_rating: Optional[float]
    is_active: bool
    is_premium: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# CV Export schemas
class CVExportResponse(BaseModel):
    """Schema for CV export response."""
    id: int
    cv_id: int
    user_id: int
    format: str
    file_url: str
    file_name: str
    file_size: int
    include_photo: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)