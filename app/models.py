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

    # Email verification (we skip verification but keep fields)
    is_active: bool = Field(default=False)
    email_confirmed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)