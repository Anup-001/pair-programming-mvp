from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.schemas import RoomCreateResponse, AutocompleteRequest, AutocompleteResponse
from backend.services.room_service import room_service
from backend.database import get_session, CONNECTION_DB

router = APIRouter()

@router.post("/rooms", response_model=RoomCreateResponse)
async def create_new_room(session: Session = Depends(get_session)):
    """Creates a new room in PostgreSQL and returns the room ID."""
    room_id = room_service.create_room(session)
    return {"roomId": room_id}

@router.post("/autocomplete", response_model=AutocompleteResponse)
async def get_mock_autocomplete(request: AutocompleteRequest):
    """
    Mocked AI Autocomplete Endpoint.
    Returns a static or rule-based suggestion based on the code content.
    """
    suggestion = ""
    # Simple rule-based mock AI logic:
    if "def " in request.code and "return" not in request.code:
        suggestion = "    return "
    elif "class " in request.code and "def __init__" not in request.code:
        suggestion = "    def __init__(self):"
    elif "loop" in request.code.lower():
        suggestion = "for item in collection:"
    else:
        suggestion = "print('Hello, World!')" # Default suggestion

    return AutocompleteResponse(
        suggestion=suggestion,
        detail="Mocked suggestion generated successfully."
    )


# Development helper: show in-memory connection counts
@router.get("/debug/rooms")
def list_rooms_debug():
    return {rid: len(conns) for rid, conns in CONNECTION_DB.items()}