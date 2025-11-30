from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routers import room_router, websocket_router
from database import create_db_and_tables
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Real-Time Pair Programming API (PostgreSQL MVP)",
    description="FastAPI backend with WebSockets and persistent storage via PostgreSQL.",
    version="1.0.0"
)

# 1. CORS Configuration
# Allow the frontend (running on a different port/origin) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Include Routers
app.include_router(room_router.router, tags=["Rooms and AI"], prefix="")
app.include_router(websocket_router.router, tags=["WebSockets"], prefix="")

# 3. Database Startup Event
@app.on_event("startup")
def on_startup():
    """Ensure database tables are created when the app starts."""
    create_db_and_tables()

# 4. Root Endpoint for health check
@app.get("/")
def read_root():
    return {"status": "ok", "service": "Pair Programming API is running (PostgreSQL)."}

# To run the app locally:
# uvicorn backend.main:app --reload --port 8000