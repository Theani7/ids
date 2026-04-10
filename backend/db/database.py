from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./ids_database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all database tables."""
    from backend.db.models import Alert  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency-injectable database session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
