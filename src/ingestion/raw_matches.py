import json
import hashlib
from datetime import datetime, timezone

from src.utils.db import get_connection


def compute_checksum(payload: dict) -> str:
    """
    Compute a deterministic checksum for a JSON payload.
    """
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.md5(payload_str.encode("utf-8")).hexdigest()


def insert_raw_match_payload(source: str, payload: dict) -> None:
    """
    Insert a raw payload into raw.matches.
    """
    checksum = compute_checksum(payload)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw.matches (source, fetched_at, payload, checksum)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    source,
                    datetime.now(timezone.utc),
                    json.dumps(payload),
                    checksum,
                ),
            )
        conn.commit()
    finally:
        conn.close()
