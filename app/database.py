from pymongo import MongoClient
from pymongo.database import Database
from typing import Generator, Optional
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL")
DB_NAME: str = os.getenv("MONGODB_DB_NAME", "fastapi_db")

if not MONGODB_URL:
    raise ValueError("MONGODB_URL is missing in .env")

client: MongoClient = MongoClient(MONGODB_URL)
db: Database = client[DB_NAME]


def get_db() -> Generator[Database, None, None]:
    yield db
