from fastapi import FastAPI
from dotenv import load_dotenv
import pathlib
import logging
import os

# Load .env from project root if present
root = pathlib.Path(__file__).resolve().parents[1]
env_path = root / '.env'
if env_path.exists():
    load_dotenv(env_path)

from fastapi.middleware.cors import CORSMiddleware

# Use package-qualified imports
from backend.routers import room_router, websocket_router
from backend.database import create_db_and_tables
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Real-Time Pair Programming API (PostgreSQL MVP)",
    description="FastAPI backend with WebSockets and persistent storage via PostgreSQL.",
    version="1.0.0"
)

# 1. CORS Configuration
# Allow the frontend (running on a different port/origin) to connect
allowed = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,null",
)
allowed_list = [o.strip() for o in allowed.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.info(f"CORS allowed origins: {allowed_list}")

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