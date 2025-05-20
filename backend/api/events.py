from fastapi import APIRouter
from services.event_log import get_recent_events

router = APIRouter()

@router.get("/events")
def get_gas_events():
    return {
        "events": get_recent_events()
    }
