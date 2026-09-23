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
def get_ticket(
    ticket_id: str,
    requester_id: str
):
    ticket = tickets.get(ticket_id)

    if not ticket:
        return {
            "success": False,
            "error": "Ticket not found"
        }

    requester = users.get(requester_id)

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    ticket_owner = users.get(ticket["user_id"])

    if not ticket_owner:
        return {
            "success": False,
            "error": "Ticket owner not found"
        }

    # Admin can view any ticket
    if requester["role"] == "admin":
        return {
            "success": True,
            "ticket": ticket
        }

    # Manager can view tickets from their own team
    if requester["role"] == "manager":

        if requester["team"] != ticket_owner["team"]:
            return {
                "success": False,
                "error": "Managers can only view tickets from their own team"
            }

        return {
            "success": True,
            "ticket": ticket
        }

    # Employee can only view their own tickets
    if requester["role"] == "employee":

        if requester["id"] != ticket["user_id"]:
            return {
                "success": False,
                "error": "Employees can only view their own tickets"
            }

        return {
            "success": True,
            "ticket": ticket
        }