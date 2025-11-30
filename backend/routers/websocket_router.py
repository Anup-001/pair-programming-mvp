from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.room_service import room_service
from backend.database import get_session
from sqlmodel import Session
import json
from starlette.concurrency import run_in_threadpool 
from typing import Generator

router = APIRouter()

# Helper function to close the session in a threadpool
def close_session_in_threadpool(session: Session):
    """Safely closes the database session in a dedicated thread."""
    try:
        session.close()
    except Exception as e:
        print(f"Error closing session in threadpool: {e}")

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time collaborative code editing.
    Threadpool is used for all synchronous DB operations.
    """
    # 1. Manually get a database session iterator
    session_generator: Generator[Session, None, None] = get_session()
    session = next(session_generator)
    
    room = None
    
    try:
        # 2. Check if the room exists by running lookup in a threadpool
        room = await run_in_threadpool(room_service.get_room_by_id, session, room_id)
        
        if not room:
            await websocket.close(code=1008, reason="Room does not exist.")
            return # Exit here, finally block handles session closure

        await websocket.accept()
        
        # Connect to in-memory store
        room_service.connect(room_id, websocket)

        # Send initial state
        initial_code = room.code
        await websocket.send_json({"type": "initial_state", "code": initial_code})

        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "code_change":
                    new_code = message.get("code")
                    if new_code is not None:
                        # 3. Update DB and broadcast (MUST be run in threadpool)
                        await run_in_threadpool(
                            room_service.broadcast_code_update,
                            session, 
                            room_id, 
                            new_code, 
                            sender=websocket
                        )
                
            except json.JSONDecodeError:
                print(f"Received non-JSON data: {data}")
            
    except WebSocketDisconnect:
        # Expected closure
        print(f"Client disconnected gracefully from room {room_id}")
    except Exception as e:
        # Catch unexpected errors (e.g., failed send due to immediate closure)
        print(f"Unexpected error in WebSocket loop for room {room_id}: {e}")
    finally:
        # CRUCIAL: 
        # 1. Remove connection from in-memory store
        if room: # Only try to disconnect if the room was successfully connected
            room_service.disconnect(room_id, websocket)
        
        # 2. Close the database session, wrapped in a threadpool
        # This prevents session cleanup from blocking the main async thread
        await run_in_threadpool(close_session_in_threadpool, session)