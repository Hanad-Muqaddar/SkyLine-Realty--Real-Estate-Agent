"""
app.py
------
The web server. It does three things:
  - serves the demo website (the real estate page + chat widget)
  - exposes POST /chat  -> the agent replies
  - keeps a short in-memory conversation history per browser session

Run it with:  uvicorn app:app --reload  (from the backend/ folder)
Then open:    http://127.0.0.1:8000
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent import get_reply

app = FastAPI(title="Skyline Realty AI Agent")

# Allow the widget to call the API (handy if you embed it on another page).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory store: {session_id: [ {role, content}, ... ] }
# Fine for a demo. For production use a database or Redis.
SESSIONS = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(BASE_DIR, "frontend", "index.html")
PITCH_HTML = os.path.join(BASE_DIR, "frontend", "pitch.html")


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.get("/")
def home():
    # The pitch page is the landing page now.
    return FileResponse(PITCH_HTML)


@app.get("/demo")
def demo():
    # The live real-estate site with the chat widget.
    return FileResponse(FRONTEND)


@app.post("/chat")
def chat(payload: ChatIn):
    history = SESSIONS.setdefault(payload.session_id, [])
    history.append({"role": "user", "content": payload.message})

    reply, updated = get_reply(history)
    SESSIONS[payload.session_id] = updated

    return {"reply": reply}


@app.get("/health")
def health():
    return {"status": "ok"}
