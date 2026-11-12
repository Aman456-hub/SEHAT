import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Get database URL from environment or default to a local SQLite file.
# If database URL uses postgresql://, translate it to postgresql+asyncpg:// for async compatibility.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sehat.db")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Configure the engine arguments based on database type.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread=False for multi-threaded async execution.
    connect_args = {"check_same_thread": False}

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL logging during debugging
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all models
class Base(DeclarativeBase):
    pass

async def get_db():
    """
    Dependency generator function that yields an active async database session.
    Ensures the session is closed after the request is finished.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
