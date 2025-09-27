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
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
from .db import init_db, get_session
from .models import User
from .auth import router as auth_router
from sqlmodel import Session

app = FastAPI(title="SweatMarket")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    uid = request.session.get("uid")
    user = session.get(User, uid) if uid else None
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# include feature routers
app.include_router(auth_router)
