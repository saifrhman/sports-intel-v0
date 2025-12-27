import os
from datetime import date, timedelta

from src.ingestion.football_data_client import fetch_matches
from src.ingestion.raw_matches import insert_raw_match_payload


def main():
    api_token = os.getenv("FOOTBALL_DATA_TOKEN")
    if not api_token:
        raise RuntimeError("FOOTBALL_DATA_TOKEN is not set")

    yesterday = date.today() - timedelta(days=1)
    today = date.today()

    payload = fetch_matches(
        api_token=api_token,
        date_from=yesterday.isoformat(),
        date_to=today.isoformat(),
    )

    insert_raw_match_payload(
        source="football-data.org",
        payload=payload,
    )

    print("Inserted real match payload into raw.matches")


if __name__ == "__main__":
    main()
