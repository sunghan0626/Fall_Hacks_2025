# Database engine and initialization.
# TODO (A or C):
# - Create SQLModel engine (sqlite+aiosqlite:///./fitcoin.db by default)
# - init_db(): SQLModel.metadata.create_all(bind=engine)
# - Consider reading DATABASE_URL from env with default SQLite file.

# app/db.py
from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sweatmarket.db")
# SQLite: check_same_thread=False for multi-threaded Uvicorn
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

def init_db() -> None:
    """Create tables if they don't exist."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    """FastAPI dependency to get a DB session."""
    with Session(engine) as session:
        yield session
