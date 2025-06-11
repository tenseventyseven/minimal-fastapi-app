from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
    """
    Service class for project-related business logic and database operations.
    Handles project CRUD and user-project relationships.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the ProjectService with a database session.

        Args:
            db (AsyncSession): The database session.
        """
        self.db = db

    async def create_project(self, project_data: ProjectCreate) -> ProjectInDB:
        """
        Create a new project and return a validated Pydantic schema.
        Checks for duplicate project_id before creation.

        Args:
            project_data (ProjectCreate): The project creation payload.

        Returns:
            ProjectInDB: The created project as a validated Pydantic schema.

        Raises:
            BusinessException: If a project with the same project_id already exists or
                on database error.
        """
        logger.debug(
            "Attempting to create project",
            project_data=project_data.model_dump(),
        )
        # Check for duplicate ID to enforce uniqueness constraint
        existing = await self.db.execute(
            select(ProjectORM).where(ProjectORM.project_id == project_data.project_id)
        )
        if existing.scalar_one_or_none():
            raise BusinessException(
                message="A project with this project_id already exists",
                details=[
                    {
                        "field": "project_id",
                        "message": "Project ID is already in use",
                        "code": "project_id_exists",
                    }
                ],
            )
        project = ProjectORM(
            project_id=project_data.project_id,
            description=project_data.description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
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
                "Failed to create project due to duplicate project_id",
                project_id=project_data.project_id,
            )
            raise BusinessException(
                message="A project with this project_id already exists",
                details=[
                    {
                        "field": "project_id",
                        "message": "Project ID is already in use",
                        "code": "project_id_exists",
                    }
                ],
            )
        return ProjectInDB.model_validate(project)

    async def get_project_by_id(self, project_id: int) -> ProjectInDB:
        """
        Retrieve a project by its unique ID and return as a Pydantic schema.

        Args:
            project_id (int): The unique project identifier.

        Returns:
            ProjectInDB: The project as a validated Pydantic schema.

        Raises:
            BusinessException: If project is not found.
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
        Retrieve a paginated list of projects and the total count as Pydantic schemas.

        Args:
            skip (int): Number of projects to skip.
            limit (int): Number of projects to return.

        Returns:
            tuple[list[ProjectInDB], int]: List of project schemas and total count.
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

    async def update_project(
        self, project_id: int, project_data: ProjectUpdate
    ) -> ProjectInDB:
        """
        Update an existing project's information by ID and return as a Pydantic schema.
        Only provided fields will be updated.

        Args:
            project_id (int): The unique project identifier.
            project_data (ProjectUpdate): The project update payload.

        Returns:
            ProjectInDB: The updated project as a validated Pydantic schema.

        Raises:
            BusinessException: If project not found or project_id is duplicate.
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
        # Check for duplicate ID (excluding self)
        if "project_id" in update_data:
            existing = await self.db.execute(
                select(ProjectORM).where(
                    (ProjectORM.project_id == update_data["project_id"])
                    & (ProjectORM.id != project_id)
                )
            )
            if existing.scalar_one_or_none():
                logger.warning(
                    "Failed to update project due to duplicate project_id",
                    project_id=update_data["project_id"],
                )
                raise BusinessException(
                    message="A project with this project_id already exists",
                    details=[
                        {
                            "field": "project_id",
                            "message": "Project ID is already in use",
                            "code": "project_id_exists",
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
                "Failed to update project due to duplicate project_id",
                project_id=update_data.get("project_id"),
            )
            raise BusinessException(
                message="A project with this project_id already exists",
                details=[
                    {
                        "field": "project_id",
                        "message": "Project ID is already in use",
                        "code": "project_id_exists",
                    }
                ],
            )
        return ProjectInDB.model_validate(project)

    async def delete_project(self, project_id: int) -> None:
        """
        Delete a project by its unique ID.

        Args:
            project_id (int): The unique project identifier.

        Raises:
            BusinessException: If project is not found.
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

    async def add_user_to_project(self, user_id: str, project_id: int) -> None:
        """
        Add a user to a project (many-to-many relationship).

        Args:
            user_id (str): The unique user identifier.
            project_id (int): The unique project identifier.

        Raises:
            BusinessException: If user or project not found.
        """
        logger.debug(
            "Adding user to project",
            user_id=user_id,
            project_id=project_id,
        )
        user = await self.db.execute(select(UserORM).where(UserORM.user_id == user_id))
        user = user.scalar_one_or_none()
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

    async def remove_user_from_project(self, user_id: str, project_id: int) -> None:
        """
        Remove a user from a project (many-to-many relationship).

        Args:
            user_id (str): The unique user identifier.
            project_id (int): The unique project identifier.

        Raises:
            BusinessException: If user or project not found, or user is not in project.
        """
        logger.debug(
            "Removing user from project",
            user_id=user_id,
            project_id=project_id,
        )
        user = await self.db.execute(select(UserORM).where(UserORM.user_id == user_id))
        user = user.scalar_one_or_none()
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
