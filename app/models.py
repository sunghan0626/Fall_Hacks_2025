# app/models.py — merged Part A (User, Post/Comment, Chat) + Part D (Tx, Order)

from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field, UniqueConstraint

# ---------- Part A: User ----------
class User(SQLModel, table=True):
    __tablename__ = "users"  # use "users.id" in foreign keys
    __table_args__ = (UniqueConstraint("username", name="uq_username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: Optional[str] = Field(default=None, index=True)
    password_hash: str

    # Wallet (Part D)
    coins: int = 0

    # Profile (Part A)
    nickname: Optional[str] = Field(default=None, index=True)  # 3–12 chars
    birth_date: Optional[date] = None
    gender: Optional[str] = None  # "male" | "female" | "prefer_not_to_answer"
    avatar_url: Optional[str] = None  # e.g., "/static/avatars/1.jpg"
    sport: Optional[str] = None
    time_window: Optional[str] = None
    region: Optional[str] = None
    goal: Optional[str] = None

    # Account flags
    is_active: bool = Field(default=False)
    email_confirmed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Part A: Community ----------
class Post(SQLModel, table=True):
    __tablename__ = "posts"
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    image_url: Optional[str] = None        # e.g., "/static/post_images/xxx.jpg"
    caption: str                           # post text
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Part A: DM ----------
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
    content: str = ""                      # allow empty when image-only
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Part D: Wallet & DEX ----------
class Tx(SQLModel, table=True):
    __tablename__ = "txs"  # explicit to avoid generic names
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    amount: int                 # +earn, -spend
    kind: str                   # 'earn' | 'spend' | 'bonus'
    note: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(SQLModel, table=True):
    __tablename__ = "orders"  # 'order' can be reserved in some DBs
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    side: str                   # 'buy' | 'sell'
    price: int                  # demo units
    amount: int                 # coins
    created_at: datetime = Field(default_factory=datetime.utcnow)
