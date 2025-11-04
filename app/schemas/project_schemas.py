"""
Project simulation and AI coaching Pydantic v2 schemas.
"""
from datetime import datetime
from typing import Optional, Any, List, Dict, TypedDict
from pydantic import BaseModel, Field, ConfigDict, model_validator, EmailStr

from app.database.project_models import (
    ProjectMethodology,
    ProjectStatus,
    ArtifactType,
    CollaborationStatus,
)


# Base schemas
class ProjectSimulationBase(BaseModel):
    """Base project simulation schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    methodology: ProjectMethodology
    difficulty_level: int = Field(..., ge=1, le=5)
    estimated_duration_hours: int = Field(..., ge=1, le=1000)
    team_size: int = Field(..., ge=1, le=50)
    budget: Optional[int] = Field(None, ge=0)  # in cents
    stakeholders: Optional[Any] = None  # JSON field
    constraints: Optional[Any] = None  # JSON field
    objectives: Any = None  # JSON field


class ProjectSimulationCreate(ProjectSimulationBase):
    """Schema for creating project simulation."""
    industry_track_id: int = Field(..., gt=0)


# Aliases for compatibility
CreateSimulationRequest = ProjectSimulationCreate


class ProjectSimulationUpdate(BaseModel):
    """Schema for updating project simulation."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_phase: Optional[str] = None
    ai_feedback_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    ai_feedback_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    actual_duration_hours: Optional[int] = Field(None, ge=0)


# Aliases for compatibility
UpdateSimulationRequest = ProjectSimulationUpdate


class ProjectSimulationResponse(ProjectSimulationBase):
    """Schema for project simulation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    industry_track_id: int
    status: ProjectStatus
    progress_percentage: int
    current_phase: Optional[str] = None
    ai_feedback_score: Optional[float] = None
    ai_feedback_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_duration_hours: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ProjectPhaseBase(BaseModel):
    """Base project phase schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    order_index: int = Field(..., ge=0)
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None


class ProjectPhaseCreate(ProjectPhaseBase):
    """Schema for creating project phase."""
    project_id: int = Field(..., gt=0)


class ProjectPhaseUpdate(BaseModel):
    """Schema for updating project phase."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    ai_phase_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    ai_phase_feedback: Optional[str] = None


class ProjectPhaseResponse(ProjectPhaseBase):
    """Schema for project phase response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    is_completed: bool
    progress_percentage: int
    ai_phase_score: Optional[float] = None
    ai_phase_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectTaskBase(BaseModel):
    """Base project task schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    order_index: int = Field(..., ge=0)
    estimated_hours: Optional[int] = Field(None, ge=0)
    assigned_team_member: Optional[str] = Field(None, max_length=100)
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$")
    depends_on_task_ids: Optional[List[int]] = None


class ProjectTaskCreate(ProjectTaskBase):
    """Schema for creating project task."""
    phase_id: Optional[int] = Field(None, gt=0)


class ProjectTaskUpdate(BaseModel):
    """Schema for updating project task."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    assigned_team_member: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    is_completed: Optional[bool] = None
    depends_on_task_ids: Optional[List[int]] = None


class ProjectTaskResponse(ProjectTaskBase):
    """Schema for project task response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    phase_id: int
    actual_hours: Optional[int] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ProjectArtifactBase(BaseModel):
    """Base project artifact schema."""
    name: str = Field(..., min_length=1, max_length=200)
    artifact_type: ArtifactType
    description: Optional[str] = None
    is_ai_generated: bool = True
    generation_prompt: Optional[str] = None
    content: Optional[str] = None
    content_format: str = Field("markdown", pattern="^(markdown|html|json)$")
    include_in_portfolio: bool = True


class ProjectArtifactCreate(ProjectArtifactBase):
    """Schema for creating project artifact."""
    project_id: int = Field(..., gt=0)


class ProjectArtifactUpdate(BaseModel):
    """Schema for updating project artifact."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    include_in_portfolio: Optional[bool] = None


class ProjectArtifactResponse(ProjectArtifactBase):
    """Schema for project artifact response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AiCoachingSessionBase(BaseModel):
    """Base AI coaching session schema."""
    session_type: str = Field(..., pattern="^(lesson|feedback|q_and_a|guidance)$")
    topic: str = Field(..., min_length=1, max_length=200)
    user_input: Optional[str] = None
    ai_response: str = Field(..., min_length=1)
    has_voice_narration: bool = False
    voice_duration_seconds: Optional[int] = Field(None, ge=0)


class AiCoachingSessionCreate(AiCoachingSessionBase):
    """Schema for creating AI coaching session."""
    ai_response: Optional[str] = Field(None, min_length=1)
    project_id: Optional[int] = Field(None, gt=0)


class AiCoachingSessionUpdate(BaseModel):
    """Schema for updating AI coaching session."""
    user_satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    learning_progress_impact: Optional[float] = Field(None, ge=0.0, le=1.0)
    session_duration_minutes: Optional[int] = Field(None, ge=0)


class AiCoachingSessionResponse(AiCoachingSessionBase):
    """Schema for AI coaching session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    voice_file_url: Optional[str] = None
    user_satisfaction_rating: Optional[int] = None
    learning_progress_impact: Optional[float] = None
    session_duration_minutes: Optional[int] = None
    created_at: datetime


class ProjectTemplateBase(BaseModel):
    """Base project template schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    methodology: ProjectMethodology
    difficulty_level: int = Field(..., ge=1, le=5)
    phases_template: List[Dict[str, Any]] = Field(..., min_length=1)
    stakeholders_template: List[Dict[str, Any]]
    constraints_template: List[str]


class ProjectTemplateCreate(ProjectTemplateBase):
    """Schema for creating project template."""
    industry_track_id: int = Field(..., gt=0)


class ProjectTemplateUpdate(BaseModel):
    """Schema for updating project template."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    phases_template: Optional[List[Dict[str, Any]]] = None
    stakeholders_template: Optional[List[Dict[str, Any]]] = None
    constraints_template: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProjectTemplateResponse(ProjectTemplateBase):
    """Schema for project template response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    industry_track_id: int
    usage_count: int
    average_rating: Optional[float] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Complex project responses with relationships
class ProjectPhaseWithTasks(ProjectPhaseResponse):
    """Project phase with tasks."""
    tasks: List[ProjectTaskResponse] = []


class ProjectSimulationDetailed(ProjectSimulationResponse):
    """Detailed project simulation with all related data."""
    phases: List[ProjectPhaseWithTasks] = []
    artifacts: List[ProjectArtifactResponse] = []
    ai_sessions: List[AiCoachingSessionResponse] = []


class ProjectCollaboratorBase(BaseModel):
    """Shared fields for project collaborators."""

    role: str = Field("viewer", min_length=1, max_length=50)
    permissions: List[str] = Field(default_factory=list)
    invite_message: Optional[str] = Field(None, max_length=500)


class ProjectCollaboratorCreate(ProjectCollaboratorBase):
    """Schema for adding project collaborator."""

    collaborator_user_id: Optional[int] = Field(None, gt=0)
    collaborator_email: Optional[EmailStr] = None

    @model_validator(mode="after")
    def validate_contact(cls, values: "ProjectCollaboratorCreate") -> "ProjectCollaboratorCreate":
        if not values.collaborator_user_id and not values.collaborator_email:
            raise ValueError("Either collaborator_user_id or collaborator_email must be provided")
        return values


class ProjectCollaboratorResponse(ProjectCollaboratorBase):
    """Response schema for project collaborator."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    collaborator_user_id: Optional[int] = None
    collaborator_email: Optional[EmailStr] = None
    invitation_status: CollaborationStatus
    invited_by_user_id: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(TypedDict):
    """Paginated project list response."""
    projects: List[ProjectSimulationResponse]
    total: int
    page: int
    size: int
    pages: int


class ProjectSearchRequest(BaseModel):
    """Search parameters for filtering projects."""
    model_config = ConfigDict(extra="ignore")

    query: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# AI-specific schemas
class AIFeedbackRequest(BaseModel):
    """Request schema for AI feedback."""
    project_id: int = Field(..., gt=0)
    context: str = Field(..., min_length=1)
    specific_questions: Optional[List[str]] = None


class AIFeedbackResponse(BaseModel):
    """Response schema for AI feedback."""
    overall_score: float = Field(..., ge=0.0, le=10.0)
    feedback_summary: str
    detailed_feedback: Dict[str, Any]
    improvement_suggestions: List[str]
    next_steps: List[str]


class GenerateArtifactRequest(BaseModel):
    """Request schema for generating artifacts."""
    project_id: int = Field(..., gt=0)
    artifact_type: ArtifactType
    custom_prompt: Optional[str] = None
    include_project_data: bool = True


class StartProjectRequest(BaseModel):
    """Request schema for starting a project."""
    template_id: Optional[int] = None
    custom_parameters: Optional[Dict[str, Any]] = None


class SimulationStatsResponse(BaseModel):
    """Response schema for simulation statistics."""
    total_simulations: int
    completed_simulations: int
    in_progress_simulations: int
    average_completion_time_hours: Optional[float] = None
    average_score: Optional[float] = None
    completion_rate: float
    most_popular_methodology: Optional[str] = None


class ProjectAnalyticsMetrics(BaseModel):
    """Analytics for a single project."""
    project_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    completion_rate: float
    project_duration_days: Optional[int] = None
    created_at: datetime
    last_activity: datetime


# Aliases for compatibility
ProjectCreate = ProjectSimulationCreate
ProjectUpdate = ProjectSimulationUpdate
ProjectResponse = ProjectSimulationResponse
ProjectAnalyticsResponse = ProjectAnalyticsMetrics
AICoachingSessionCreate = AiCoachingSessionCreate
AICoachingSessionResponse = AiCoachingSessionResponse
