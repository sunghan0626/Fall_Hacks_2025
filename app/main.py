# app/main.py
import os, logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db, engine
from .auth import router as auth_router
from .chat import router as chat_router  # DM(WebSocket)

load_dotenv()
logging.getLogger("uvicorn").info(f"DATABASE_URL={os.getenv('DATABASE_URL')}")

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret"),
    session_cookie="sweatmarket_session",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router)
app.include_router(chat_router)   # /chat, /ws/chat/*

@app.get("/")
def index(request: Request):
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

@app.on_event("startup")
def on_startup():
    init_db()

