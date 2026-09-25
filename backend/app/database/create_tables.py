from app.database.connection import Base, engine

from app.database.models import (
    User,
    Permission,
    UserPermission,
    Incident,
    Ticket,
    Conversation,
    ConversationMessage,
)


Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")