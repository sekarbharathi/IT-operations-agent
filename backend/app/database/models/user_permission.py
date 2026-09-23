from sqlalchemy import Column, String, ForeignKey

from app.database.connection import Base


class UserPermission(Base):
    __tablename__ = "user_permissions"

    user_id = Column(
        String,
        ForeignKey("users.id"),
        primary_key=True
    )

    permission_id = Column(
        String,
        ForeignKey("permissions.id"),
        primary_key=True
    )