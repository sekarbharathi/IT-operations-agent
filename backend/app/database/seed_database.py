from app.database.connection import SessionLocal
from app.database.models import (
    User,
    Permission,
    UserPermission,
    Incident,
)


db = SessionLocal()


try:
    # -------------------------
    # Users
    # -------------------------

    users = [
        User(
            id="user_001",
            name="Admin User",
            email="admin@opsai.local",
            department="IT",
            team="IT Administration",
            role="admin",
        ),
        User(
            id="user_002",
            name="Bharathi Sekar",
            email="bharathi@opsai.local",
            department="IT",
            team="IT Operations",
            role="manager",
        ),
        User(
            id="user_003",
            name="Employee User",
            email="employee@opsai.local",
            department="IT",
            team="IT Operations",
            role="employee",
        ),
        User(
            id="user_004",
            name="Team Member",
            email="member@opsai.local",
            department="IT",
            team="IT Operations",
            role="employee",
        ),
        User(
            id="user_005",
            name="Another Employee",
            email="employee2@opsai.local",
            department="Finance",
            team="Finance Applications",
            role="employee",
        ),
    ]

    db.add_all(users)


    # -------------------------
    # Permissions
    # -------------------------

    permissions = [
        Permission(id="permission_001", name="knowledge.read"),
        Permission(id="permission_002", name="ticket.create"),
        Permission(id="permission_003", name="vpn.check"),
        Permission(id="permission_004", name="incident.read"),
        Permission(id="permission_005", name="user.read"),
    ]

    db.add_all(permissions)


    # -------------------------
    # User permissions
    # -------------------------

    user_permissions = [
        # Admin
        UserPermission(
            user_id="user_001",
            permission_id="permission_001",
        ),
        UserPermission(
            user_id="user_001",
            permission_id="permission_002",
        ),
        UserPermission(
            user_id="user_001",
            permission_id="permission_003",
        ),
        UserPermission(
            user_id="user_001",
            permission_id="permission_004",
        ),
        UserPermission(
            user_id="user_001",
            permission_id="permission_005",
        ),

        # Manager
        UserPermission(
            user_id="user_002",
            permission_id="permission_001",
        ),
        UserPermission(
            user_id="user_002",
            permission_id="permission_002",
        ),
        UserPermission(
            user_id="user_002",
            permission_id="permission_003",
        ),
        UserPermission(
            user_id="user_002",
            permission_id="permission_004",
        ),
        UserPermission(
            user_id="user_002",
            permission_id="permission_005",
        ),

        # Employee
        UserPermission(
            user_id="user_003",
            permission_id="permission_001",
        ),
        UserPermission(
            user_id="user_003",
            permission_id="permission_002",
        ),
        UserPermission(
            user_id="user_003",
            permission_id="permission_003",
        ),
        UserPermission(
            user_id="user_003",
            permission_id="permission_004",
        ),

        # Team member
        UserPermission(
            user_id="user_004",
            permission_id="permission_001",
        ),
        UserPermission(
            user_id="user_004",
            permission_id="permission_002",
        ),
        UserPermission(
            user_id="user_004",
            permission_id="permission_003",
        ),
        UserPermission(
            user_id="user_004",
            permission_id="permission_004",
        ),

        # Finance employee
        UserPermission(
            user_id="user_005",
            permission_id="permission_001",
        ),
        UserPermission(
            user_id="user_005",
            permission_id="permission_002",
        ),
    ]

    db.add_all(user_permissions)


    # -------------------------
    # Incidents
    # -------------------------

    incidents = [
        Incident(
            id="incident_001",
            service="vpn",
            status="resolved",
            severity="medium",
            title="VPN authentication failures",
            description="Some users experienced authentication failures.",
        ),
        Incident(
            id="incident_002",
            service="email",
            status="active",
            severity="high",
            title="Email delivery delays",
            description="Some emails are currently experiencing delays.",
        ),
    ]

    db.add_all(incidents)


    db.commit()

    print("Database seeded successfully.")


except Exception:
    db.rollback()
    raise


finally:
    db.close()