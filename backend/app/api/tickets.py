from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"]
)


tickets = {}


class TicketCreate(BaseModel):
    user_id: str
    category: str
    description: str

@router.get("")
def get_tickets():
    return list(tickets.values())

@router.post("")
def create_ticket(ticket: TicketCreate):

    if not ticket.user_id:
        raise HTTPException(
            status_code=400,
            detail="User ID is required"
        )

    ticket_id = f"ticket_{len(tickets) + 1:03d}"

    new_ticket = {
        "id": ticket_id,
        "user_id": ticket.user_id,
        "category": ticket.category,
        "description": ticket.description,
        "status": "open"
    }

    tickets[ticket_id] = new_ticket

    return new_ticket


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str):

    ticket = tickets.get(ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return ticket