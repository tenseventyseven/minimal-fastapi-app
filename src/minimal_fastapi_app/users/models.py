from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from minimal_fastapi_app.core.db import Base


class UserORM(Base):
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
