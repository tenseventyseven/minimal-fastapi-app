# Project service for minimal_fastapi_app
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from minimal_fastapi_app.core.db import get_async_session
from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.projects.models import ProjectORM
from minimal_fastapi_app.projects.schemas import ProjectCreate, ProjectInDB
from minimal_fastapi_app.users.models import UserORM

logger = get_logger(__name__)


class ProjectService:
    def __init__(self):
        self.async_session_factory = get_async_session()

    async def create_project(self, project_data: ProjectCreate) -> ProjectInDB:
        logger.debug(
            "Attempting to create project",
            project_data=project_data.model_dump(),
        )
        async with self.async_session_factory() as session:
            # Check for duplicate name
            existing = await session.execute(
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
            )
            session.add(project)
            try:
                await session.commit()
                await session.refresh(project)
                logger.info(
                    "Project created successfully",
                    project_id=project.id,
                )
            except IntegrityError:
                await session.rollback()
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
        logger.debug("Fetching project by ID", project_id=project_id)
        async with self.async_session_factory() as session:
            result = await session.execute(
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
        logger.debug(
            "Fetching projects with pagination",
            skip=skip,
            limit=limit,
        )
        async with self.async_session_factory() as session:
            total_result = await session.execute(select(ProjectORM))
            total = len(total_result.scalars().all())
            result = await session.execute(select(ProjectORM).offset(skip).limit(limit))
            projects = result.scalars().all()
            logger.info("Projects fetched", count=len(projects))
            return [ProjectInDB.model_validate(p) for p in projects], total

    async def add_user_to_project(self, user_id: int, project_id: int) -> None:
        logger.debug(
            "Adding user to project",
            user_id=user_id,
            project_id=project_id,
        )
        async with self.async_session_factory() as session:
            user = await session.get(UserORM, user_id)
            project = await session.get(ProjectORM, project_id)
            if not user or not project:
                logger.error(
                    "User or project not found for association",
                    user_id=user_id,
                    project_id=project_id,
                )
                raise BusinessException(message="User or Project not found", details=[])
            if project not in user.projects:
                user.projects.append(project)
                await session.commit()
                logger.info(
                    "User added to project",
                    user_id=user_id,
                    project_id=project_id,
                )

    async def remove_user_from_project(self, user_id: int, project_id: int) -> None:
        logger.debug(
            "Removing user from project",
            user_id=user_id,
            project_id=project_id,
        )
        async with self.async_session_factory() as session:
            user = await session.get(UserORM, user_id)
            project = await session.get(ProjectORM, project_id)
            if not user or not project:
                logger.error(
                    "User or project not found for removal",
                    user_id=user_id,
                    project_id=project_id,
                )
                raise BusinessException(message="User or Project not found", details=[])
            if project in user.projects:
                user.projects.remove(project)
                await session.commit()
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
