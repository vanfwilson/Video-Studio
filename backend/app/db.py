from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
SessionLocal = None
engine = None

def init_engine(database_url: str):
    global engine, SessionLocal
    engine = create_engine(database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_engine first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
