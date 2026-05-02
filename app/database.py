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


def _ensure_refresh_token_indexes(database: Database) -> None:
    refresh_tokens = database["refresh_tokens"]

    index_specs = [
        (("tokenHash", 1), {"unique": True, "name": "uniq_refresh_token_hash"}),
        (("userId", 1), {"name": "idx_refresh_tokens_user_id"}),
        (("expiresAt", 1), {"expireAfterSeconds": 0, "name": "ttl_refresh_tokens_expires_at"}),
    ]

    for field, options in index_specs:
        try:
            refresh_tokens.create_index([field], **options)
        except OperationFailure as exc:
            logger.warning("Could not create refresh token index %s: %s", options["name"], exc)


_ensure_users_email_uniqueness(db)
_ensure_refresh_token_indexes(db)


def get_db() -> Generator[Database, None, None]:
    yield db
