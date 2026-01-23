from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

def init_engine(database_url: str):
    global engine
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal.configure(bind=engine)
    return engine
