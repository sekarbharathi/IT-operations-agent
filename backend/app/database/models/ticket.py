from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey

from app.database.connection import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True)
    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )