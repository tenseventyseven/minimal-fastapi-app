from sqlalchemy import Column, ForeignKey, Integer, Table

from minimal_fastapi_app.core.db import Base

user_project_association = Table(
    "user_project_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
)
