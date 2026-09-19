from app.api.incidents import incidents
from app.api.users import users
from app.api.tickets import tickets


def check_service_incidents(service: str):

    service_incidents = [
        incident
        for incident in incidents.values()
        if incident["service"] == service
    ]

    return service_incidents


def get_user(user_id: str):

    return users.get(user_id)


def get_user_permissions(user_id: str):

    user = users.get(user_id)

    if not user:
        return None

    return user["permissions"]

def create_ticket(
    user_id: str,
    category: str,
    description: str
):
    user = users.get(user_id)

    if not user:
        return {
            "success": False,
            "error": "User not found"
        }

    if "ticket.create" not in user["permissions"]:
        return {
            "success": False,
            "error": "User does not have permission to create tickets"
        }

    ticket_id = f"ticket_{len(tickets) + 1:03d}"

    ticket = {
        "id": ticket_id,
        "user_id": user_id,
        "category": category,
        "description": description,
        "status": "open"
    }

    tickets[ticket_id] = ticket

    return {
        "success": True,
        "ticket": ticket
    }


if __name__ == "__main__":

    print(check_service_incidents("vpn"))

    print(get_user("user_001"))

    print(get_user_permissions("user_001"))

    print(
        create_ticket(
            user_id="user_002",
            category="VPN",
            description="VPN is not connecting."
        )
    )