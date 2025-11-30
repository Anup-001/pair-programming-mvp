from typing import Generator, Any, Dict, Set, List
from sqlmodel import Session, SQLModel, create_engine
from fastapi import WebSocket
import os # <--- THIS IMPORT IS THE FIX

# --- 1. Database Configuration ---
# Update this with your actual PostgreSQL connection details (Supabase or Docker).
# If you are using Supabase, remember to replace YOUR_PASSWORD.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:dGu-aeJZ&?RPXA2@db.hjmdkclkvdlbcvbcascc.supabase.co:5432/postgres"
)

# Set connect_args={"check_same_thread": False} for SQLite, but not needed for PostgreSQL.
engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)

def create_db_and_tables():
    """Creates the PostgreSQL tables defined by the SQLModel models."""
    print("Attempting to create database tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        print("Ensure the PostgreSQL database 'pair_coding_db' exists and is reachable.")

def get_session() -> Generator[Session, Any, None]:
    """Dependency to provide a database session to FastAPI routes."""
    with Session(engine) as session:
        yield session

# --- 2. In-Memory Store for Volatile Data ---
# Connections MUST be stored in memory, as they are live WS objects.
# Key: roomId (str)
# Value: Set[WebSocket]
CONNECTION_DB: Dict[str, Set[WebSocket]] = {}