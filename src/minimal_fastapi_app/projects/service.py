# Project service for minimal_fastapi_app
from datetime import datetime

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from minimal_fastapi_app.core.db import get_db_session
from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.projects.models import ProjectORM
from minimal_fastapi_app.projects.schemas import (
    ProjectCreate,
    ProjectInDB,
    ProjectUpdate,
)
from minimal_fastapi_app.users.models import UserORM

logger = get_logger(__name__)


class ProjectService:
    """Service layer for project operations using SQLAlchemy async ORM."""

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db

    async def create_project(self, project_data: ProjectCreate) -> ProjectInDB:
        """
        Create a new project in the database.
        Checks for duplicate project name before creation.
        Raises BusinessException if name already exists.
        """
        logger.debug(
            "Attempting to create project",
            project_data=project_data.model_dump(),
        )
        # Check for duplicate name to enforce uniqueness constraint
        existing = await self.db.execute(
            select(ProjectORM).where(ProjectORM.name == project_data.name)
        )
        if existing.scalar_one_or_none():
            raise BusinessException(
                message="A project with this name already exists",
                details=[
                    {
                        "field": "name",
                        "message": "Project name is already in use",
                        "code": "name_exists",
                    }
                ],
            )
        project = ProjectORM(
            name=project_data.name,
            description=project_data.description,
            created_at=datetime.now(),
            updated_at=datetime.now(),  # NEW
        )
        self.db.add(project)
        try:
            await self.db.commit()
            await self.db.refresh(project)
            logger.info(
                "Project created successfully",
                project_id=project.id,
            )
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Failed to create project due to duplicate name",
                name=project_data.name,
            )
            raise BusinessException(
                message="A project with this name already exists",
                details=[
                    {
                        "field": "name",
                        "message": "Project name is already in use",
                        "code": "name_exists",
                    }
                ],
            )
        return ProjectInDB.model_validate(project)

    async def get_project_by_id(self, project_id: int) -> ProjectInDB:
        """
        Retrieve a project by its unique ID.
        Raises BusinessException if project is not found.
        """
        logger.debug("Fetching project by ID", project_id=project_id)
        result = await self.db.execute(
            select(ProjectORM).where(ProjectORM.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            logger.error(
                "Project not found",
                project_id=project_id,
            )
            raise BusinessException(
                message=f"Project with id '{project_id}' not found",
                details=[],
            )
        logger.info("Project fetched successfully", project_id=project.id)
        return ProjectInDB.model_validate(project)

    async def get_projects(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProjectInDB], int]:
        """
        Retrieve a paginated list of projects and the total count.
        Useful for API pagination endpoints.
        """
        logger.debug(
            "Fetching projects with pagination",
            skip=skip,
            limit=limit,
        )
        total = await self.db.scalar(select(func.count()).select_from(ProjectORM))
        result = await self.db.execute(select(ProjectORM).offset(skip).limit(limit))
        projects = result.scalars().all()
        logger.info("Projects fetched", count=len(projects))
        return [ProjectInDB.model_validate(p) for p in projects], int(total or 0)

    async def add_user_to_project(self, user_id: int, project_id: int) -> None:
        """
        Add a user to a project (many-to-many relationship).
        Raises BusinessException if user or project not found.
        """
        logger.debug(
            "Adding user to project",
            user_id=user_id,
            project_id=project_id,
        )
        user = await self.db.get(UserORM, user_id)
        project = await self.db.get(ProjectORM, project_id)
        if not user or not project:
            logger.error(
                "User or project not found for association",
                user_id=user_id,
                project_id=project_id,
            )
            raise BusinessException(message="User or Project not found", details=[])
        if project not in user.projects:
            user.projects.append(project)
            await self.db.commit()
            logger.info(
                "User added to project",
                user_id=user_id,
                project_id=project_id,
            )

    async def remove_user_from_project(self, user_id: int, project_id: int) -> None:
        """
        Remove a user from a project (many-to-many relationship).
        Raises BusinessException if user or project not found.
        """
        logger.debug(
            "Removing user from project",
            user_id=user_id,
            project_id=project_id,
        )
        user = await self.db.get(UserORM, user_id)
        project = await self.db.get(ProjectORM, project_id)
        if not user or not project:
            logger.error(
                "User or project not found for removal",
                user_id=user_id,
                project_id=project_id,
            )
            raise BusinessException(message="User or Project not found", details=[])
        if project in user.projects:
            user.projects.remove(project)
            await self.db.commit()
            logger.info(
                "User removed from project",
                user_id=user_id,
                project_id=project_id,
            )
        else:
            logger.warning(
                "User is not in project",
                user_id=user_id,
                project_id=project_id,
            )
            raise BusinessException(message="User is not in project", details=[])

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> ProjectInDB:
        """
        Update an existing project's information by ID.
        Raises BusinessException if project not found or name is duplicate.
        """
        logger.debug(
            "Attempting to update project",
            project_id=project_id,
            project_data=project_data.model_dump(exclude_unset=True),
        )
        result = await self.db.execute(
            select(ProjectORM).where(ProjectORM.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            logger.error(
                "Project not found for update",
                project_id=project_id,
            )
            raise BusinessException(
                message=f"Project with id '{project_id}' not found",
                details=[],
            )
        update_data = project_data.model_dump(exclude_unset=True)
        # Check for duplicate name (excluding self)
        if "name" in update_data:
            existing = await self.db.execute(
                select(ProjectORM).where(
                    (ProjectORM.name == update_data["name"])
                    & (ProjectORM.id != project_id)
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(
                    "Failed to update project due to duplicate name",
                    name=update_data["name"],
                )
                raise BusinessException(
                    message="A project with this name already exists",
                    details=[
                        {
                            "field": "name",
                            "message": "Project name is already in use",
                            "code": "name_exists",
                        }
                    ],
                )
        for field, value in update_data.items():
            object.__setattr__(project, field, value)
        # always update timestamp
        object.__setattr__(project, "updated_at", datetime.now())
        try:
            await self.db.commit()
            await self.db.refresh(project)
            logger.info(
                "Project updated successfully",
                project_id=project.id,
            )
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Failed to update project due to duplicate name",
                name=update_data.get("name"),
            )
            raise BusinessException(
                message="A project with this name already exists",
                details=[
                    {
                        "field": "name",
                        "message": "Project name is already in use",
                        "code": "name_exists",
                    }
                ],
            )
        return ProjectInDB.model_validate(project)

    async def delete_project(self, project_id: int) -> None:
        """
        Delete a project by its unique ID.
        Raises BusinessException if project not found.
        """
        logger.debug("Attempting to delete project", project_id=project_id)
        result = await self.db.execute(
            select(ProjectORM).where(ProjectORM.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            logger.error(
                "Project not found for deletion",
                project_id=project_id,
            )
            raise BusinessException(
                message=f"Project with id '{project_id}' not found",
                details=[],
            )
        await self.db.delete(project)
        await self.db.commit()
        logger.info("Project deleted successfully", project_id=project_id)
