from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, OperationFailure
from typing import Generator, Optional
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()

MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL")
DB_NAME: str = os.getenv("MONGODB_DB_NAME", "fastapi_db")

if not MONGODB_URL:
    raise ValueError("MONGODB_URL is missing in .env")

client: MongoClient = MongoClient(MONGODB_URL)
db: Database = client[DB_NAME]


def _ensure_users_email_uniqueness(database: Database) -> None:
    users = database["users"]

    # Backfill a normalized email field for existing users.
    users.update_many(
        {"email": {"$type": "string"}},
        [{"$set": {"email_normalized": {"$toLower": "$email"}}}],
    )

    try:
        users.create_index("email_normalized", unique=True, name="uniq_email_normalized")
    except (DuplicateKeyError, OperationFailure) as exc:
        # Keep API booting; index creation can fail if duplicate users already exist.
        logger.warning("Could not create unique index uniq_email_normalized: %s", exc)


_ensure_users_email_uniqueness(db)


def get_db() -> Generator[Database, None, None]:
    yield db
