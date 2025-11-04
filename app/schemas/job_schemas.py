"""
Job search and application Pydantic v2 schemas.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# Job Listing schemas
class JobListingBase(BaseModel):
    """Base job listing schema."""
    title: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    employment_type: str = Field("full-time", pattern="^(full-time|part-time|contract|freelance)$")
    work_mode: str = Field("onsite", pattern="^(remote|onsite|hybrid)$")
    experience_level: str = Field(..., pattern="^(entry|mid|senior|lead|executive)$")
    salary_min: Optional[int] = Field(None, ge=0)  # in cents
    salary_max: Optional[int] = Field(None, ge=0)  # in cents
    salary_currency: str = Field("USD", max_length=3)
    salary_period: str = Field("yearly", pattern="^(yearly|monthly|hourly)$")
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    technologies: Optional[List[str]] = None
    methodologies: Optional[List[str]] = None
    company_size: Optional[str] = Field(None, pattern="^(startup|small|medium|large|enterprise)$")
    industry: Optional[str] = Field(None, max_length=50)
    application_url: Optional[str] = Field(None, max_length=500)
    source_platform: str = Field(..., max_length=50)
    source_url: str = Field(..., max_length=1000)


class JobListingCreate(JobListingBase):
    """Schema for creating job listing."""
    external_job_id: Optional[str] = Field(None, max_length=100)
    hr_email: Optional[EmailStr] = None
    hiring_manager_email: Optional[EmailStr] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = Field(None, max_length=255)
    application_deadline: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class JobListingUpdate(BaseModel):
    """Schema for updating job listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    popularity_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class JobListingResponse(JobListingBase):
    """Schema for job listing response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    external_job_id: Optional[str] = None
    hr_email: Optional[str] = None
    hiring_manager_email: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    application_deadline: Optional[datetime] = None
    match_score: Optional[float] = None
    popularity_score: Optional[float] = None
    is_active: bool
    is_featured: bool
    is_remote_friendly: bool
    is_entry_level_friendly: bool
    keywords: Optional[List[str]] = None
    posted_at: Optional[datetime] = None
    scraped_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


# Job Application schemas
class JobApplicationBase(BaseModel):
    """Base job application schema."""
    cover_letter: Optional[str] = None
    customized_cv_content: Optional[Dict[str, Any]] = None
    tailored_skills: Optional[List[str]] = None
    user_notes: Optional[str] = None
    priority_level: str = Field("medium", pattern="^(low|medium|high)$")


class JobApplicationCreate(JobApplicationBase):
    """Schema for creating job application."""
    job_listing_id: int = Field(..., gt=0)
    cv_id: Optional[int] = Field(None, gt=0)
    is_auto_applied: bool = False
    auto_application_type: Optional[str] = Field(None, pattern="^(one_click|bulk|scheduled)$")


class JobApplicationUpdate(BaseModel):
    """Schema for updating job application."""
    status: Optional[str] = Field(None, pattern="^(draft|submitted|reviewed|interview|rejected|accepted)$")
    cover_letter: Optional[str] = None
    customized_cv_content: Optional[Dict[str, Any]] = None
    tailored_skills: Optional[List[str]] = None
    response_received: Optional[bool] = None
    response_type: Optional[str] = Field(None, pattern="^(acknowledgment|interview|rejection|questions)$")
    response_date: Optional[datetime] = None
    interview_scheduled: Optional[bool] = None
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = Field(None, pattern="^(phone|video|onsite|technical)$")
    final_outcome: Optional[str] = Field(None, pattern="^(hired|rejected|withdrawn|no_response)$")
    feedback_received: Optional[str] = None
    salary_offered: Optional[int] = Field(None, ge=0)
    user_notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    priority_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")


class JobApplicationResponse(JobApplicationBase):
    """Schema for job application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    job_listing_id: int
    cv_id: Optional[int] = None
    status: str
    is_auto_applied: bool
    auto_application_type: Optional[str] = None
    hr_email_sent: bool
    ceo_email_sent: bool
    hr_email_opened: bool
    ceo_email_opened: bool
    response_received: bool
    response_type: Optional[str] = None
    response_date: Optional[datetime] = None
    interview_scheduled: bool
    interview_date: Optional[datetime] = None
    interview_type: Optional[str] = None
    final_outcome: Optional[str] = None
    feedback_received: Optional[str] = None
    salary_offered: Optional[int] = None
    follow_up_date: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Job Match schemas
class JobMatchBase(BaseModel):
    """Base job match schema."""
    overall_match_score: float = Field(..., ge=0.0, le=1.0)
    skills_match_score: float = Field(..., ge=0.0, le=1.0)
    experience_match_score: float = Field(..., ge=0.0, le=1.0)
    location_match_score: float = Field(..., ge=0.0, le=1.0)
    salary_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    matching_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    match_reasoning: Optional[str] = None
    application_tips: Optional[List[str]] = None
    skill_gap_recommendations: Optional[List[str]] = None


class JobMatchCreate(JobMatchBase):
    """Schema for creating job match."""
    job_listing_id: int = Field(..., gt=0)


class JobMatchUpdate(BaseModel):
    """Schema for updating job match."""
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_feedback: Optional[str] = None
    is_bookmarked: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class JobMatchResponse(JobMatchBase):
    """Schema for job match response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    job_listing_id: int
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    is_bookmarked: bool
    is_dismissed: bool
    is_recommended: bool
    created_at: datetime
    updated_at: datetime


# Job Search schemas
class JobSearchBase(BaseModel):
    """Base job search schema."""
    name: str = Field(..., min_length=1, max_length=100)
    search_terms: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=100)
    work_mode: Optional[str] = Field(None, pattern="^(remote|onsite|hybrid)$")
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|freelance)$")
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|executive)$")
    salary_min: Optional[int] = Field(None, ge=0)
    industry: Optional[str] = Field(None, max_length=50)
    is_alert_enabled: bool = False
    alert_frequency: str = Field("daily", pattern="^(daily|weekly|monthly)$")


class JobSearchCreate(JobSearchBase):
    """Schema for creating job search."""
    pass


class JobSearchUpdate(BaseModel):
    """Schema for updating job search."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    search_terms: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=100)
    work_mode: Optional[str] = Field(None, pattern="^(remote|onsite|hybrid)$")
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|freelance)$")
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|executive)$")
    salary_min: Optional[int] = Field(None, ge=0)
    industry: Optional[str] = Field(None, max_length=50)
    is_alert_enabled: Optional[bool] = None
    alert_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")


class JobSearchResponse(JobSearchBase):
    """Schema for job search response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    last_alert_sent: Optional[datetime] = None
    last_search_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# Company Profile schemas
class CompanyProfileBase(BaseModel):
    """Base company profile schema."""
    company_name: str = Field(..., min_length=1, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=50)
    company_size: Optional[str] = Field(None, pattern="^(startup|small|medium|large|enterprise)$")
    founded_year: Optional[int] = Field(None, ge=1800, le=2030)
    headquarters_location: Optional[str] = Field(None, max_length=100)
    locations: Optional[List[str]] = None
    remote_policy: Optional[str] = Field(None, pattern="^(remote_first|hybrid|onsite_only)$")
    company_culture: Optional[str] = None
    benefits: Optional[List[str]] = None
    values: Optional[List[str]] = None


class CompanyProfileCreate(CompanyProfileBase):
    """Schema for creating company profile."""
    hr_email: Optional[EmailStr] = None
    careers_email: Optional[EmailStr] = None
    ceo_email: Optional[EmailStr] = None
    glassdoor_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    employee_satisfaction_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    typical_hiring_process: Optional[str] = None
    average_interview_duration: Optional[str] = Field(None, max_length=50)
    response_time_days: Optional[int] = Field(None, ge=0, le=365)
    preferred_tech_stack: Optional[List[str]] = None
    preferred_methodologies: Optional[List[str]] = None


class CompanyProfileResponse(CompanyProfileBase):
    """Schema for company profile response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    hr_email: Optional[str] = None
    careers_email: Optional[str] = None
    ceo_email: Optional[str] = None
    glassdoor_rating: Optional[float] = None
    employee_satisfaction_score: Optional[float] = None
    typical_hiring_process: Optional[str] = None
    average_interview_duration: Optional[str] = None
    response_time_days: Optional[int] = None
    preferred_tech_stack: Optional[List[str]] = None
    preferred_methodologies: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


# Complex responses with relationships
class JobApplicationWithDetails(JobApplicationResponse):
    """Job application with job listing details."""
    job_listing: JobListingResponse


class JobMatchWithListing(JobMatchResponse):
    """Job match with job listing details."""
    job_listing: JobListingResponse


# List responses
class JobListingListResponse(BaseModel):
    """Paginated job listing list response."""
    jobs: List[JobListingResponse]
    total: int
    page: int
    size: int
    pages: int


class JobApplicationListResponse(BaseModel):
    """Paginated job application list response."""
    applications: List[JobApplicationResponse]
    total: int
    page: int
    size: int
    pages: int


class JobMatchListResponse(BaseModel):
    """Paginated job match list response."""
    matches: List[JobMatchResponse]
    total: int
    page: int
    size: int
    pages: int


# Search and filter schemas
class JobSearchRequest(BaseModel):
    """Search request for job listings."""
    query: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = Field(None, pattern="^(remote|onsite|hybrid)$")
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|freelance)$")
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|executive)$")
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    industry: Optional[str] = None
    required_skills: Optional[List[str]] = None
    company_size: Optional[str] = Field(None, pattern="^(startup|small|medium|large|enterprise)$")
    posted_since: Optional[int] = Field(None, ge=1, le=365)  # days
    posted_within_days: Optional[int] = Field(None, ge=1, le=365)
    is_entry_level_friendly: Optional[bool] = None
    is_remote_friendly: Optional[bool] = None
    remote_only: Optional[bool] = None
    sort_by: Optional[str] = Field(
        None,
        pattern="^(posted_date_desc|posted_date_asc|salary_desc|relevance)$"
    )


class AutoApplicationRequest(BaseModel):
    """Request for automated job applications."""
    search_criteria: JobSearchRequest
    max_applications: int = Field(10, ge=1, le=100)
    cv_id: int = Field(..., gt=0)
    cover_letter_template: Optional[str] = None
    custom_message: Optional[str] = None
    send_to_hr: bool = True
    send_to_ceo: bool = False


class JobApplicationRequest(BaseModel):
    """Request for job application."""
    job_listing_id: int = Field(..., gt=0)
    cv_id: int = Field(..., gt=0)
    cover_letter: Optional[str] = None
    custom_message: Optional[str] = None
    expected_salary: Optional[int] = Field(None, gt=0)


class AutoApplicationResponse(BaseModel):
    """Response for automated job applications."""
    total_jobs_found: int
    applications_sent: int
    failed_applications: int
    application_ids: List[int]
    errors: List[str]


# Job Alert schemas
class JobAlertBase(BaseModel):
    """Base job alert schema."""
    title: str = Field(..., min_length=1, max_length=100)
    keywords: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|executive)$")
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    job_type: Optional[str] = Field(None, pattern="^(remote|onsite|hybrid)$")
    is_active: bool = True
    frequency: str = Field("daily", pattern="^(daily|weekly|instant)$")
    email_notifications: bool = True


class JobAlertCreate(JobAlertBase):
    """Job alert creation schema."""
    pass


class JobAlertResponse(JobAlertBase):
    """Job alert response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    last_triggered: Optional[datetime] = None
    jobs_found_count: int = 0
    created_at: datetime
    updated_at: datetime


# Analytics and reporting schemas
class JobAnalyticsResponse(BaseModel):
    """Job analytics response schema."""
    total_jobs: int = 0
    active_jobs: int = 0
    jobs_this_month: int = 0
    top_skills: List[str] = []
    top_companies: List[str] = []
    average_salary: Optional[float] = None
    salary_range: Dict[str, Optional[int]] = {"min": None, "max": None}


class ApplicationAnalyticsResponse(BaseModel):
    """Application analytics response schema."""
    total_applications: int = 0
    applications_this_month: int = 0
    success_rate: float = 0.0
    avg_response_time: Optional[float] = None
    status_breakdown: Dict[str, int] = {}
    top_applied_companies: List[str] = []


# Smart Job Matching schemas
class JobMatchResponse(BaseModel):
    """Job match analysis response schema."""
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: List[str] = []
    missing_skills: List[str] = []
    recommended_skills: List[str] = []
    experience_gap: Optional[str] = None
    salary_fit: Optional[str] = None


class JobRecommendationResponse(BaseModel):
    """Job recommendation with matching details."""
    job: Dict[str, Any]  # Job data from external APIs
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: List[str] = []
    matching_method: Optional[str] = "TF-IDF"
    recommended_action: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SavedJobResponse(BaseModel):
    """Saved job response schema."""
    id: int
    job_title: str
    company_name: str
    job_url: str
    saved_at: datetime
    job_data: Dict[str, Any] = {}
    
    model_config = ConfigDict(from_attributes=True)


class SmartJobSearchRequest(BaseModel):
    """Smart job search request schema."""
    keywords: Optional[List[str]] = []
    location: Optional[str] = None
    remote_only: bool = False
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|lead|executive)$")
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|freelance)$")
    salary_min: Optional[int] = Field(None, ge=0)
    max_results: int = Field(20, ge=1, le=100)
    use_ai_matching: bool = True


class JobMatchingCapabilitiesResponse(BaseModel):
    """Job matching capabilities response."""
    sentence_transformers_available: bool
    embedding_model: Optional[str] = None
    fallback_method: str = "TF-IDF"
    features: List[str] = []
    error: Optional[str] = None


# Aliases for compatibility
JobCreate = JobListingCreate
JobUpdate = JobListingUpdate
JobResponse = JobListingResponse
JobListResponse = JobListingListResponse
CompanyCreate = CompanyProfileCreate
CompanyResponse = CompanyProfileResponse