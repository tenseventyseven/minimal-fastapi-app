from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minimal_fastapi_app.core.db import get_db_session
from minimal_fastapi_app.core.exceptions import BusinessException, enrich_log_fields
from minimal_fastapi_app.core.logging import get_logger
from minimal_fastapi_app.projects.models import ProjectORM
from minimal_fastapi_app.projects.schemas import Project, ProjectCreate, ProjectUpdate
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
    """
    Paginated response model for projects list API.

    Attributes:
        items (list[Project]): List of project objects.
        total (int): Total number of projects available.
        limit (int): Number of projects returned in this page.
        skip (int): Number of projects skipped (offset).
    """
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
        400: {"description": "Duplicate project_id or validation error."},
    },
)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    """Create a new project and return the created project object.

    Args:
        project_data (ProjectCreate): The project creation payload.
        request (Request): The incoming HTTP request.

    Returns:
        Project: The created project object.
    """
    logger.info(
        "Create project endpoint called",
        **enrich_log_fields({"project_id": project_data.project_id}, request),
    )
    project_service = ProjectService(db)
    try:
        project = await project_service.create_project(project_data)
    except BusinessException as exc:
        raise HTTPException(status_code=400, detail=exc.message)
    logger.info(
        "Project creation endpoint completed",
        **enrich_log_fields({"project_id": project.project_id}, request, user_id=None),
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
    """Get all projects with pagination and return a paginated response object.

    Args:
        request (Request): The incoming HTTP request.
        skip (int): Number of projects to skip.
        limit (int): Number of projects to return.

    Returns:
        PaginatedProjectsResponse: Paginated list of projects.
    """
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
    description="Get a specific project by project_id.",
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
    """Get a specific project by project_id (int).

    Args:
        project_id (int): The project_id.
        request (Request): The incoming HTTP request.

    Returns:
        Project: The project object if found.

    Raises:
        HTTPException: If project is not found.
    """
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
        **enrich_log_fields({"project_id": project.project_id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=Project,
    tags=["projects"],
    description=(
        "Update a project by project_id. All fields must be provided. "
        "Missing fields will be set to null or default."
    ),
    summary="Update Project",
    operation_id="updateProject",
    responses={
        200: {"description": "Project updated successfully."},
        400: {"description": "Duplicate project_id or validation error."},
        404: {"description": "Project not found."},
        422: {"description": "Validation error: missing required fields."},
    },
)
async def update_project(
    project_id: int,
    project_data: ProjectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    """
    Replace all fields of a project by project_id.

    Args:
        project_id (int): The unique project identifier from the path.
        project_data (ProjectCreate): The new project data (all fields required).
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        Project: The updated project object.

    Raises:
        HTTPException: 422 if any required field is missing,
        404 if project not found,
        400 for business/validation errors.
    """
    logger.info(
        "Update project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    # Ensure all required fields are present for a full update (PUT)
    required_fields = ["project_id"]  # Only project_id is required per schema
    missing_fields = [
        field for field in required_fields if getattr(project_data, field, None) is None
    ]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "message": (
                    f"PUT requires all fields: missing {', '.join(missing_fields)}"
                ),
                "fields": missing_fields,
            },
        )
    project_service = ProjectService(db)
    try:
        project_update = ProjectUpdate(**project_data.model_dump())
        project = await project_service.update_project(project_id, project_update)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "project_id": project_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "Update project endpoint completed",
        **enrich_log_fields({"project_id": project.project_id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=Project,
    tags=["projects"],
    description="Partially update a project by project_id.",
    summary="Patch Project",
    operation_id="patchProject",
    responses={
        200: {"description": "Project updated successfully."},
        400: {"description": "Duplicate project_id or validation error."},
        404: {"description": "Project not found."},
    },
)
async def patch_project(
    project_id: int,
    project_data: ProjectUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Project:
    """
    Partially update a project by project_id.

    Args:
        project_id (int): The unique project identifier from the path.
        project_data (ProjectUpdate): The project update payload (partial; only provided
            fields will be updated).
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        Project: The updated project object.

    Raises:
        HTTPException: 404 if project not found, 400 for business/validation errors.
    """
    logger.info(
        "Patch project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService(db)
    try:
        project = await project_service.update_project(project_id, project_data)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "project_id": project_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "Patch project endpoint completed",
        **enrich_log_fields({"project_id": project.project_id}, request, user_id=None),
    )
    return Project.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=204,
    tags=["projects"],
    description="Delete a project by project_id.",
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
    """
    Delete a project by project_id.

    Args:
        project_id (int): The unique project identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Raises:
        HTTPException: 404 if project not found.
    """
    logger.info(
        "Delete project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )
    project_service = ProjectService(db)
    try:
        await project_service.delete_project(project_id)
    except BusinessException:
        raise HTTPException(
            status_code=404, detail=f"Project with project_id '{project_id}' not found"
        )
    logger.info(
        "Delete project endpoint completed",
        **enrich_log_fields({"project_id": project_id}, request, user_id=None),
    )


@router.post(
    "/{project_id}/users/{user_id}",
    status_code=204,
    tags=["projects"],
    description="Add a user to a project.",
    summary="Add User to Project",
    operation_id="addUserToProject",
    responses={
        204: {"description": "User added to project successfully."},
        404: {"description": "Project or user not found."},
        400: {"description": "Business or validation error."},
    },
)
async def add_user_to_project(
    project_id: int,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Add a user to a project.

    Args:
        project_id (int): The unique project identifier from the path.
        user_id (str): The unique user identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Raises:
        HTTPException: 404 if project or user not found,
            400 for business/validation errors.
    """
    logger.info(
        "Add user to project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService(db)
    try:
        await project_service.add_user_to_project(user_id, project_id)
    except BusinessException as exc:
        if "not found" in exc.message.lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "project_id": project_id,
                    "user_id": user_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "User added to project",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )


@router.delete(
    "/{project_id}/users/{user_id}",
    status_code=204,
    tags=["projects"],
    description="Remove a user from a project.",
    summary="Remove User from Project",
    operation_id="removeUserFromProject",
    responses={
        204: {"description": "User removed from project successfully."},
        404: {"description": "Project or user not found."},
        400: {"description": "Business or validation error."},
    },
)
async def remove_user_from_project(
    project_id: int,
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Remove a user from a project.

    Args:
        project_id (int): The unique project identifier from the path.
        user_id (str): The unique user identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Raises:
        HTTPException: 404 if project or user not found,
            400 for business/validation errors.
    """
    logger.info(
        "Remove user from project endpoint called",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )
    project_service = ProjectService(db)
    try:
        await project_service.remove_user_from_project(user_id, project_id)
    except BusinessException as exc:
        msg = exc.message.lower()
        if "not found" in msg or "not in project" in msg:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": exc.message,
                    "project_id": project_id,
                    "user_id": user_id,
                },
            )
        raise HTTPException(
            status_code=400, detail={"error": "business_error", "message": exc.message}
        )
    logger.info(
        "User removed from project",
        **enrich_log_fields({"project_id": project_id, "user_id": user_id}, request),
    )


@router.get(
    "/{project_id}/users",
    response_model=list[User],
    tags=["projects"],
    description="List users in a project.",
    summary="List Users in Project",
    operation_id="listUsersInProject",
    responses={
        200: {"description": "List of users in the project."},
        404: {"description": "Project not found."},
    },
)
async def list_users_in_project(
    project_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> list[User]:
    """
    List all users in a project.

    Args:
        project_id (int): The unique project identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        list[User]: List of users in the project.

    Raises:
        HTTPException: 404 if project not found.
    """
    logger.info(
        "List users in project endpoint called",
        **enrich_log_fields({"project_id": project_id}, request),
    )
    db_project = await db.get(ProjectORM, project_id)
    if not db_project:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"Project with id '{project_id}' not found",
                "project_id": project_id,
            },
        )
    users = db_project.users
    logger.info(
        "List users in project endpoint completed",
        **enrich_log_fields({
            "project_id": project_id,
            "user_count": len(users)
        }, request),
    )
    return [User.model_validate(u) for u in users]


@router.get(
    "/user/{user_id}/projects",
    response_model=list[Project],
    tags=["projects"],
    description="List projects for a user.",
    summary="List Projects for User",
    operation_id="listProjectsForUser",
    responses={
        200: {"description": "List of projects for the user."},
        404: {"description": "User not found."},
    },
)
async def list_projects_for_user(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> list[Project]:
    """
    List all projects for a user.

    Args:
        user_id (str): The unique user identifier from the path.
        request (Request): The incoming HTTP request.
        db (AsyncSession): The database session dependency.

    Returns:
        list[Project]: List of projects for the user.

    Raises:
        HTTPException: 404 if user not found.
    """
    logger.info(
        "List projects for user endpoint called",
        **enrich_log_fields({"user_id": user_id}, request),
    )
    user_result = await db.execute(select(UserORM).where(UserORM.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"User with user_id '{user_id}' not found",
                "user_id": user_id,
            },
        )
    projects = user.projects
    logger.info(
        "List projects for user endpoint completed",
        **enrich_log_fields({
            "user_id": user_id,
            "project_count": len(projects)
        }, request),
    )
    return [Project.model_validate(p) for p in projects]
