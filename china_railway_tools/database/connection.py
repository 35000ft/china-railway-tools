# database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import get_default_db_url

ASYNC_DATABASE_URL = get_default_db_url().replace("sqlite:///", "sqlite+aiosqlite:///")

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={
        # 0 means “no detect_types” → sqlite3 returns raw strings
        "detect_types": 0
    }
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()
