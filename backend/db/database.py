import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Go up two levels: db/ -> backend/ -> project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'ids_database.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all database tables."""
    from backend.db.models import Alert, TrafficStats, ProtocolStats, DNSQuery, HTTPRequest  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency-injectable database session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
