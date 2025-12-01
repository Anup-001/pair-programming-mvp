Real-Time Collaborative Pair-Programming Editor — MVP

This repository contains a small prototype of a real-time collaborative code editor:

- Backend: FastAPI + WebSockets + SQLModel (Postgres)
- Frontend: React (JSX) + minimal UI
- Sync strategy: Last-write-wins (full-file sync on every change)
- Mock AI autocomplete endpoint for suggestions

**Getting Started**

- **Prerequisites:** `python` 3.8+, `node` + `npm`, and (optionally) `PostgreSQL`.
- Recommended workflow: run backend and frontend in separate terminals.

**Backend (FastAPI)**

- Navigate to the backend folder and create a virtual environment (recommended):

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
```

- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

- Configure the database (optional):
	- By default the app reads `DATABASE_URL` from the environment. For quick local testing you can set it to a sqlite DB (no Postgres required):

```powershell
# quick local fallback (development only):
setx DATABASE_URL "sqlite:///./dev.db"
```

- Start the server (from project root or `backend` directory):

```powershell
# from project root
uvicorn backend.main:app --reload --port 8000
```

**Frontend (React)**

- Install frontend deps and run dev server:

```powershell
cd frontend
npm install
npm run dev
```

- Open the app in the browser (default Vite port): `http://localhost:5173` or the URL shown by your dev server.

**Basic Usage / Demo**

- Click `Create New Room`. The frontend will POST to `/rooms` and navigate to `/room/{roomId}`.
- Open a second tab (or another browser) and go to the same URL to see real-time sync.
- Pause typing ~600ms to trigger the mocked autocomplete; press `Tab` to accept the suggestion.

**API endpoints**

- `POST /rooms` — create a new room, returns `{ "roomId": "..." }`.
- `POST /autocomplete` — mocked AI autocomplete, accepts `{ code, cursorPosition, language }`.
- WebSocket: `ws://<host>/ws/{roomId}` — connects to a room and receives `initial_state` and `code_update` messages.
- `GET /debug/rooms` — development helper: returns in-memory connection counts per room.

**Troubleshooting**

- WebSocket handshake 403 / rejected:
	- Ensure the frontend origin is allowed. The backend reads `ALLOWED_ORIGINS` (comma-separated) and includes common localhost origins by default.
	- Incognito/file contexts can send `Origin: null` — the default server config includes `null` for convenience.

- Rapid reconnects / many connections:
	- Dev servers with hot-reload (`--reload`) restart on code changes, causing connected clients to reconnect quickly.
	- React StrictMode can mount components twice in development, which may open duplicate sockets. Use a single socket instance per tab (the frontend already includes connection guards but see code comments).

- Room appears full / immediate close:
	- The backend limits concurrent connections per room (default 2) to prevent resource storms. Increase the limit in `backend/services/room_service.py` for local testing.

**Future Improvements**
- Can add User Authentication feature.
- Real AI Autocompletion
- Code Execution Feature

**Development notes & recommendations**

- For local testing without Postgres, set `DATABASE_URL` to `sqlite:///./dev.db` to avoid DB setup.
- Disable `--reload` while testing long-lived WebSocket behavior to avoid reconnect storms.
- Use `GET /debug/rooms` to inspect the server's in-memory connection counts.

If you'd like, I can also:

- Add a `docker-compose.yml` to run Postgres + backend quickly.
- Provide a ready-made `.env.example` with `DATABASE_URL` and `ALLOWED_ORIGINS`.
- Patch the frontend to add a safer single-socket pattern (prevents duplicate sockets in dev). 

Thanks — open an issue or ask me to apply any of the optional improvements above.
