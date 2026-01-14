from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = create_engine(
    # DATABASE_URL should be like: postgresql+psycopg2://user:pass@host:5432/dbname
    url=None,  # set in init_engine()
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False)

def init_engine(database_url: str):
    global engine
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal.configure(bind=engine)
    return engine
