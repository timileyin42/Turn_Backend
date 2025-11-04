"""
ProjectSimulation management service for ProjectSimulation CRUD, tasks, and AI coaching integration.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.database.project_models import (
    ProjectSimulation,
    ProjectTask,
    ProjectTemplate,
    ProjectPhase,
    ProjectArtifact,
    AiCoachingSession,
    AICoachingSession,
    ProjectCollaborator,
    CollaborationStatus,
)
from app.database.user_models import User, UserRole
from app.schemas.project_schemas import (
    ProjectSimulationCreate,
    ProjectSimulationUpdate,
    ProjectSimulationResponse,
    ProjectTaskCreate,
    ProjectTaskUpdate,
    ProjectTaskResponse,
    ProjectTemplateResponse,
    AiCoachingSessionCreate,
    AiCoachingSessionResponse,
    ProjectPhaseCreate,
    ProjectPhaseUpdate,
    ProjectPhaseResponse,
    ProjectArtifactCreate,
    ProjectArtifactResponse,
    ProjectListResponse,
    ProjectSearchRequest,
    AICoachingSessionCreate,
    AICoachingSessionResponse,
    ProjectAnalyticsResponse,
    ProjectCollaboratorCreate,
    ProjectCollaboratorResponse,
)
from app.services.ai_service import ai_service


class ProjectService:
    """Service for ProjectSimulation management and AI coaching operations."""
    
    async def create_project(
        self, 
        db: AsyncSession, 
        user_id: int, 
        project_data: ProjectSimulationCreate
    ) -> ProjectSimulationResponse:
        """
        Create a new ProjectSimulation.
        
        Args:
            db: Database session
            user_id: ProjectSimulation owner ID
            project_data: ProjectSimulation creation data
            
        Returns:
            Created ProjectSimulation response
        """
        db_project = ProjectSimulation(
            user_id=user_id,
            **project_data.model_dump()
        )
        
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        return ProjectSimulationResponse.model_validate(db_project)
    
    async def get_project_by_id(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> Optional[ProjectSimulationResponse]:
        """
        Get ProjectSimulation by ID with access control.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: Requesting user ID
            
        Returns:
            ProjectSimulation response if user has access
        """
        ProjectSimulation = await self._get_project_with_access_check(db, project_id, user_id)
        if not ProjectSimulation:
            return None
        
        return ProjectSimulationResponse.model_validate(ProjectSimulation)
    
    async def update_project(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int, 
        project_data: ProjectSimulationUpdate
    ) -> Optional[ProjectSimulationResponse]:
        """
        Update ProjectSimulation information.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID (must be owner or collaborator)
            project_data: Updated ProjectSimulation data
            
        Returns:
            Updated ProjectSimulation response
        """
        ProjectSimulation = await self._get_project_with_access_check(
            db, project_id, user_id, require_write=True
        )
        if not ProjectSimulation:
            return None
        
        # Update fields
        update_data = project_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(ProjectSimulation, field, value)
            
            ProjectSimulation.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(ProjectSimulation)
        
        return ProjectSimulationResponse.model_validate(ProjectSimulation)
    
    async def delete_project(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> bool:
        """
        Delete ProjectSimulation (owner only).
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID (must be owner)
            
        Returns:
            True if ProjectSimulation was deleted
        """
        project = await self._get_project_with_access_check(
            db, project_id, user_id, require_write=True
        )
        if not project:
            return False

        await db.delete(project)
        await db.commit()
        return True
    
    async def get_user_projects(
        self, 
        db: AsyncSession, 
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> ProjectListResponse:
        """
        Get projects owned by or accessible to user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Paginated ProjectSimulation list
        """
        # Projects owned by user
        query = select(ProjectSimulation).options(
            selectinload(ProjectSimulation.phases),
            selectinload(ProjectSimulation.artifacts),
            selectinload(ProjectSimulation.ai_sessions)
        ).where(
            ProjectSimulation.user_id == user_id
        ).order_by(desc(ProjectSimulation.updated_at))
        
        # Count total
        count_query = select(func.count(ProjectSimulation.id)).where(
            ProjectSimulation.user_id == user_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        project_responses = [ProjectSimulationResponse.model_validate(p) for p in projects]

        return {
            "projects": project_responses,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit,
        }
    
    async def search_projects(
        self, 
        db: AsyncSession, 
        user_id: int,
        search_params: ProjectSearchRequest,
        skip: int = 0,
        limit: int = 20
    ) -> ProjectListResponse:
        """
        Search projects with filters.
        
        Args:
            db: Database session
            user_id: User ID
            search_params: Search parameters
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Filtered ProjectSimulation list
        """
        query = select(ProjectSimulation).options(
            selectinload(ProjectSimulation.phases),
            selectinload(ProjectSimulation.artifacts)
        )
        
        # Base access control - only owner
        conditions = [ProjectSimulation.user_id == user_id]
        
        # Apply search filters
        if search_params.query:
            search_term = f"%{search_params.query.strip()}%"
            conditions.append(
                or_(
                    ProjectSimulation.title.ilike(search_term),
                    ProjectSimulation.description.ilike(search_term)
                )
            )
        
        if search_params.status:
            conditions.append(ProjectSimulation.status == search_params.status)
        
        if search_params.date_from:
            conditions.append(ProjectSimulation.created_at >= search_params.date_from)
        
        if search_params.date_to:
            conditions.append(ProjectSimulation.created_at <= search_params.date_to)
        
        query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count(ProjectSimulation.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(ProjectSimulation.updated_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        project_responses = [ProjectSimulationResponse.model_validate(p) for p in projects]

        return {
            "projects": project_responses,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit,
        }
    
    # Task Management
    
    async def create_task(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int, 
        task_data: ProjectTaskCreate
    ) -> Optional[ProjectTaskResponse]:
        """
        Create a new task in ProjectSimulation.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID
            task_data: Task creation data
            
        Returns:
            Created task response
        """
        is_admin = await self._is_user_admin(db, user_id)

        def _project_filters() -> list:
            base_filters = [ProjectSimulation.id == project_id]
            if not is_admin:
                base_filters.append(ProjectSimulation.user_id == user_id)
            return base_filters

        # Ensure the phase belongs to the project when explicitly supplied
        phase = None
        if task_data.phase_id:
            phase_conditions = [ProjectPhase.id == task_data.phase_id, *_project_filters()]
            phase_result = await db.execute(
                select(ProjectPhase)
                .join(ProjectSimulation)
                .where(and_(*phase_conditions))
            )
            phase = phase_result.scalar_one_or_none()

        if not phase:
            # Fallback to the first available phase within the project
            fallback_result = await db.execute(
                select(ProjectPhase)
                .join(ProjectSimulation)
                .where(and_(*_project_filters()))
                .order_by(ProjectPhase.order_index)
            )
            phase = fallback_result.scalars().first()

        if not phase:
            # Lazily provision a default phase if the project has none
            project_exists = await self._check_project_access(db, project_id, user_id)
            if not project_exists:
                return None

            max_order_stmt = select(func.max(ProjectPhase.order_index)).where(
                ProjectPhase.project_id == project_id
            )
            current_max_order = (await db.execute(max_order_stmt)).scalar() or -1

            phase = ProjectPhase(
                project_id=project_id,
                name="General Phase",
                description="Auto-generated phase for task management.",
                order_index=current_max_order + 1,
            )
            db.add(phase)
            await db.flush()

        task_payload = task_data.model_dump()
        task_payload["phase_id"] = phase.id
        db_task = ProjectTask(**task_payload)
        
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        return ProjectTaskResponse.model_validate(db_task)
    
    async def update_task(
        self, 
        db: AsyncSession, 
        task_id: int, 
        user_id: int, 
        task_data: ProjectTaskUpdate
    ) -> Optional[ProjectTaskResponse]:
        """
        Update ProjectSimulation task.
        
        Args:
            db: Database session
            task_id: Task ID
            user_id: User ID
            task_data: Updated task data
            
        Returns:
            Updated task response
        """
        # Get task with ProjectSimulation access check
        task_result = await db.execute(
            select(ProjectTask, ProjectPhase.project_id)
            .join(ProjectPhase, ProjectTask.phase_id == ProjectPhase.id)
            .where(ProjectTask.id == task_id)
        )
        row = task_result.first()

        if not row:
            return None

        task, task_project_id = row

        # Check ProjectSimulation access
        project_access = await self._check_project_access(
            db, task_project_id, user_id, require_write=True
        )
        if not project_access:
            return None
        
        # Update fields
        update_data = task_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(task, field, value)
            
            task.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(task)
        
        return ProjectTaskResponse.model_validate(task)
    
    async def get_project_tasks(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> List[ProjectTaskResponse]:
        """
        Get all tasks for a ProjectSimulation.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID
            
        Returns:
            List of ProjectSimulation tasks
        """
        # Check ProjectSimulation access
        if not await self._check_project_access(db, project_id, user_id):
            return []
        
        result = await db.execute(
            select(ProjectTask)
            .join(ProjectPhase, ProjectTask.phase_id == ProjectPhase.id)
            .where(ProjectPhase.project_id == project_id)
            .order_by(ProjectTask.created_at)
        )
        tasks = result.scalars().all()
        
        return [ProjectTaskResponse.model_validate(task) for task in tasks]
    
    # AI Coaching
    
    async def create_ai_coaching_session(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int, 
        session_data: AICoachingSessionCreate
    ) -> Optional[AICoachingSessionResponse]:
        """
        Create AI coaching session for ProjectSimulation.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID
            session_data: Session data
            
        Returns:
            Created AI coaching session
        """
        # Check ProjectSimulation access
        if not await self._check_project_access(db, project_id, user_id):
            return None
        
        session_payload = session_data.model_dump(exclude={"project_id"}, exclude_none=True)

        if not session_payload.get("ai_response"):
            generated_response = await ai_service.generate_project_coaching_response(
                session_type=session_payload.get("session_type", "coaching"),
                topic=session_payload.get("topic"),
                user_input=session_payload.get("user_input"),
            )
            session_payload["ai_response"] = generated_response

        db_session = AICoachingSession(
            project_id=project_id,
            **session_payload,
            created_at=datetime.utcnow()
        )
        
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        
        return AICoachingSessionResponse.model_validate(db_session)
    
    async def get_project_ai_sessions(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> List[AICoachingSessionResponse]:
        """
        Get AI coaching sessions for ProjectSimulation.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID
            
        Returns:
            List of AI coaching sessions
        """
        # Check ProjectSimulation access
        if not await self._check_project_access(db, project_id, user_id):
            return []
        
        result = await db.execute(
            select(AICoachingSession)
            .where(AICoachingSession.project_id == project_id)
            .order_by(desc(AICoachingSession.created_at))
        )
        sessions = result.scalars().all()
        
        return [AICoachingSessionResponse.model_validate(session) for session in sessions]
    
    # ProjectSimulation Analytics
    
    async def get_project_analytics(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> Optional[ProjectAnalyticsResponse]:
        """
        Get ProjectSimulation analytics and statistics.
        
        Args:
            db: Database session
            project_id: ProjectSimulation ID
            user_id: User ID
            
        Returns:
            ProjectSimulation analytics data
        """
        # Check ProjectSimulation access
        if not await self._check_project_access(db, project_id, user_id):
            return None
        
        # Get ProjectSimulation with tasks
        result = await db.execute(
            select(ProjectSimulation)
            .options(
                selectinload(ProjectSimulation.phases).selectinload(ProjectPhase.tasks)
            )
            .where(ProjectSimulation.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # Flatten tasks across phases
        tasks = [task for phase in project.phases for task in phase.tasks]

        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.is_completed)
        in_progress_tasks = sum(
            1 for task in tasks if not task.is_completed and task.actual_hours not in (None, 0)
        )
        pending_tasks = total_tasks - completed_tasks - in_progress_tasks

        completion_rate = (completed_tasks / total_tasks * 100.0) if total_tasks else 0.0

        project_duration = None
        if project.started_at and project.completed_at:
            project_duration = (project.completed_at - project.started_at).days
        
        return ProjectAnalyticsResponse(
            project_id=project_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=max(in_progress_tasks, 0),
            pending_tasks=max(pending_tasks, 0),
            completion_rate=completion_rate,
            project_duration_days=project_duration,
            created_at=project.created_at,
            last_activity=project.updated_at
        )
    
    # Collaboration

    async def add_collaborator(
        self,
        db: AsyncSession,
        project_id: int,
        user_id: int,
        collaborator_data: ProjectCollaboratorCreate,
    ) -> Optional[ProjectCollaboratorResponse]:
        """Add a collaborator to a project."""

        project = await self._get_project_with_access_check(
            db, project_id, user_id, require_write=True
        )
        if not project:
            return None

        target_user: Optional[User] = None
        collaborator_user_id = collaborator_data.collaborator_user_id
        collaborator_email = (
            collaborator_data.collaborator_email.lower()
            if collaborator_data.collaborator_email
            else None
        )

        if collaborator_user_id:
            user_result = await db.execute(
                select(User).where(User.id == collaborator_user_id)
            )
            target_user = user_result.scalar_one_or_none()
            if not target_user:
                raise ValueError("Collaborator user not found")

        if not target_user and collaborator_email:
            email_result = await db.execute(
                select(User).where(func.lower(User.email) == collaborator_email)
            )
            target_user = email_result.scalar_one_or_none()

        if target_user:
            collaborator_user_id = target_user.id
            collaborator_email = target_user.email.lower()
            if collaborator_user_id == project.user_id:
                raise ValueError("Project owner is already a collaborator by default")

        if collaborator_data.collaborator_email and target_user and collaborator_email != collaborator_data.collaborator_email.lower():
            raise ValueError("Provided email does not match collaborator account")

        if collaborator_user_id:
            existing_by_user = await db.execute(
                select(ProjectCollaborator).where(
                    ProjectCollaborator.project_id == project_id,
                    ProjectCollaborator.collaborator_user_id == collaborator_user_id,
                )
            )
            if existing_by_user.scalar_one_or_none():
                raise ValueError("Collaborator already added to this project")

        if collaborator_email:
            existing_by_email = await db.execute(
                select(ProjectCollaborator).where(
                    ProjectCollaborator.project_id == project_id,
                    func.lower(ProjectCollaborator.collaborator_email) == collaborator_email,
                )
            )
            if existing_by_email.scalar_one_or_none():
                raise ValueError("Collaborator already invited with this email")

        invitation_status = (
            CollaborationStatus.ACCEPTED if target_user else CollaborationStatus.INVITED
        )

        db_collaborator = ProjectCollaborator(
            project_id=project_id,
            collaborator_user_id=collaborator_user_id,
            collaborator_email=collaborator_email,
            role=collaborator_data.role,
            permissions=collaborator_data.permissions,
            invite_message=collaborator_data.invite_message,
            invitation_status=invitation_status,
            invited_by_user_id=user_id,
        )

        db.add(db_collaborator)
        await db.commit()
        await db.refresh(db_collaborator)

        return ProjectCollaboratorResponse.model_validate(db_collaborator)
    
    # Helper methods
    
    async def _get_project_with_access_check(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int,
        require_write: bool = False
    ) -> Optional[ProjectSimulation]:
        """Get ProjectSimulation with access control (owner only)."""
        is_admin = await self._is_user_admin(db, user_id)
        conditions = [ProjectSimulation.id == project_id]
        if not is_admin:
            conditions.append(ProjectSimulation.user_id == user_id)

        result = await db.execute(
            select(ProjectSimulation)
            .options(
                selectinload(ProjectSimulation.phases),
                selectinload(ProjectSimulation.artifacts)
            )
            .where(and_(*conditions))
        )
        project = result.scalar_one_or_none()
        return project
    
    async def _check_project_access(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int,
        require_write: bool = False
    ) -> bool:
        """Check if user has access to ProjectSimulation (owner only)."""
        is_admin = await self._is_user_admin(db, user_id)
        conditions = [ProjectSimulation.id == project_id]
        if not is_admin:
            conditions.append(ProjectSimulation.user_id == user_id)

        result = await db.execute(
            select(ProjectSimulation).where(and_(*conditions))
        )
        project = result.scalar_one_or_none()

        return project is not None

    async def _is_user_admin(self, db: AsyncSession, user_id: int) -> bool:
        """Check whether the given user has admin privileges."""
        if user_id is None:
            return False

        result = await db.execute(
            select(User.role).where(User.id == user_id)
        )
        role = result.scalar_one_or_none()
        return role == UserRole.ADMIN


# Global ProjectSimulation service instance
project_service = ProjectService()
