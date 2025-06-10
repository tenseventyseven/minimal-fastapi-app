from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minimal_fastapi_app.association_tables import user_project_association
from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    from minimal_fastapi_app.users.models import UserORM  # noqa: F401


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
    users: Mapped[list["UserORM"]] = relationship(
        secondary=user_project_association,
        back_populates="projects",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ProjectORM(id={self.id}, name={self.name!r})>"
