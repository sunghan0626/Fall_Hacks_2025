# app/auth.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlmodel import select, Session
from .db import get_session
from .models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Argon2 password hasher (bcrypt는 72바이트 제한 때문에 버림)
pwd = CryptContext(schemes=["argon2"], deprecated="auto")


# -------- Helper --------
def current_user(request: Request, session: Session) -> User | None:
    """현재 로그인한 사용자 객체 반환 (없으면 None)."""
    uid = request.session.get("uid")
    if not uid:
        return None
    return session.get(User, uid)


# -------- Signup --------
@router.get("/signup")
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    email: str | None = Form(None),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    # username 중복 확인
    exists = session.exec(select(User).where(User.username == username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Argon2 해시 (길이 제한 없음)
    try:
        pw_hash = pwd.hash(password)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="Password hashing failed. Try a different password."
        ) from e

    user = User(username=username.strip(), email=email, password_hash=pw_hash)
    session.add(user)
    session.commit()
    session.refresh(user)

    # 세션 저장
    request.session["uid"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# -------- Login / Logout --------
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not pwd.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    request.session["uid"] = user.id
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# -------- Profile Edit --------
@router.get("/profile/edit")
def profile_edit(request: Request, session: Session = Depends(get_session)):
    user = current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("profile_edit.html", {"request": request, "user": user})


@router.post("/profile/edit")
def profile_update(
    request: Request,
    sport: str | None = Form(None),
    time_window: str | None = Form(None),
    region: str | None = Form(None),
    goal: str | None = Form(None),
    session: Session = Depends(get_session),
):
    user = current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)

    user.sport = sport
    user.time_window = time_window
    user.region = region
    user.goal = goal
    session.add(user)
    session.commit()

    return RedirectResponse("/profile/edit", status_code=303)
