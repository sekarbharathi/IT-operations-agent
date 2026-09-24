from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Incident


router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"]
)


def incident_to_dict(incident: Incident):
    return {
        "id": incident.id,
        "service": incident.service,
        "status": incident.status,
        "severity": incident.severity,
        "title": incident.title,
        "description": incident.description,
    }


@router.get("")
def get_incidents(
    db: Session = Depends(get_db)
):
    incidents = db.query(Incident).all()

    return [
        incident_to_dict(incident)
        for incident in incidents
    ]


@router.get("/{service}")
def get_service_incidents(
    service: str,
    db: Session = Depends(get_db)
):
    incidents = (
        db.query(Incident)
        .filter(Incident.service == service)
        .all()
    )

    if not incidents:
        raise HTTPException(
            status_code=404,
            detail="No incidents found for this service"
        )

    return [
        incident_to_dict(incident)
        for incident in incidents
    ]