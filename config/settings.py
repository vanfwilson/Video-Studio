import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")

settings = Settings()
