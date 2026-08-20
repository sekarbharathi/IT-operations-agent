from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"]
)


incidents = {
    "incident_001": {
        "id": "incident_001",
        "service": "vpn",
        "status": "resolved",
        "severity": "medium",
        "title": "VPN authentication failures",
        "description": "Some users experienced authentication failures.",
    },
    "incident_002": {
        "id": "incident_002",
        "service": "email",
        "status": "active",
        "severity": "high",
        "title": "Email delivery delays",
        "description": "Some emails are currently experiencing delays.",
    }
}


@router.get("")
def get_incidents():
    return list(incidents.values())


@router.get("/{service}")
def get_service_incidents(service: str):

    service_incidents = []

    for incident in incidents.values():
        if incident["service"] == service:
            service_incidents.append(incident)

    if not service_incidents:
        raise HTTPException(
            status_code=404,
            detail="No incidents found for this service"
        )

    return service_incidents