from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from minimal_fastapi_app.core.db import Base

# Only SQLAlchemy model and association table here. No Pydantic schemas.


# Association table for many-to-many relationship
user_project_association = Table(
    "user_project_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
)


class ProjectORM(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    users = relationship(
        "UserORM",
        secondary=user_project_association,
        back_populates="projects",
        lazy="selectin",
    )
