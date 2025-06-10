from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    # For static type checking only.
    pass


class UserORM(Base):
    """
    SQLAlchemy ORM for users table.
    - Email is unique and indexed.
    - Linked to projects via user_project_association (many-to-many).
    - created_at is set on creation.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    given_name: Mapped[str] = mapped_column(String, nullable=False)
    family_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    projects = relationship(
        "ProjectORM",
        secondary="user_project_association",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<UserORM(id={self.id}, given_name={self.given_name!r}, "
            f"family_name={self.family_name!r}, email={self.email!r})>"
        )
