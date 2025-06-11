from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minimal_fastapi_app.core.association_tables import user_project_association
from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    from minimal_fastapi_app.projects.models import ProjectORM


class UserORM(Base):
    """
    SQLAlchemy ORM for users table.
    - Email and user_id are both unique and both indexed.
    - Linked to projects via user_project_association (many-to-many).
    - created_at is set on creation.
    - updated_at is set on update.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    given_name: Mapped[str] = mapped_column(String, nullable=False)
    family_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    projects: Mapped[list["ProjectORM"]] = relationship(
        secondary=user_project_association,
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<UserORM(id={self.id}, user_id={self.user_id!r}, "
            f"given_name={self.given_name!r}, family_name={self.family_name!r}, "
            f"email={self.email!r})>"
        )
