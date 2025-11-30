import uuid
from typing import Dict, Any, Set, Optional
from fastapi import WebSocket
from sqlmodel import Session, select
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import CONNECTION_DB
from schemas import Room

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
        if room_id in CONNECTION_DB:
            CONNECTION_DB[room_id].add(websocket)
            return True
        return False

    def disconnect(self, room_id: str, websocket: WebSocket):
        """Removes a WebSocket connection from the room."""
        if room_id in CONNECTION_DB and websocket in CONNECTION_DB[room_id]:
            CONNECTION_DB[room_id].remove(websocket)

    def update_room_code(self, session: Session, room_id: str, new_code: str):
        """Updates the code state persistently in the database."""
        room = self.get_room_by_id(session, room_id)
        if room:
            room.code = new_code
            session.add(room)
            session.commit()
            session.refresh(room)

    async def broadcast_code_update(self, session: Session, room_id: str, new_code: str, sender: WebSocket):
        """
        1. Updates the code persistently in the DB.
        2. Sends the new code state to all connected clients in memory, excluding the sender.
        """
        # 1. Update Persistent DB State (Last-Write Wins)
        self.update_room_code(session, room_id, new_code)
        
        # 2. Broadcast to Volatile Connections
        if room_id in CONNECTION_DB:
            disconnected_sockets = set()
            for connection in list(CONNECTION_DB[room_id]):
                if connection != sender:
                    try:
                        # Send the entire new code state
                        await connection.send_json({"type": "code_update", "code": new_code})
                    except Exception:
                        # Mark connection for cleanup if sending fails
                        disconnected_sockets.add(connection)
                        
            # Clean up disconnected sockets
            for ws in disconnected_sockets:
                self.disconnect(room_id, ws)

room_service = RoomService()