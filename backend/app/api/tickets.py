from fastapi import APIRouter
from pydantic import BaseModel

from app.api.users import users


router = APIRouter()

tickets = {}


class TicketCreate(BaseModel):
    user_id: str
    category: str
    description: str


@router.post("/api/tickets")
def create_ticket(ticket: TicketCreate):

    # Check that the user exists
    user = users.get(ticket.user_id)

    if not user:
        return {
            "success": False,
            "error": "User not found"
        }

    # Backend authorization check
    if "ticket.create" not in user["permissions"]:
        return {
            "success": False,
            "error": "User does not have permission to create tickets"
        }

    ticket_id = f"ticket_{len(tickets) + 1:03d}"

    new_ticket = {
        "id": ticket_id,
        "user_id": ticket.user_id,
        "category": ticket.category,
        "description": ticket.description,
        "status": "open"
    }

    tickets[ticket_id] = new_ticket

    return {
        "success": True,
        "ticket": new_ticket
    }


@router.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):

    ticket = tickets.get(ticket_id)

    if not ticket:
        return {
            "success": False,
            "error": "Ticket not found"
        }

    return ticket