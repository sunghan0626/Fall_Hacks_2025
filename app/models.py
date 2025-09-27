# app/models.py — merged Part A (User) + Part D (Tx, Order)

from typing import Optional
from datetime import datetime, date
from sqlmodel import SQLModel, Field, UniqueConstraint

# ---------- Part A: User ----------
class User(SQLModel, table=True):
    __tablename__ = "users"  # NOTE: use "users.id" in foreign keys
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
    avatar_url: Optional[str] = None  # "/static/avatars/1.jpg"
    sport: Optional[str] = None       # "gym","soccer","running","others"
    time_window: Optional[str] = None
    region: Optional[str] = None
    goal: Optional[str] = None

    # Email verification flags (kept for future)
    is_active: bool = Field(default=False)
    email_confirmed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Part D: Wallet & DEX ----------
class Tx(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # matches __tablename__ above
    amount: int                 # +earn, -spend
    kind: str                   # 'earn' | 'spend' | 'bonus'
    note: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")  # matches __tablename__ above
    side: str                   # 'buy' | 'sell'
    price: int                  # demo units
    amount: int                 # coins
    created_at: datetime = Field(default_factory=datetime.utcnow)
