# app/main.py
"""
FastAPI application entrypoint for SweatMarket.

Routes (wired here):
  - GET "/"                 -> landing (shows user card if logged in)
  - /login, /signup, /logout, /profile/*  (from auth router)
  - /chat, /chat/{room_id}, /ws/chat/{room_id} (from chat router)
  - /posts, /posts/new, /posts/{pid}, /posts/{pid}/comment (from posts router)
  - GET /health            -> health check

Owners:
  - Auth & Profile -> A
  - Community/Search -> B
  - Check-in/Geo -> C
  - Wallet/DEX -> D
"""
import os
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db, engine
from .auth import router as auth_router
from .chat import router as chat_router          # DM(WebSocket)
from .posts import router as posts_router        # Community Posts

# ------------------- Env & Logging -------------------
load_dotenv()
log = logging.getLogger("uvicorn")
log.info(f"DATABASE_URL={os.getenv('DATABASE_URL')}")

# ------------------- App Setup -------------------
app = FastAPI()

# Cookie-based session (stores uid)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret"),
    session_cookie="sweatmarket_session",
)

# Static files (css/js/img)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(auth_router)
app.include_router(chat_router)    # /chat, /ws/chat/*
app.include_router(posts_router)   # /posts, /posts/new, ...

# ------------------- Routes -------------------
@app.get("/")
def index(request: Request):
    """Landing page. If logged in, inject current user into template."""
    uid = request.session.get("uid")
    user = None
    if uid:
        from sqlmodel import Session as SQLSession, select
        from .models import User
        with SQLSession(engine) as s:
            user = s.exec(select(User).where(User.id == uid)).first()
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/health")
def health():
    return {"ok": True}

# ------------------- Startup -------------------
@app.on_event("startup")
def on_startup():
    # Create tables if they don't exist
    init_db()