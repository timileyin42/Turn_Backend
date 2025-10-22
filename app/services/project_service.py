"""
Project management service for project CRUD, tasks, and AI coaching integration.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.database.project_models import (
    ProjectSimulation, ProjectTask, ProjectTemplate, ProjectPhase, ProjectArtifact,
    AiCoachingSession, Project, ProjectCollaborator, AICoachingSession
)
from app.schemas.project_schemas import (
    ProjectSimulationCreate, ProjectSimulationUpdate, ProjectSimulationResponse, 
    ProjectTaskCreate, ProjectTaskUpdate, ProjectTaskResponse,
    ProjectTemplateResponse, AiCoachingSessionCreate, AiCoachingSessionResponse,
    ProjectPhaseCreate, ProjectPhaseUpdate, ProjectPhaseResponse,
    ProjectArtifactCreate, ProjectArtifactResponse,
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectListResponse,
    ProjectSearchRequest, AICoachingSessionCreate, AICoachingSessionResponse,
    ProjectAnalyticsResponse, ProjectCollaboratorCreate, ProjectCollaboratorResponse
)


class ProjectService:
    """Service for project management and AI coaching operations."""
    
    async def create_project(
        self, 
        db: AsyncSession, 
        user_id: int, 
        project_data: ProjectCreate
    ) -> ProjectResponse:
        """
        Create a new project.
        
        Args:
            db: Database session
            user_id: Project owner ID
            project_data: Project creation data
            
        Returns:
            Created project response
        """
        db_project = Project(
            owner_id=user_id,
            **project_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        
        return ProjectResponse.model_validate(db_project)
    
    async def get_project_by_id(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> Optional[ProjectResponse]:
        """
        Get project by ID with access control.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: Requesting user ID
            
        Returns:
            Project response if user has access
        """
        project = await self._get_project_with_access_check(db, project_id, user_id)
        if not project:
            return None
        
        return ProjectResponse.model_validate(project)
    
    async def update_project(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int, 
        project_data: ProjectUpdate
    ) -> Optional[ProjectResponse]:
        """
        Update project information.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID (must be owner or collaborator)
            project_data: Updated project data
            
        Returns:
            Updated project response
        """
        project = await self._get_project_with_access_check(
            db, project_id, user_id, require_write=True
        )
        if not project:
            return None
        
        # Update fields
        update_data = project_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(project, field, value)
            
            project.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(project)
        
        return ProjectResponse.model_validate(project)
    
    async def delete_project(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> bool:
        """
        Delete project (owner only).
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID (must be owner)
            
        Returns:
            True if project was deleted
        """
        # Check if user is owner
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.owner_id == user_id
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if project:
            await db.delete(project)
            await db.commit()
            return True
        
        return False
    
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
            Paginated project list
        """
        # Projects owned by user or where user is collaborator
        query = select(Project).options(
            selectinload(Project.tasks),
            selectinload(Project.collaborators)
        ).where(
            or_(
                Project.owner_id == user_id,
                Project.collaborators.any(ProjectCollaborator.user_id == user_id)
            )
        ).order_by(desc(Project.updated_at))
        
        # Count total
        count_query = select(func.count(Project.id)).where(
            or_(
                Project.owner_id == user_id,
                Project.collaborators.any(ProjectCollaborator.user_id == user_id)
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        project_responses = [ProjectResponse.model_validate(p) for p in projects]
        
        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
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
            Filtered project list
        """
        query = select(Project).options(
            selectinload(Project.tasks),
            selectinload(Project.collaborators)
        )
        
        # Base access control
        access_condition = or_(
            Project.owner_id == user_id,
            Project.collaborators.any(ProjectCollaborator.user_id == user_id)
        )
        
        conditions = [access_condition]
        
        # Apply search filters
        if search_params.query:
            search_term = f"%{search_params.query}%"
            conditions.append(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term)
                )
            )
        
        if search_params.status:
            conditions.append(Project.status == search_params.status)
        
        if search_params.priority:
            conditions.append(Project.priority == search_params.priority)
        
        if search_params.category:
            conditions.append(Project.category == search_params.category)
        
        if search_params.tags:
            # Check if any of the search tags exist in project tags
            tag_conditions = []
            for tag in search_params.tags:
                tag_conditions.append(Project.tags.contains([tag]))
            if tag_conditions:
                conditions.append(or_(*tag_conditions))
        
        if search_params.date_from:
            conditions.append(Project.created_at >= search_params.date_from)
        
        if search_params.date_to:
            conditions.append(Project.created_at <= search_params.date_to)
        
        query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count(Project.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(Project.updated_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        projects = result.scalars().all()
        
        project_responses = [ProjectResponse.model_validate(p) for p in projects]
        
        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    # Task Management
    
    async def create_task(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int, 
        task_data: ProjectTaskCreate
    ) -> Optional[ProjectTaskResponse]:
        """
        Create a new task in project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            task_data: Task creation data
            
        Returns:
            Created task response
        """
        # Check project access
        project = await self._get_project_with_access_check(
            db, project_id, user_id, require_write=True
        )
        if not project:
            return None
        
        db_task = ProjectTask(
            project_id=project_id,
            created_by=user_id,
            **task_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
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
        Update project task.
        
        Args:
            db: Database session
            task_id: Task ID
            user_id: User ID
            task_data: Updated task data
            
        Returns:
            Updated task response
        """
        # Get task with project access check
        result = await db.execute(
            select(ProjectTask)
            .join(Project)
            .where(ProjectTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # Check project access
        project_access = await self._check_project_access(
            db, task.project_id, user_id, require_write=True
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
        Get all tasks for a project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            
        Returns:
            List of project tasks
        """
        # Check project access
        if not await self._check_project_access(db, project_id, user_id):
            return []
        
        result = await db.execute(
            select(ProjectTask)
            .where(ProjectTask.project_id == project_id)
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
        Create AI coaching session for project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            session_data: Session data
            
        Returns:
            Created AI coaching session
        """
        # Check project access
        if not await self._check_project_access(db, project_id, user_id):
            return None
        
        db_session = AICoachingSession(
            project_id=project_id,
            user_id=user_id,
            **session_data.model_dump(),
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
        Get AI coaching sessions for project.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            
        Returns:
            List of AI coaching sessions
        """
        # Check project access
        if not await self._check_project_access(db, project_id, user_id):
            return []
        
        result = await db.execute(
            select(AICoachingSession)
            .where(AICoachingSession.project_id == project_id)
            .order_by(desc(AICoachingSession.created_at))
        )
        sessions = result.scalars().all()
        
        return [AICoachingSessionResponse.model_validate(session) for session in sessions]
    
    # Project Analytics
    
    async def get_project_analytics(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int
    ) -> Optional[ProjectAnalyticsResponse]:
        """
        Get project analytics and statistics.
        
        Args:
            db: Database session
            project_id: Project ID
            user_id: User ID
            
        Returns:
            Project analytics data
        """
        # Check project access
        if not await self._check_project_access(db, project_id, user_id):
            return None
        
        # Get project with tasks
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # Calculate analytics
        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.status == "completed"])
        in_progress_tasks = len([t for t in project.tasks if t.status == "in_progress"])
        pending_tasks = len([t for t in project.tasks if t.status == "pending"])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate project duration
        project_duration = None
        if project.end_date and project.start_date:
            project_duration = (project.end_date - project.start_date).days
        
        return ProjectAnalyticsResponse(
            project_id=project_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            pending_tasks=pending_tasks,
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
        owner_id: int, 
        collaborator_data: ProjectCollaboratorCreate
    ) -> Optional[ProjectCollaboratorResponse]:
        """
        Add collaborator to project (owner only).
        
        Args:
            db: Database session
            project_id: Project ID
            owner_id: Project owner ID
            collaborator_data: Collaborator data
            
        Returns:
            Created collaborator response
        """
        # Check if user is project owner
        result = await db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.owner_id == owner_id
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # Check if user is already a collaborator
        existing = await db.execute(
            select(ProjectCollaborator).where(
                and_(
                    ProjectCollaborator.project_id == project_id,
                    ProjectCollaborator.user_id == collaborator_data.user_id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("User is already a collaborator on this project")
        
        db_collaborator = ProjectCollaborator(
            project_id=project_id,
            **collaborator_data.model_dump(),
            added_at=datetime.utcnow()
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
    ) -> Optional[Project]:
        """Get project with access control."""
        result = await db.execute(
            select(Project)
            .options(
                selectinload(Project.tasks),
                selectinload(Project.collaborators)
            )
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        # Check access
        has_access = await self._check_project_access(
            db, project_id, user_id, require_write
        )
        
        return project if has_access else None
    
    async def _check_project_access(
        self, 
        db: AsyncSession, 
        project_id: int, 
        user_id: int,
        require_write: bool = False
    ) -> bool:
        """Check if user has access to project."""
        result = await db.execute(
            select(Project)
            .outerjoin(ProjectCollaborator)
            .where(
                and_(
                    Project.id == project_id,
                    or_(
                        Project.owner_id == user_id,
                        ProjectCollaborator.user_id == user_id
                    )
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return False
        
        # If write access required, check permissions
        if require_write:
            # Owner always has write access
            if project.owner_id == user_id:
                return True
            
            # Check collaborator permissions
            collab_result = await db.execute(
                select(ProjectCollaborator).where(
                    and_(
                        ProjectCollaborator.project_id == project_id,
                        ProjectCollaborator.user_id == user_id,
                        ProjectCollaborator.permission_level.in_(["editor", "admin"])
                    )
                )
            )
            return collab_result.scalar_one_or_none() is not None
        
        return True


# Global project service instance
project_service = ProjectService()