# app/chat.py
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import os, json
from .db import get_session
from .models import ChatRoom, Message, User
from .auth import current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --- simple in-memory WS connection manager (per room) ---
class RoomManager:
    def __init__(self):
        self.rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, room_id: int, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(room_id, set()).add(ws)

    def disconnect(self, room_id: int, ws: WebSocket):
        self.rooms.get(room_id, set()).discard(ws)
        if not self.rooms.get(room_id):
            self.rooms.pop(room_id, None)

    async def broadcast(self, room_id: int, payload: dict):
        dead = []
        for ws in self.rooms.get(room_id, set()):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room_id, ws)

manager = RoomManager()

def get_or_create_room(session: Session, a: int, b: int) -> ChatRoom:
    u1, u2 = sorted([a, b])
    room = session.exec(
        select(ChatRoom).where(ChatRoom.user1_id == u1, ChatRoom.user2_id == u2)
    ).first()
    if not room:
        room = ChatRoom(user1_id=u1, user2_id=u2)
        session.add(room)
        session.commit()
        session.refresh(room)
    return room

# ----- UI: my chat list -----
@router.get("/chat")
def chat_list(request: Request, session: Session = Depends(get_session)):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login", status_code=303)
    rooms = session.exec(
        select(ChatRoom).where((ChatRoom.user1_id == me.id) | (ChatRoom.user2_id == me.id))
    ).all()
    # resolve the other side
    def other_id(r: ChatRoom) -> int:
        return r.user2_id if r.user1_id == me.id else r.user1_id
    others = {r.id: session.get(User, other_id(r)) for r in rooms}
    return templates.TemplateResponse("chat_list.html", {"request": request, "user": me, "rooms": rooms, "others": others})

# ----- start 1:1 chat from a profile -----
@router.post("/chat/start")
def chat_start(request: Request, user_id: int = Form(...), session: Session = Depends(get_session)):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login", status_code=303)
    if me.id == user_id:
        return RedirectResponse("/chat", status_code=303)
    other = session.get(User, user_id)
    if not other:
        return RedirectResponse("/chat", status_code=303)
    room = get_or_create_room(session, me.id, other.id)
    return RedirectResponse(f"/chat/{room.id}", status_code=303)

# ----- room page -----
@router.get("/chat/{room_id}")
def chat_room(room_id: int, request: Request, session: Session = Depends(get_session)):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login", status_code=303)
    room = session.get(ChatRoom, room_id)
    if not room or (me.id not in (room.user1_id, room.user2_id)):
        return RedirectResponse("/chat", status_code=303)
    msgs = session.exec(
        select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
    ).all()
    other_id = room.user2_id if room.user1_id == me.id else room.user1_id
    other = session.get(User, other_id)
    return templates.TemplateResponse(
        "chat_room.html",
        {"request": request, "user": me, "room": room, "other": other, "messages": msgs},
    )

# ----- WebSocket for real-time text -----
@router.websocket("/ws/chat/{room_id}")
async def ws_chat(room_id: int, websocket: WebSocket, session: Session = Depends(get_session)):
    # session-auth via Cookie (Starlette copies it to headers)
    await manager.connect(room_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            content = (data.get("content") or "").strip()
            sender_id = int(data["sender_id"])

            # persist
            msg = Message(room_id=room_id, sender_id=sender_id, content=content)
            session.add(msg)
            session.commit()
            session.refresh(msg)

            await manager.broadcast(room_id, {
                "type": "text",
                "id": msg.id,
                "sender_id": sender_id,
                "content": content,
                "created_at": msg.created_at.isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)

# ----- HTTP upload for images (then broadcast url) -----
@router.post("/chat/{room_id}/image")
def upload_image(room_id: int, request: Request, image: UploadFile = File(...), session: Session = Depends(get_session)):
    me = current_user(request, session)
    if not me:
        return RedirectResponse("/login", status_code=303)
    os.makedirs("static/chat_images", exist_ok=True)
    ext = os.path.splitext(image.filename)[1].lower() or ".jpg"
    path = f"static/chat_images/{room_id}_{me.id}_{int(__import__('time').time())}{ext}"
    with open(path, "wb") as f:
        f.write(image.file.read())
    url = "/" + path

    msg = Message(room_id=room_id, sender_id=me.id, image_url=url, content="")
    session.add(msg)
    session.commit()
    session.refresh(msg)

    # fire-and-forget broadcast (no await here; it’s sync route)
    import anyio
    anyio.from_thread.run(manager.broadcast, room_id, {
        "type": "image",
        "id": msg.id,
        "sender_id": me.id,
        "image_url": url,
        "created_at": msg.created_at.isoformat()
    })
    return RedirectResponse(f"/chat/{room_id}", status_code=303)