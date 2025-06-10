from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    # For static type checking only.
    pass


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

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    users = relationship(
        "UserORM",
        secondary="user_project_association",
        back_populates="projects",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectORM(id={self.id}, name={self.name!r})>"
