import os
import uuid
from typing import Dict, Any, Set, Optional
from fastapi import WebSocket
from sqlmodel import Session, select

from backend.database import CONNECTION_DB
from backend.schemas import Room
import logging

class RoomService:
    def create_room(self, session: Session) -> str:
        """Creates a new room in the database and returns its unique ID."""
        # Generates a short, simple ID from a UUID
        room_id = str(uuid.uuid4()).split('-')[0] 
        
        # Ensures ID uniqueness and persistence
        new_room = Room(room_id=room_id, code="# Start coding here...")
        session.add(new_room)
        session.commit()
        session.refresh(new_room)
        
        # Initialize in-memory connection list for this room
        CONNECTION_DB[room_id] = set()
        
        return room_id

    def get_room_by_id(self, session: Session, room_id: str) -> Optional[Room]:
        """Retrieves a room object from the database."""
        statement = select(Room).where(Room.room_id == room_id)
        return session.exec(statement).first()

    # --- Volatile Connection Management (In-Memory) ---

    def connect(self, room_id: str, websocket: WebSocket) -> bool:
        """Adds a WebSocket connection to the room's active connections."""
        # Ensure the in-memory map has an entry for the room. This is important
        # because the persistent DB may contain the room record but the in-memory
        # CONNECTION_DB is reset when the server restarts.
        if room_id not in CONNECTION_DB:
            CONNECTION_DB[room_id] = set()

        # Limit the number of concurrent connections per room to avoid
        # excessive resource usage and accidental multi-connection storms.
        try:
            MAX_CONNECTIONS_PER_ROOM = int(os.getenv("MAX_CONNECTIONS_PER_ROOM", "2"))
        except Exception:
            MAX_CONNECTIONS_PER_ROOM = 2

        conns = CONNECTION_DB[room_id]
        if len(conns) >= MAX_CONNECTIONS_PER_ROOM:
            logging.info(f"Room {room_id} has reached max connections ({len(conns)}). Rejecting new connection.")
            return False

        conns.add(websocket)
        logging.info(f"Connected websocket to room {room_id}. connections={len(conns)}")
        return True

    def disconnect(self, room_id: str, websocket: WebSocket):
        """Removes a WebSocket connection from the room."""
        if room_id in CONNECTION_DB and websocket in CONNECTION_DB[room_id]:
            CONNECTION_DB[room_id].remove(websocket)
            logging.info(f"Disconnected websocket from room {room_id}. connections={len(CONNECTION_DB[room_id])}")

    def update_room_code(self, session: Session, room_id: str, new_code: str):
        """Updates the code state persistently in the database."""
        room = self.get_room_by_id(session, room_id)
        if room:
            room.code = new_code
            session.add(room)
            session.commit()
            session.refresh(room)

    async def broadcast_code_update(self, room_id: str, new_code: str, sender: WebSocket):
        """
        Broadcast the updated code to all in-memory WebSocket connections
        for the given `room_id`, excluding the `sender` socket.

        Database persistence should be handled outside this async method
        (for example, in `run_in_threadpool`) so the event loop is not
        blocked by synchronous DB operations.
        """
        if room_id in CONNECTION_DB:
            disconnected_sockets = set()
            for connection in list(CONNECTION_DB[room_id]):
                if connection != sender:
                    try:
                        await connection.send_json({"type": "code_update", "code": new_code})
                    except Exception:
                        disconnected_sockets.add(connection)

            for ws in disconnected_sockets:
                self.disconnect(room_id, ws)

room_service = RoomService()