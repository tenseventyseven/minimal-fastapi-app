from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minimal_fastapi_app.core.association_tables import user_project_association
from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    from minimal_fastapi_app.users.models import UserORM  # noqa: F401


class ProjectORM(Base):
    """
    SQLAlchemy ORM for projects table.
    - project_id is unique (string, indexed).
    - Linked to users via user_project_association (many-to-many).
    - created_at is set on creation.
    - updated_at is set on update.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    users: Mapped[list["UserORM"]] = relationship(
        secondary=user_project_association,
        back_populates="projects",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectORM(id={self.id}, project_id={self.project_id!r})>"
