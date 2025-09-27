# FastAPI app entrypoint.
# TODO (All):
# - Wire up Jinja2 templates and StaticFiles mount.
# - Startup: call init_db().
# - Routes:
#   - GET "/" -> landing (shows open offers)
#   - Auth: GET/POST "/login", "/signup", "/logout"
#   - Offers: list/new/join ("/offers", "/offers/new", "/offers/{id}/join")
#   - Session: QR page + confirm ("/session/{sid}", "/session/{sid}/qr.png", POST "/session/{sid}/confirm")
#   - Wallet: GET "/wallet"
#   - Profile: GET/POST "/profile"
#   - Community: GET "/posts", GET/POST "/posts/new", GET "/posts/{pid}", POST "/posts/{pid}/comment"
#   - DEX: GET "/dex", POST "/dex/new"
#
# Owners:
# - Auth & Profile -> A
# - Community/Search -> B
# - Check-in/Geo -> C
# - Wallet/DEX -> D

# app/main.py
# FastAPI app entrypoint.
# -------------------------------
# Routes overview:
#   - GET "/" -> landing (shows open offers)
#   - Auth: GET/POST "/login", "/signup", "/logout"
#   - Offers: list/new/join
#   - Session: QR + confirm
#   - Wallet
#   - Profile: GET/POST "/profile"
#   - Community: posts/comments
#   - DEX
#
# Owners:
#   - Auth & Profile -> A
#   - Community/Search -> B
#   - Check-in/Geo -> C
#   - Wallet/DEX -> D
# -------------------------------

import os, logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db
from .auth import router as auth_router

# ------------------- Env & Logging -------------------
load_dotenv()
log = logging.getLogger("uvicorn")
log.info(f"DATABASE_URL={os.getenv('DATABASE_URL')}")

# ------------------- App Setup -------------------
app = FastAPI()

# 세션 미들웨어 (쿠키에 uid 저장)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret"),
    session_cookie="sweatmarket_session",
)

# 정적 파일 (css/js/img)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿
templates = Jinja2Templates(directory="app/templates")

# 라우터 등록
app.include_router(auth_router)

# ------------------- Routes -------------------
@app.get("/")
def index(request: Request):
    """Landing page. If logged in, injects current user into template."""
    uid = request.session.get("uid")
    user = None
    if uid:
        from .models import User
        from sqlmodel import Session as SQLSession, select
        from .db import engine
        with SQLSession(engine) as s:
            user = s.exec(select(User).where(User.id == uid)).first()
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# ------------------- Startup -------------------
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}