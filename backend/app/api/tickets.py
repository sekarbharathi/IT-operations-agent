from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Ticket, User

router = APIRouter(tags=["Tickets"])


class TicketCreate(BaseModel):
    user_id: str
    category: str
    description: str


def ticket_to_dict(ticket: Ticket):
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "category": ticket.category,
        "description": ticket.description,
        "status": ticket.status,
        "created_at": ticket.created_at,
    }


@router.post("/api/tickets")
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.id == ticket.user_id)
        .first()
    )

    if not user:
        return {
            "success": False,
            "error": "User not found"
        }

    has_permission = any(
        permission.name == "ticket.create"
        for permission in user.permissions
    )

    if not has_permission:
        return {
            "success": False,
            "error": "User does not have permission to create tickets"
        }

    ticket_count = db.query(Ticket).count()
    ticket_id = f"ticket_{ticket_count + 1:03d}"

    new_ticket = Ticket(
        id=ticket_id,
        user_id=ticket.user_id,
        category=ticket.category,
        description=ticket.description,
        status="open"
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return {
        "success": True,
        "ticket": ticket_to_dict(new_ticket)
    }

@router.get("/api/tickets/team")
def get_team_tickets(
    requester_id: str,
    db: Session = Depends(get_db)
):
    requester = (
        db.query(User)
        .filter(User.id == requester_id)
        .first()
    )

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    if requester.role != "manager":
        return {
            "success": False,
            "error": "Only managers can view team tickets"
        }

    tickets = (
        db.query(Ticket)
        .join(User, Ticket.user_id == User.id)
        .filter(User.team == requester.team)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "tickets": [
            ticket_to_dict(ticket)
            for ticket in tickets
        ]
    }

@router.get("/api/tickets/employee/{employee_id}")
def get_employee_tickets(
    employee_id: str,
    requester_id: str,
    db: Session = Depends(get_db)
):
    requester = (
        db.query(User)
        .filter(User.id == requester_id)
        .first()
    )

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    employee = (
        db.query(User)
        .filter(User.id == employee_id)
        .first()
    )

    if not employee:
        return {
            "success": False,
            "error": "Employee not found"
        }

    # Employee can only view their own tickets
    if requester.role == "employee":
        if requester.id != employee.id:
            return {
                "success": False,
                "error": "Employees can only view their own tickets"
            }

    # Manager can only view employees in their own team
    elif requester.role == "manager":
        if employee.team != requester.team:
            return {
                "success": False,
                "error": "Managers can only view tickets from employees in their own team"
            }

    # Admin can view any employee's tickets
    elif requester.role == "admin":
        pass

    else:
        return {
            "success": False,
            "error": "Requester does not have permission to view employee tickets"
        }

    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == employee.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "employee": {
            "id": employee.id,
            "name": employee.name,
            "team": employee.team
        },
        "tickets": [
            ticket_to_dict(ticket)
            for ticket in tickets
        ]
    }

@router.get("/api/tickets/all")
def get_all_tickets(
    requester_id: str,
    db: Session = Depends(get_db)
):
    requester = (
        db.query(User)
        .filter(User.id == requester_id)
        .first()
    )

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    if requester.role != "admin":
        return {
            "success": False,
            "error": "Only admins can view all tickets"
        }

    tickets = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "tickets": [
            ticket_to_dict(ticket)
            for ticket in tickets
        ]
    }

@router.get("/api/tickets/{ticket_id}")
def get_ticket(
    ticket_id: str,
    requester_id: str,
    db: Session = Depends(get_db)
):

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        return {
            "success": False,
            "error": "Ticket not found"
        }

    requester = (
        db.query(User)
        .filter(User.id == requester_id)
        .first()
    )

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    ticket_owner = (
        db.query(User)
        .filter(User.id == ticket.user_id)
        .first()
    )

    if not ticket_owner:
        return {
            "success": False,
            "error": "Ticket owner not found"
        }

    if requester.role == "admin":
        return {
            "success": True,
            "ticket": ticket_to_dict(ticket)
        }

    if requester.role == "manager":

        if requester.team != ticket_owner.team:
            return {
                "success": False,
                "error": "Managers can only view tickets from their own team"
            }

        return {
            "success": True,
            "ticket": ticket_to_dict(ticket)
        }

    if requester.role == "employee":

        if requester.id != ticket.user_id:
            return {
                "success": False,
                "error": "Employees can only view their own tickets"
            }

        return {
            "success": True,
            "ticket": ticket_to_dict(ticket)
        }

    return {
        "success": False,
        "error": "Requester does not have permission to view tickets"
    }

@router.get("/api/tickets")
def get_my_tickets(
    user_id: str,
    db: Session = Depends(get_db)
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == user_id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "tickets": [
            ticket_to_dict(ticket)
            for ticket in tickets
        ]
    }

