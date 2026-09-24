from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship(
        "User",
        secondary="user_permissions",
        back_populates="permissions"
    )