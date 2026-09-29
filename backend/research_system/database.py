"""
Database configuration and session management.
Centralized database initialization and session factory.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./khronos_research.db")
# For production: use PostgreSQL
# DATABASE_URL = "postgresql://user:password@localhost/khronos_research"

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration (good for development)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL logging
    )
else:
    # PostgreSQL configuration (production)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    from .schema import Base
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {DATABASE_URL}")


def drop_all_tables():
    """Drop all tables (use with caution!)."""
    from .schema import Base
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


if __name__ == "__main__":
    init_db()
