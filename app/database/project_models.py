"""
Project simulation and AI coaching database models.
"""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum, Float, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.core.utils import utc_now

if TYPE_CHECKING:
    from app.database.user_models import User
    from app.database.industry_models import IndustryTrack


class ProjectMethodology(str, enum.Enum):
    """Project management methodologies."""
    AGILE = "agile"
    SCRUM = "scrum"
    WATERFALL = "waterfall"
    PRINCE2 = "prince2"
    HYBRID = "hybrid"
    KANBAN = "kanban"


class ProjectStatus(str, enum.Enum):
    """Project simulation status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ArtifactType(str, enum.Enum):
    """Types of project artifacts."""
    GANTT_CHART = "gantt_chart"
    PROJECT_CHARTER = "project_charter"
    RISK_LOG = "risk_log"
    STATUS_REPORT = "status_report"
    REQUIREMENTS_DOC = "requirements_doc"
    MEETING_MINUTES = "meeting_minutes"
    BUDGET_PLAN = "budget_plan"
    COMMUNICATION_PLAN = "communication_plan"
    STAKEHOLDER_MATRIX = "stakeholder_matrix"
    LESSONS_LEARNED = "lessons_learned"


class CollaborationStatus(str, enum.Enum):
    """Invitation lifecycle for project collaborators."""
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ProjectSimulation(Base):
    """Main project simulation entity."""
    
    __tablename__ = "project_simulations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    industry_track_id: Mapped[int] = mapped_column(ForeignKey("industry_tracks.id"), nullable=False)
    
    # Project basics
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[ProjectMethodology] = mapped_column(SQLEnum(ProjectMethodology), nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    estimated_duration_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Project scenario details
    team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in cents
    stakeholders: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of stakeholder info
    constraints: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of constraints
    objectives: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON array of objectives
    
    # Progress tracking
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus), default=ProjectStatus.NOT_STARTED, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # AI coaching data
    ai_feedback_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_feedback_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Completion data
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_duration_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    industry_track: Mapped["IndustryTrack"] = relationship("IndustryTrack", back_populates="projects")
    phases: Mapped[List["ProjectPhase"]] = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")
    artifacts: Mapped[List["ProjectArtifact"]] = relationship("ProjectArtifact", back_populates="project", cascade="all, delete-orphan")
    ai_sessions: Mapped[List["AiCoachingSession"]] = relationship("AiCoachingSession", back_populates="project", cascade="all, delete-orphan")
    collaborators: Mapped[List["ProjectCollaborator"]] = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_project_simulations_user_id', 'user_id'),
        Index('idx_project_simulations_industry_track_id', 'industry_track_id'),
        Index('idx_project_simulations_methodology', 'methodology'),
        Index('idx_project_simulations_difficulty_level', 'difficulty_level'),
        Index('idx_project_simulations_estimated_duration_hours', 'estimated_duration_hours'),
        Index('idx_project_simulations_status', 'status'),
        Index('idx_project_simulations_progress_percentage', 'progress_percentage'),
        Index('idx_project_simulations_current_phase', 'current_phase'),
        Index('idx_project_simulations_ai_feedback_score', 'ai_feedback_score'),
        Index('idx_project_simulations_started_at', 'started_at'),
        Index('idx_project_simulations_completed_at', 'completed_at'),
        Index('idx_project_simulations_created_at', 'created_at'),
        Index('idx_project_simulations_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_project_simulations_user_status', 'user_id', 'status'),
        Index('idx_project_simulations_user_track', 'user_id', 'industry_track_id'),
        Index('idx_project_simulations_track_difficulty', 'industry_track_id', 'difficulty_level'),
        Index('idx_project_simulations_status_methodology', 'status', 'methodology'),
        Index('idx_project_simulations_user_progress', 'user_id', 'progress_percentage'),
        Index('idx_project_simulations_user_completed', 'user_id', 'completed_at'),
        Index('idx_project_simulations_active_progress', 'status', 'progress_percentage'),
        
        {"sqlite_autoincrement": True}
    )


class ProjectPhase(Base):
    """Individual phases within a project simulation."""
    
    __tablename__ = "project_phases"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project_simulations.id", ondelete="CASCADE"), nullable=False)
    
    # Phase details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Scheduling
    planned_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Progress
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # AI feedback for this phase
    ai_phase_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_phase_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    project: Mapped["ProjectSimulation"] = relationship("ProjectSimulation", back_populates="phases")
    tasks: Mapped[List["ProjectTask"]] = relationship("ProjectTask", back_populates="phase", cascade="all, delete-orphan")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_project_phases_project_id', 'project_id'),
        Index('idx_project_phases_order_index', 'order_index'),
        Index('idx_project_phases_is_completed', 'is_completed'),
        Index('idx_project_phases_progress_percentage', 'progress_percentage'),
        Index('idx_project_phases_planned_start_date', 'planned_start_date'),
        Index('idx_project_phases_planned_end_date', 'planned_end_date'),
        Index('idx_project_phases_actual_start_date', 'actual_start_date'),
        Index('idx_project_phases_actual_end_date', 'actual_end_date'),
        Index('idx_project_phases_ai_phase_score', 'ai_phase_score'),
        Index('idx_project_phases_created_at', 'created_at'),
        Index('idx_project_phases_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_project_phases_project_order', 'project_id', 'order_index'),
        Index('idx_project_phases_project_completed', 'project_id', 'is_completed'),
        Index('idx_project_phases_project_progress', 'project_id', 'progress_percentage'),
        Index('idx_project_phases_completed_order', 'is_completed', 'order_index'),
        Index('idx_project_phases_project_start', 'project_id', 'actual_start_date'),
        
        {"sqlite_autoincrement": True}
    )


class ProjectTask(Base):
    """Individual tasks within project phases."""
    
    __tablename__ = "project_tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("project_phases.id", ondelete="CASCADE"), nullable=False)
    
    # Task details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Task properties
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assigned_team_member: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    
    # Status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Dependencies
    depends_on_task_ids: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # JSON array of task IDs
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    phase: Mapped["ProjectPhase"] = relationship("ProjectPhase", back_populates="tasks")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_project_tasks_phase_id', 'phase_id'),
        Index('idx_project_tasks_order_index', 'order_index'),
        Index('idx_project_tasks_priority', 'priority'),
        Index('idx_project_tasks_is_completed', 'is_completed'),
        Index('idx_project_tasks_assigned_team_member', 'assigned_team_member'),
        Index('idx_project_tasks_estimated_hours', 'estimated_hours'),
        Index('idx_project_tasks_actual_hours', 'actual_hours'),
        Index('idx_project_tasks_completed_at', 'completed_at'),
        Index('idx_project_tasks_created_at', 'created_at'),
        Index('idx_project_tasks_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_project_tasks_phase_order', 'phase_id', 'order_index'),
        Index('idx_project_tasks_phase_completed', 'phase_id', 'is_completed'),
        Index('idx_project_tasks_phase_priority', 'phase_id', 'priority'),
        Index('idx_project_tasks_completed_priority', 'is_completed', 'priority'),
        Index('idx_project_tasks_assigned_completed', 'assigned_team_member', 'is_completed'),
        
        {"sqlite_autoincrement": True}
    )


class ProjectCollaborator(Base):
    """Project collaborators with optional external invites."""

    __tablename__ = "project_collaborators"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project_simulations.id", ondelete="CASCADE"), nullable=False)
    collaborator_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    collaborator_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    permissions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    invite_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invitation_status: Mapped[CollaborationStatus] = mapped_column(SQLEnum(CollaborationStatus), default=CollaborationStatus.INVITED, nullable=False)
    invited_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project: Mapped["ProjectSimulation"] = relationship("ProjectSimulation", back_populates="collaborators")
    collaborator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[collaborator_user_id])
    invited_by: Mapped["User"] = relationship("User", foreign_keys=[invited_by_user_id])

    __table_args__ = (
        Index("idx_project_collaborators_project", "project_id"),
        Index("idx_project_collaborators_user", "collaborator_user_id"),
        Index("idx_project_collaborators_email", "collaborator_email"),
        Index("idx_project_collaborators_status", "invitation_status"),
        Index("idx_project_collaborators_project_user", "project_id", "collaborator_user_id"),
        Index("idx_project_collaborators_project_email", "project_id", "collaborator_email"),
        {"sqlite_autoincrement": True}
    )


class ProjectArtifact(Base):
    """Generated project artifacts and deliverables."""
    
    __tablename__ = "project_artifacts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project_simulations.id", ondelete="CASCADE"), nullable=False)
    
    # Artifact details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(SQLEnum(ArtifactType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # File information
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in bytes
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Generation info
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Content (for text-based artifacts)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)  # markdown, html, json
    
    # Portfolio inclusion
    include_in_portfolio: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    project: Mapped["ProjectSimulation"] = relationship("ProjectSimulation", back_populates="artifacts")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_project_artifacts_project_id', 'project_id'),
        Index('idx_project_artifacts_artifact_type', 'artifact_type'),
        Index('idx_project_artifacts_is_ai_generated', 'is_ai_generated'),
        Index('idx_project_artifacts_content_format', 'content_format'),
        Index('idx_project_artifacts_include_in_portfolio', 'include_in_portfolio'),
        Index('idx_project_artifacts_file_size', 'file_size'),
        Index('idx_project_artifacts_mime_type', 'mime_type'),
        Index('idx_project_artifacts_created_at', 'created_at'),
        Index('idx_project_artifacts_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_project_artifacts_project_type', 'project_id', 'artifact_type'),
        Index('idx_project_artifacts_project_portfolio', 'project_id', 'include_in_portfolio'),
        Index('idx_project_artifacts_type_generated', 'artifact_type', 'is_ai_generated'),
        Index('idx_project_artifacts_portfolio_type', 'include_in_portfolio', 'artifact_type'),
        Index('idx_project_artifacts_project_created', 'project_id', 'created_at'),
        
        {"sqlite_autoincrement": True}
    )


class AiCoachingSession(Base):
    """AI coaching sessions and interactions."""
    
    __tablename__ = "ai_coaching_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project_simulations.id", ondelete="CASCADE"), nullable=False)
    
    # Session details
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)  # lesson, feedback, q_and_a, guidance
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # AI interaction data
    user_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Voice coaching data
    has_voice_narration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voice_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    voice_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Feedback and scoring
    user_satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    learning_progress_impact: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Session metadata
    session_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    project: Mapped["ProjectSimulation"] = relationship("ProjectSimulation", back_populates="ai_sessions")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_ai_coaching_sessions_project_id', 'project_id'),
        Index('idx_ai_coaching_sessions_session_type', 'session_type'),
        Index('idx_ai_coaching_sessions_has_voice_narration', 'has_voice_narration'),
        Index('idx_ai_coaching_sessions_user_satisfaction_rating', 'user_satisfaction_rating'),
        Index('idx_ai_coaching_sessions_learning_progress_impact', 'learning_progress_impact'),
        Index('idx_ai_coaching_sessions_session_duration_minutes', 'session_duration_minutes'),
        Index('idx_ai_coaching_sessions_voice_duration_seconds', 'voice_duration_seconds'),
        Index('idx_ai_coaching_sessions_created_at', 'created_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_ai_coaching_sessions_project_type', 'project_id', 'session_type'),
        Index('idx_ai_coaching_sessions_project_created', 'project_id', 'created_at'),
        Index('idx_ai_coaching_sessions_type_rating', 'session_type', 'user_satisfaction_rating'),
        Index('idx_ai_coaching_sessions_voice_duration', 'has_voice_narration', 'voice_duration_seconds'),
        Index('idx_ai_coaching_sessions_project_impact', 'project_id', 'learning_progress_impact'),
        
        {"sqlite_autoincrement": True}
    )


class ProjectTemplate(Base):
    """Reusable project templates for different scenarios."""
    
    __tablename__ = "project_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    industry_track_id: Mapped[int] = mapped_column(ForeignKey("industry_tracks.id"), nullable=False)
    
    # Template details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[ProjectMethodology] = mapped_column(SQLEnum(ProjectMethodology), nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Template structure
    phases_template: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON structure of phases and tasks
    stakeholders_template: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON template for stakeholders
    constraints_template: Mapped[str] = mapped_column(JSON, nullable=False)  # JSON template for constraints
    
    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    industry_track: Mapped["IndustryTrack"] = relationship("IndustryTrack", back_populates="project_templates")

    # Indexes for performance optimization
    __table_args__ = (
        # Single column indexes for common queries
        Index('idx_project_templates_industry_track_id', 'industry_track_id'),
        Index('idx_project_templates_methodology', 'methodology'),
        Index('idx_project_templates_difficulty_level', 'difficulty_level'),
        Index('idx_project_templates_usage_count', 'usage_count'),
        Index('idx_project_templates_average_rating', 'average_rating'),
        Index('idx_project_templates_is_active', 'is_active'),
        Index('idx_project_templates_created_at', 'created_at'),
        Index('idx_project_templates_updated_at', 'updated_at'),
        
        # Composite indexes for common filter combinations
        Index('idx_project_templates_track_active', 'industry_track_id', 'is_active'),
        Index('idx_project_templates_track_difficulty', 'industry_track_id', 'difficulty_level'),
        Index('idx_project_templates_methodology_difficulty', 'methodology', 'difficulty_level'),
        Index('idx_project_templates_active_rating', 'is_active', 'average_rating'),
        Index('idx_project_templates_track_usage', 'industry_track_id', 'usage_count'),
        Index('idx_project_templates_active_usage', 'is_active', 'usage_count'),
        
        {"sqlite_autoincrement": True}
    )


# Aliases for compatibility  
Project = ProjectSimulation
ProjectCollaboratorModel = ProjectCollaborator
AICoachingSession = AiCoachingSession