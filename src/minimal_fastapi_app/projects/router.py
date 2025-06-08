from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from minimal_fastapi_app.core.exceptions import BusinessException, enrich_log_fields
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.projects.models import Project, ProjectCreate, ProjectORM
from minimal_fastapi_app.projects.service import ProjectService
from minimal_fastapi_app.users.models import User, UserORM

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1/projects",
    tags=["projects"],
)


class PaginatedProjectsResponse(BaseModel):
    items: list[Project]
    total: int
    limit: int
    skip: int


@router.post(
    "/",
    response_model=Project,
    status_code=201,
    tags=["projects"],
    description="Create a new project.",
)
async def create_project(project_data: ProjectCreate, request: Request) -> Project:
    logger.info(
        "Create project endpoint called",
        **enrich_log_fields({"project_name": project_data.name}, request),
    )
    project_service = ProjectService()
    try:
        project = await project_service.create_project(project_data)
    except BusinessException as exc:
        raise exc
    logger.info(
        "Project creation endpoint completed",
        **enrich_log_fields({"project_id": project.id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.get(
    "/",
    response_model=PaginatedProjectsResponse,
    tags=["projects"],
    description="Get all projects with pagination.",
)
async def get_projects(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of projects to return"),
) -> PaginatedProjectsResponse:
    logger.info(
        "Get projects endpoint called",
        **enrich_log_fields({"skip": skip, "limit": limit}, request),
    )
    project_service = ProjectService()
    projects, total = await project_service.get_projects(skip=skip, limit=limit)
    project_responses = [Project.model_validate(project) for project in projects]
    logger.info(
        "Get projects endpoint completed",
        **enrich_log_fields({"returned_count": len(projects)}, request),
    )
    return PaginatedProjectsResponse(
        items=project_responses,
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/{project_id}",
    response_model=Project,
    tags=["projects"],
    description="Get a specific project by ID.",
)
async def get_project(project_id: int, request: Request) -> Project:
    logger.info(
        "Get project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService()
    try:
        project = await project_service.get_project_by_id(project_id)
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "Get project endpoint completed",
        **enrich_log_fields({"project_id": project.id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.post(
    "/{project_id}/users/{user_id}",
    status_code=204,
    tags=["projects"],
    description="Add a user to a project.",
)
async def add_user_to_project(project_id: int, user_id: int, request: Request) -> None:
    logger.info(
        "Add user to project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService()
    try:
        await project_service.add_user_to_project(user_id, project_id)
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "User added to project",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )


@router.delete(
    "/{project_id}/users/{user_id}",
    status_code=204,
    tags=["projects"],
    description="Remove a user from a project.",
)
async def remove_user_from_project(
    project_id: int, user_id: int, request: Request
) -> None:
    logger.info(
        "Remove user from project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService()
    try:
        await project_service.remove_user_from_project(user_id, project_id)
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "User removed from project",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )


@router.get(
    "/{project_id}/users", tags=["projects"], description="List users in a project."
)
async def list_users_in_project(project_id: int, request: Request):
    logger.info(
        "List users in project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request),
    )
    project_service = ProjectService()
    async with project_service.async_session_factory() as session:
        db_project = await session.get(ProjectORM, project_id)
        if not db_project:
            raise HTTPException(
                status_code=404, detail=f"Project with id '{project_id}' not found"
            )
        users = db_project.users
        return [User.model_validate(u) for u in users]


@router.get(
    "/user/{user_id}/projects",
    tags=["projects"],
    description="List projects for a user.",
)
async def list_projects_for_user(user_id: int, request: Request):
    logger.info(
        "List projects for user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request),
    )
    project_service = ProjectService()
    async with project_service.async_session_factory() as session:
        user = await session.get(UserORM, user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id '{user_id}' not found"
            )
        projects = user.projects
        from minimal_fastapi_app.projects.models import Project

        return [Project.model_validate(p) for p in projects]
