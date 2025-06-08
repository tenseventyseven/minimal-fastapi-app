# Project service for minimal_fastapi_app
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from minimal_fastapi_app.core.db import get_async_session
from minimal_fastapi_app.core.exceptions import BusinessException
from minimal_fastapi_app.projects.models import ProjectCreate, ProjectInDB, ProjectORM
from minimal_fastapi_app.users.models import UserORM


class ProjectService:
    def __init__(self):
        self.async_session_factory = get_async_session()

    async def create_project(self, project_data: ProjectCreate) -> ProjectInDB:
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
            except IntegrityError:
                await session.rollback()
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
        async with self.async_session_factory() as session:
            result = await session.execute(
                select(ProjectORM).where(ProjectORM.id == project_id)
            )
            project = result.scalar_one_or_none()
            if not project:
                raise BusinessException(
                    message=f"Project with id '{project_id}' not found",
                    details=[],
                )
            return ProjectInDB.model_validate(project)

    async def get_projects(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProjectInDB], int]:
        async with self.async_session_factory() as session:
            total_result = await session.execute(select(ProjectORM))
            total = len(total_result.scalars().all())
            result = await session.execute(select(ProjectORM).offset(skip).limit(limit))
            projects = result.scalars().all()
            return [ProjectInDB.model_validate(p) for p in projects], total

    async def add_user_to_project(self, user_id: int, project_id: int) -> None:
        async with self.async_session_factory() as session:
            user = await session.get(UserORM, user_id)
            project = await session.get(ProjectORM, project_id)
            if not user or not project:
                raise BusinessException(message="User or Project not found", details=[])
            if project not in user.projects:
                user.projects.append(project)
                await session.commit()

    async def remove_user_from_project(self, user_id: int, project_id: int) -> None:
        async with self.async_session_factory() as session:
            user = await session.get(UserORM, user_id)
            project = await session.get(ProjectORM, project_id)
            if not user or not project:
                raise BusinessException(message="User or Project not found", details=[])
            if project in user.projects:
                user.projects.remove(project)
                await session.commit()
            else:
                raise BusinessException(message="User is not in project", details=[])
