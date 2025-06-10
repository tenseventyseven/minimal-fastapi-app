from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from minimal_fastapi_app.core.db import get_db_session
from minimal_fastapi_app.core.exceptions import BusinessException, enrich_log_fields
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.projects.models import ProjectORM
from minimal_fastapi_app.projects.schemas import Project, ProjectCreate
from minimal_fastapi_app.projects.service import ProjectService
from minimal_fastapi_app.users.models import UserORM
from minimal_fastapi_app.users.schemas import User

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1/projects",
    tags=["projects"],
    responses={
        404: {"description": "Project not found."},
        400: {"description": "Validation or business logic error."},
    },
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
    summary="Create Project",
    operation_id="createProject",
    responses={
        201: {"description": "Project created successfully."},
        400: {"description": "Duplicate name or validation error."},
    },
)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    logger.info(
        "Create project endpoint called",
        **enrich_log_fields({"project_name": project_data.name}, request),
    )
    project_service = ProjectService(db)
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
    summary="List Projects",
    operation_id="listProjects",
    responses={
        200: {"description": "Paginated list of projects."},
    },
)
async def get_projects(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of projects to return"),
    db: AsyncSession = Depends(get_db_session),
) -> PaginatedProjectsResponse:
    logger.info(
        "Get projects endpoint called",
        **enrich_log_fields({"skip": skip, "limit": limit}, request),
    )
    project_service = ProjectService(db)
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
    summary="Get Project",
    operation_id="getProject",
    responses={
        200: {"description": "Project found."},
        404: {"description": "Project not found."},
    },
)
async def get_project(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    logger.info(
        "Get project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService(db)
    try:
        project = await project_service.get_project_by_id(project_id)
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "Get project endpoint completed",
        **enrich_log_fields({"project_id": project.id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=Project,
    tags=["projects"],
    description="Update a project by ID.",
    summary="Update Project",
    operation_id="updateProject",
    responses={
        200: {"description": "Project updated successfully."},
        400: {"description": "Duplicate name or validation error."},
        404: {"description": "Project not found."},
    },
)
async def update_project(
    project_id: int,
    project_data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    logger.info(
        "Update project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService(db)
    try:
        project = await project_service.update_project(project_id, project_data)
        logger.info(
            "Project updated",
            **enrich_log_fields({"project_id": project_id}, request, user_id=None),
        )
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    return Project.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=204,
    tags=["projects"],
    description="Delete a project by ID.",
    summary="Delete Project",
    operation_id="deleteProject",
    responses={
        204: {"description": "Project deleted successfully."},
        404: {"description": "Project not found."},
    },
)
async def delete_project(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    logger.info(
        "Delete project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService(db)
    try:
        await project_service.delete_project(project_id)
        logger.info(
            "Project deleted",
            **enrich_log_fields({"project_id": project_id}, request, user_id=None),
        )
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post(
    "/{project_id}/users/{user_id}",
    status_code=204,
    tags=["projects"],
    description="Add a user to a project.",
)
async def add_user_to_project(
    project_id: int,
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    logger.info(
        "Add user to project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService(db)
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
    project_id: int,
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    logger.info(
        "Remove user from project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService(db)
    try:
        await project_service.remove_user_from_project(user_id, project_id)
    except BusinessException as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    logger.info(
        "User removed from project",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )


@router.get(
    "/{project_id}/users",
    tags=["projects"],
    description="List users in a project.",
)
async def list_users_in_project(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    logger.info(
        "List users in project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request),
    )
    db_project = await db.get(ProjectORM, project_id)
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
async def list_projects_for_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    logger.info(
        "List projects for user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request),
    )
    user = await db.get(UserORM, user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail=f"User with id '{user_id}' not found"
        )
    projects = user.projects
    return [Project.model_validate(p) for p in projects]
