from sqlalchemy import Column, String

from app.database.connection import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    service = Column(String, nullable=False)
    status = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)