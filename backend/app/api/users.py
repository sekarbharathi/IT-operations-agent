from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/users", tags=["Users"])


users = {
    "user_001": {
        "id": "user_001",
        "name": "Bharathi Sekar",
        "email": "bharathi@opsai.local",
        "department": "Engineering",
        "role": "employee",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check"
        ]
    },
    "user_002": {
        "id": "user_002",
        "name": "Admin User",
        "email": "admin@opsai.local",
        "department": "IT",
        "role": "it_admin",
        "permissions": [
            "knowledge.read",
            "ticket.create",
            "vpn.check",
            "incident.read",
            "user.read",
            "admin.access"
        ]
    },
    "user_002": {
            "id": "user_003",
            "name": "Admin User",
            "email": "admin@opsai.local",
            "department": "IT",
            "role": "it_admin",
            "permissions": [
                "knowledge.read",
                
                "vpn.check",
                "incident.read",
                "user.read",
                
            ]
    }
}


@router.get("")
def get_allusers():
    return list(users.values())


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