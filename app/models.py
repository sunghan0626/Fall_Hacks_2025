# app/models.py
from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field, UniqueConstraint

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: Optional[str] = Field(default=None, index=True)
    password_hash: str

    # Profile
    nickname: Optional[str] = Field(default=None, index=True)   # 3–12 chars
    birth_date: Optional[date] = None
    gender: Optional[str] = None                                # "male"|"female"|"prefer_not_to_answer"
    avatar_url: Optional[str] = None                            # "/static/avatars/1.jpg"
    sport: Optional[str] = None                                 # "gym","soccer","running","others"
    time_window: Optional[str] = None
    region: Optional[str] = None
    goal: Optional[str] = None

    # Email verification (optional)
    is_active: bool = Field(default=False)
    email_confirmed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(index=True, foreign_key="users.id")
    image_url: str                                  # "/static/posts/xxx.jpg"
    caption: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(index=True, foreign_key="posts.id")
    author_id: int = Field(index=True, foreign_key="users.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- NEW: DM models ----------
class ChatRoom(SQLModel, table=True):
    __tablename__ = "chat_rooms"
    id: Optional[int] = Field(default=None, primary_key=True)

    # 1:1 room (unordered pair)
    user1_id: int = Field(foreign_key="users.id")
    user2_id: int = Field(foreign_key="users.id")

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="chat_rooms.id")

    sender_id: int = Field(foreign_key="users.id")
    content: str = ""                         # allow empty when image-only
    image_url: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)