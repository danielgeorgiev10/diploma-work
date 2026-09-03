"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
