from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User, Permission, UserPermission


router = APIRouter(prefix="/api/users", tags=["Users"])


def user_to_dict(user: User, db: Session):
    permissions = (
        db.query(Permission.name)
        .join(
            UserPermission,
            Permission.id == UserPermission.permission_id
        )
        .filter(UserPermission.user_id == user.id)
        .all()
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "team": user.team,
        "role": user.role,
        "permissions": [permission[0] for permission in permissions]
    }


@router.get("")
def get_allusers(db: Session = Depends(get_db)):

    users = db.query(User).all()

    return [
        user_to_dict(user, db)
        for user in users
    ]


@router.get("/admin/{target_user_id}")
def get_employee(
    target_user_id: str,
    requester_id: str,
    db: Session = Depends(get_db)
):
    requester = db.query(User).filter(
        User.id == requester_id
    ).first()

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    target = db.query(User).filter(
        User.id == target_user_id
    ).first()

    if not target:
        return {
            "success": False,
            "error": "Employee not found"
        }

    target_data = user_to_dict(target, db)

    # Admin can read anyone
    if requester.role == "admin":
        return {
            "success": True,
            "user": target_data
        }

    # Manager can read employees in their own team,
    # but not administrators
    if requester.role == "manager":

        if target.role == "admin":
            return {
                "success": False,
                "error": "Managers cannot view administrators"
            }

        if requester.team != target.team:
            return {
                "success": False,
                "error": "Managers can only view employees in their own team"
            }

        return {
            "success": True,
            "user": target_data
        }

    # Employees can only read themselves
    if requester.role == "employee":

        if requester.id != target.id:
            return {
                "success": False,
                "error": "Requester does not have permission to view employees"
            }

        return {
            "success": True,
            "user": target_data
        }


@router.get("/admin")
def get_employees(
    requester_id: str,
    db: Session = Depends(get_db)
):
    requester = db.query(User).filter(
        User.id == requester_id
    ).first()

    if not requester:
        return {
            "success": False,
            "error": "Requester not found"
        }

    # Admin → all users
    if requester.role == "admin":

        users = db.query(User).all()

        return {
            "success": True,
            "users": [
                user_to_dict(user, db)
                for user in users
            ]
        }

    # Manager → own team only
    if requester.role == "manager":

        team_members = (
            db.query(User)
            .filter(
                User.team == requester.team,
                User.role != "admin"
            )
            .all()
        )

        return {
            "success": True,
            "users": [
                user_to_dict(user, db)
                for user in team_members
            ]
        }

    # Employee → only themselves
    return {
        "success": True,
        "users": [
            user_to_dict(requester, db)
        ]
    }


@router.get("/{user_id}")
def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user_to_dict(user, db)


@router.get("/{user_id}/permissions")
def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    permissions = (
        db.query(Permission.name)
        .join(
            UserPermission,
            Permission.id == UserPermission.permission_id
        )
        .filter(UserPermission.user_id == user_id)
        .all()
    )

    return {
        "user_id": user_id,
        "permissions": [
            permission[0]
            for permission in permissions
        ]
    }