# app/main.py — merged Part A + Part D (demo-friendly, passes `user`)

from __future__ import annotations

import os
import random
import inspect
from pathlib import Path
from typing import Optional, Dict, List

# Optional .env loading (safe if python-dotenv is missing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlmodel import Session as DBSession, select

# ---------- DB imports (soft) ----------
try:
    from .db import engine, init_db, get_session  # Part A style
except Exception:
    engine = None  # type: ignore

    async def init_db() -> None:  # type: ignore
        pass

    def get_session():  # type: ignore
        class _Dummy:
            def get(self, *_a, **_kw):
                return None
        return _Dummy()

# ---------- Auth imports (soft) ----------
try:
    from .auth import router as auth_router  # Part A may expose a router
except Exception:
    auth_router = None  # type: ignore

try:
    from .auth import COOKIE_NAME, verify_session  # Part D cookie helpers (optional)
except Exception:
    COOKIE_NAME = "fitcoin_session"  # type: ignore

    def verify_session(_: str) -> Optional[int]:  # type: ignore
        return None

# ---------- Models (soft) ----------
try:
    from .models import User, Tx, Order  # type: ignore
except Exception:
    User = Tx = Order = None  # type: ignore


app = FastAPI(title="SweatMarket")

# ---------- Static & templates (make dirs if missing) ----------
BASE_DIR = Path(__file__).resolve().parent.parent  # repo root
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"),
    session_cookie="sweatmarket_session",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ---------- DEMO MODE (for Part D) ----------
# Enabled if DB/models are missing, or env SWEATMARKET_DEMO=1, or ?demo=1
MOCK_ORDERS: Dict[str, List[Dict[str, int]]] = {"buy": [], "sell": []}

def seed_mock_orders() -> None:
    if MOCK_ORDERS["buy"] or MOCK_ORDERS["sell"]:
        return
    for p in [96, 98, 100, 101, 103]:
        MOCK_ORDERS["buy"].append({"price": p, "amount": random.randint(5, 20)})
    for p in [104, 106, 108, 110]:
        MOCK_ORDERS["sell"].append({"price": p, "amount": random.randint(5, 20)})

def is_demo(request: Request) -> bool:
    if os.getenv("SWEATMARKET_DEMO") == "1":
        return True
    if request.query_params.get("demo") == "1":
        return True
    if engine is None or User is None or Tx is None:
        return True
    return False

def current_user_id(request: Request) -> Optional[int]:
    # Prefer Part-A session
    try:
        uid = request.session.get("uid")  # type: ignore[attr-defined]
        if uid:
            return int(uid)
    except Exception:
        pass
    # Fallback to Part-D cookie
    token = request.cookies.get(COOKIE_NAME)
    return verify_session(token) if token else None  # type: ignore


# ---------- startup ----------
@app.on_event("startup")
async def _startup() -> None:
    # Support both sync/async init_db
    if inspect.iscoroutinefunction(init_db):   # type: ignore
        await init_db()                        # type: ignore
    else:
        init_db()                              # type: ignore
    seed_mock_orders()


# ---------- home (Part A style) ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: DBSession = Depends(get_session)):
    uid: Optional[int] = None
    try:
        uid = request.session.get("uid")
    except Exception:
        uid = None

    user = None
    try:
        if uid and User is not None and session is not None:
            user = session.get(User, uid)  # type: ignore
    except Exception:
        # Fallback if dependency isn’t a real Session yet
        if uid and engine is not None and User is not None:
            with DBSession(engine) as db:  # type: ignore[arg-type]
                user = db.get(User, uid)   # type: ignore

    return templates.TemplateResponse("index.html", {"request": request, "user": user})


# ---------- include Part-A auth router if present ----------
if auth_router:
    app.include_router(auth_router)


# ====================== Part D: WALLET ===============================
@app.get("/wallet", response_class=HTMLResponse)
def wallet_page(request: Request) -> HTMLResponse:
    demo = is_demo(request)
    uid = current_user_id(request)

    # Fetch a user object for the nav when possible
    user_for_nav = None
    if uid and engine and User:
        try:
            with DBSession(engine) as db:  # type: ignore[arg-type]
                user_for_nav = db.get(User, uid)  # type: ignore
        except Exception:
            user_for_nav = None

    if demo:
        u = type("U", (), {"coins": 42})()  # demo balance
        sample = [
            {"created_at": "now-1h", "kind": "earn",  "amount": 10, "note": "Meetup demo"},
            {"created_at": "now-3h", "kind": "spend", "amount": -3, "note": "Gold Badge"},
            {"created_at": "yesterday", "kind": "bonus", "amount": 5, "note": "Streak"},
        ]
        return templates.TemplateResponse(
            "wallet.html",
            {"request": request, "u": u, "txs": sample, "demo": True, "user": user_for_nav},
        )

    if not uid:
        return RedirectResponse("/login", status_code=303)
    if engine is None or User is None or Tx is None:
        return HTMLResponse("<h2>Wallet</h2><p>DB/models not ready.</p>", status_code=200)

    with DBSession(engine) as db:  # type: ignore[arg-type]
        u = db.get(User, uid)  # type: ignore
        if not u:
            return HTMLResponse("<h2>Wallet</h2><p>User not found.</p>", status_code=404)
        txs = db.exec(select(Tx).where(Tx.user_id == uid).order_by(Tx.id.desc())).all()  # type: ignore

    return templates.TemplateResponse(
        "wallet.html",
        {"request": request, "u": u, "txs": txs, "demo": False, "user": u},
    )


# ======================= Part D: DEX ================================
@app.get("/dex", response_class=HTMLResponse)
def dex_page(request: Request) -> HTMLResponse:
    demo = is_demo(request)

    # Fetch user for nav if possible
    user_for_nav = None
    uid = current_user_id(request)
    if uid and engine and User:
        try:
            with DBSession(engine) as db:  # type: ignore[arg-type]
                user_for_nav = db.get(User, uid)  # type: ignore
        except Exception:
            user_for_nav = None

    if demo:
        buys = sorted(MOCK_ORDERS["buy"], key=lambda o: o["price"], reverse=True)
        sells = sorted(MOCK_ORDERS["sell"], key=lambda o: o["price"])
        return templates.TemplateResponse(
            "dex.html",
            {"request": request, "buys": buys, "sells": sells, "demo": True, "user": user_for_nav},
        )

    if engine is None or Order is None:
        return HTMLResponse("<h2>DEX</h2><p>DB/models not ready.</p>", status_code=200)

    with DBSession(engine) as db:  # type: ignore[arg-type]
        buys = db.exec(select(Order).where(Order.side == "buy").order_by(Order.price.desc())).all()  # type: ignore
        sells = db.exec(select(Order).where(Order.side == "sell").order_by(Order.price.asc())).all()  # type: ignore

    return templates.TemplateResponse(
        "dex.html",
        {"request": request, "buys": buys, "sells": sells, "demo": False, "user": user_for_nav},
    )


@app.post("/dex/new")
def dex_new(request: Request, side: str = Form(...), price: int = Form(...), amount: int = Form(...)) -> RedirectResponse:
    demo = is_demo(request)
    uid = current_user_id(request)

    if demo:
        if side not in ("buy", "sell"):
            side = "buy"
        MOCK_ORDERS[side].append({"price": int(price), "amount": int(amount)})
        return RedirectResponse("/dex?demo=1", status_code=303)

    if not uid:
        return RedirectResponse("/login", status_code=303)
    if engine is None or Order is None:
        return RedirectResponse("/dex?e=db_not_ready", status_code=303)

    with DBSession(engine) as db:  # type: ignore[arg-type]
        db.add(Order(user_id=uid, side=side, price=price, amount=amount))  # type: ignore
        db.commit()
    return RedirectResponse("/dex", status_code=303)


# ---------- health (from Part A) ----------
@app.get("/health")
def health():
    return {"ok": True}

# -------- TODO: Parts B/C will add their routers/routes later --------
# [B] /posts, /posts/new, /posts/{pid}, /posts/{pid}/comment
# [C] /offers, /offers/new, /offers/{id}/join, /session/{sid}, /session/{sid}/qr.png, POST /session/{sid}/confirm
