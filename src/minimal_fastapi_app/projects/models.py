from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    pass

# Only SQLAlchemy model and association table here. No Pydantic schemas.


# Association table for many-to-many relationship
user_project_association = Table(
    "user_project_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
)


class ProjectORM(Base):
    """
    SQLAlchemy ORM for projects table.
    - Project name is unique.
    - Linked to users via user_project_association (many-to-many).
    - created_at is set on creation.
    """

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    users = relationship(
        "UserORM",
        secondary="user_project_association",
        back_populates="projects",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectORM(id={self.id}, name={self.name!r})>"
