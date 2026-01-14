from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    original_filename = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    status = Column(String, default="uploading")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
