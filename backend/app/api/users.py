from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/users", tags=["Users"])


users = {
    "user_001": {
        "id": "user_001",
        "name": "Admin User",
        "email": "admin@opsai.local",
        "department": "IT",
        "team": "IT Administration",
        "role": "admin",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check",
            "incident.read",
            "user.read"
        ]
    },

    "user_002": {
        "id": "user_002",
        "name": "Bharathi Sekar",
        "email": "bharathi@opsai.local",
        "department": "IT",
        "team": "IT Operations",
        "role": "manager",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check",
            "incident.read",
            "user.read"
        ]
    },

    "user_003": {
        "id": "user_003",
        "name": "Employee User",
        "email": "employee@opsai.local",
        "department": "IT",
        "team": "IT Operations",
        "role": "employee",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check",
            "incident.read"
        ]
    },

    "user_004": {
        "id": "user_004",
        "name": "Team Member",
        "email": "member@opsai.local",
        "department": "IT",
        "team": "IT Operations",
        "role": "employee",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check",
            "incident.read"
        ]
    },

    "user_005": {
        "id": "user_005",
        "name": "Another Employee",
        "email": "employee2@opsai.local",
        "department": "Finance",
        "team": "Finance Applications",
        "role": "employee",
        "permissions": [
            "knowledge.read",
            "ticket.create"
        ]
    }
}


@router.get("")
def get_allusers():
    return list(users.values())

@router.get("/admin/{target_user_id}")
def get_employee(
    target_user_id: str,
    requester_id: str
):
    requester = users.get(requester_id)

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    target = users.get(target_user_id)

    if not target:
        return {
            "success": False,
            "error": "Employee not found"
        }

    # Admin can read anyone
    if requester["role"] == "admin":
        return {
            "success": True,
            "user": target
        }


    # Manager can read employees in their own team,
    # but not administrators
    if requester["role"] == "manager":

        if target["role"] == "admin":
            return {
                "success": False,
                "error": "Managers cannot view administrators"
            }

        if requester["team"] != target["team"]:
            return {
                "success": False,
                "error": "Managers can only view employees in their own team"
            }

        return {
            "success": True,
            "user": target
        }


    # Employees can only read themselves
    if requester["role"] == "employee":

        if requester["id"] != target["id"]:
            return {
                "success": False,
                "error": "Requester does not have permission to view employees"
            }

        return {
            "success": True,
            "user": target
        }

@router.get("/admin")
def get_employees(requester_id: str):

    requester = users.get(requester_id)

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    # Admin → all users
    if requester["role"] == "admin":
        return {
            "success": True,
            "users": list(users.values())
        }

    # Manager → own team only
    if requester["role"] == "manager":

        team_members = [
                user
                for user in users.values()
                if user["team"] == requester["team"]
                and user["role"] != "admin"
            ]

        return {
            "success": True,
            "users": team_members
        }

    # Employee → only themselves
    return {
        "success": True,
        "users": [requester]
    }

@router.get("/{user_id}")
def get_user(user_id: str):
    user = users.get(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/{user_id}/permissions")
def get_user_permissions(user_id: str):
    user = users.get(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user_id,
        "permissions": user["permissions"]
    }

