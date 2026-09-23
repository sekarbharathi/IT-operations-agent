from sqlalchemy import Column, String

from app.database.connection import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)