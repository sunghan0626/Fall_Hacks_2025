# SQLModel data models.
# TODO (A):
# - User(id, handle, password_hash, coins, created_at)
# - Profile(user_id unique, sports, timezones, regions, goals)
#
# TODO (B):
# - Post(author_id, title, body, tags, created_at)
# - Comment(post_id, author_id, body, created_at)
#
# TODO (C):
# - Offer(owner_id, title, when_text, where_text, is_open, lat?, lon?, created_at)
# - Session(offer_id, host_id, guest_id, started_at, confirmed_host, confirmed_guest, qr_nonce)
#
# TODO (D):
# - Tx(user_id, amount, kind['earn','spend','bonus'], note, created_at)
# - Order(user_id, side['buy','sell'], price, amount, created_at)

# app/models.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, UniqueConstraint

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: Optional[str] = Field(default=None, index=True)
    password_hash: str

    # --- Profile fields (simple strings for speed; refine later) ---
    sport: Optional[str] = None          # ex) "헬스,축구"
    time_window: Optional[str] = None    # ex) "주중 저녁"
    region: Optional[str] = None         # ex) "버나비/로히드"
    goal: Optional[str] = None           # ex) "다이어트"

    created_at: datetime = Field(default_factory=datetime.utcnow)
