# app/posts.py
import os, time
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .db import get_session
from .auth import current_user
from .models import User, Post, Comment

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# 목록 (최신순 그리드)
@router.get("/posts")
def posts_list(request: Request, session: Session = Depends(get_session)):
    me = current_user(request, session)
    posts = session.exec(select(Post).order_by(Post.created_at.desc())).all()
    return templates.TemplateResponse("posts_list.html",
        {"request": request, "user": me, "posts": posts})

# 새 글 폼
@router.get("/posts/new")
def posts_new(request: Request, session: Session = Depends(get_session)):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login?msg=Please+log+in+first", status_code=303)
    return templates.TemplateResponse("post_new.html",
        {"request": request, "user": me})

# 업로드 처리
@router.post("/posts/new")
def posts_create(
    request: Request,
    image: UploadFile = File(...),
    caption: str | None = Form(None),
    session: Session = Depends(get_session),
):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login?msg=Please+log+in+first", status_code=303)

    os.makedirs("static/posts", exist_ok=True)
    ext = os.path.splitext(image.filename)[1].lower() or ".jpg"
    filename = f"{me.id}_{int(time.time())}{ext}"
    path = os.path.join("static/posts", filename)
    with open(path, "wb") as f:
        f.write(image.file.read())
    url = "/" + path

    post = Post(author_id=me.id, image_url=url, caption=caption or "")
    session.add(post)
    session.commit()
    return RedirectResponse(f"/posts/{post.id}", status_code=303)

# 글 상세 + 댓글
@router.get("/posts/{pid}")
def post_detail(pid: int, request: Request, session: Session = Depends(get_session)):
    me = current_user(request, session)
    post = session.get(Post, pid)
    if not post:
        return RedirectResponse("/posts", status_code=303)
    author = session.get(User, post.author_id)
    comments = session.exec(
        select(Comment).where(Comment.post_id == pid).order_by(Comment.created_at)
    ).all()
    return templates.TemplateResponse("post_detail.html",
        {"request": request, "user": me, "post": post, "author": author, "comments": comments})

# 댓글 추가
@router.post("/posts/{pid}/comment")
def add_comment(
    pid: int,
    request: Request,
    content: str = Form(...),
    session: Session = Depends(get_session),
):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login?msg=Please+log+in+first", status_code=303)
    post = session.get(Post, pid)
    if not post:
        return RedirectResponse("/posts", status_code=303)

    c = Comment(post_id=pid, author_id=me.id, content=(content or "").strip())
    session.add(c)
    session.commit()
    return RedirectResponse(f"/posts/{pid}", status_code=303)