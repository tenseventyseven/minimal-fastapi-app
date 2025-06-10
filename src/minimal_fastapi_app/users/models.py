from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from minimal_fastapi_app.core.db import Base

if TYPE_CHECKING:
    pass


class UserORM(Base):
    """
    SQLAlchemy ORM for users table.
    - Email is unique and indexed.
    - Linked to projects via user_project_association (many-to-many).
    - created_at is set on creation.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    projects = relationship(
        "ProjectORM",
        secondary="user_project_association",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserORM(id={self.id}, name={self.name!r}, email={self.email!r})>"
