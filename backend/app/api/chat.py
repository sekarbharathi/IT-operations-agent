import uuid

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models.conversation import Conversation, ConversationMessage

from app.services.langgraph_agent import (
    agent,
    SYSTEM_PROMPT,
    CURRENT_USER_ID
)


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def save_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str
):
    message = ConversationMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)


@router.post("")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------
    # 1. Get or create conversation
    # --------------------------------------------------

    conversation_id = request.conversation_id

    if conversation_id:

        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == CURRENT_USER_ID
            )
            .first()
        )

        if not conversation:
            return {
                "success": False,
                "error": "Conversation not found"
            }

    else:

        conversation_id = str(uuid.uuid4())

        conversation = Conversation(
            id=conversation_id,
            user_id=CURRENT_USER_ID
        )

        db.add(conversation)
        db.flush()

    # --------------------------------------------------
    # 2. Load conversation history
    # --------------------------------------------------

    conversation_messages = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id
        )
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )

    # System prompt is internal and is NOT stored
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(
        {
            "role": message.role,
            "content": message.content
        }
        for message in conversation_messages
    )

    # --------------------------------------------------
    # 3. Save new user message
    # --------------------------------------------------

    save_message(
        db,
        conversation_id,
        "user",
        request.message
    )

    messages.append({
        "role": "user",
        "content": request.message
    })

    # --------------------------------------------------
    # 4. Run LangGraph
    # --------------------------------------------------

    result = agent.invoke(
        {
            "messages": messages,
            "user_id": CURRENT_USER_ID
        }
    )

    # --------------------------------------------------
    # 5. Get latest assistant response
    # --------------------------------------------------

    assistant_messages = [
        message
        for message in result["messages"]
        if message.get("role") == "assistant"
        and message.get("content")
    ]

    answer = assistant_messages[-1].get("content", "")

    # --------------------------------------------------
    # 6. Save assistant response
    # --------------------------------------------------

    save_message(
        db,
        conversation_id,
        "assistant",
        answer
    )

    # --------------------------------------------------
    # 7. Update conversation timestamp
    # --------------------------------------------------

    conversation.updated_at = datetime.utcnow()

    # --------------------------------------------------
    # 8. Commit everything
    # --------------------------------------------------

    db.commit()

    return {
        "success": True,
        "conversation_id": conversation_id,
        "user_id": CURRENT_USER_ID,
        "response": answer
    }