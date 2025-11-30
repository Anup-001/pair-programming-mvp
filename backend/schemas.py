from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from typing import Optional

# --- 1. Database Model ---

class Room(SQLModel, table=True):
    """
    SQLModel representation of the 'room' table in PostgreSQL.
    Stores the persistent code state.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # This is the external identifier (e.g., in the URL)
    room_id: str = Field(index=True, unique=True, nullable=False)
    
    # The actual code content, stored persistently
    code: str = Field(default="# Start coding here...", nullable=False)


# --- 2. API Schemas ---

class RoomCreateResponse(BaseModel):
    """Response model for room creation."""
    roomId: str

class AutocompleteRequest(BaseModel):
    """Request model for the AI autocomplete endpoint."""
    code: str
    cursorPosition: int
    language: str

class AutocompleteResponse(BaseModel):
    """Response model for the AI autocomplete endpoint."""
    suggestion: str
    detail: str