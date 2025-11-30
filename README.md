Real-Time Collaborative Pair-Programming Editor MVP

This is the Minimum Viable Product (MVP) for a real-time collaborative code editor.

Features

Room Management: Users can create unique rooms or join existing rooms.

Real-Time Sync: Code changes are instantly synchronized between all connected users via WebSockets.

Persistence: Code state is saved to a PostgreSQL database, ensuring code remains even if the server restarts.

Mock AI Autocomplete: A mock endpoint provides code suggestions (press Tab to accept).

Architecture

Component

Technology

Role

Backend API

FastAPI, Python, SQLModel

REST endpoints for room creation and AI mock.

Backend Persistence

PostgreSQL

Stores room data (room_id, code).

Backend WS

FastAPI WebSockets

Manages real-time connections and broadcasts updates. Active connections are kept in in-memory (CONNECTION_DB).

Frontend

React (JSX), Tailwind CSS

UI, implements debounce for AI, and manages the WebSocket connection.

Sync Strategy

Last-Write Wins (Full Sync)

The entire file content is sent on every change for simplicity.

Setup and Installation

Prerequisites

Python 3.8+

Node.js & npm (for the frontend)

PostgreSQL Server (running locally or remotely).

A. PostgreSQL Setup

Start your PostgreSQL server.

Create a database named pair_coding_db.

Ensure your connection details match the DATABASE_URL in backend/database.py (default: postgresql://postgres:password@localhost:5432/pair_coding_db).

B. Backend Setup

Navigate to the backend directory:

cd backend


Install dependencies:

pip install -r requirements.txt


Run the FastAPI server:

uvicorn main:app --reload --port 8000


Note: On startup, the main.py file will automatically connect to PostgreSQL and create the room table.

C. Frontend Setup

The frontend is a single React file. If you are using a standard development environment (like Vite/CRA), ensure frontend/src/App.jsx is your main component.

Run the development server:

# Assuming you are running a standard React setup
npm run dev


How to Demo

Open the frontend application in your browser (e.g., http://localhost:5173).

Click "Create New Room".

Copy the URL (which now contains the room ID, e.g., /room/abcd123).

Open a second browser tab (or incognito window) and paste the URL.

Type code in one editor; the changes will instantly reflect in the other.

Pause typing for ~600ms to see the mock AI suggestion appear, then press Tab to insert the code.

Test Persistence: Stop the FastAPI server, restart it, and refresh the browser tabs—the code state will be reloaded from PostgreSQL.