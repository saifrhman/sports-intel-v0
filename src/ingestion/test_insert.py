from src.ingestion.raw_matches import insert_raw_match_payload


def main():
    fake_payload = {
        "match_id": 12345,
        "home_team": "Team A",
        "away_team": "Team B",
        "score": {"home": 2, "away": 1},
    }

    insert_raw_match_payload(
        source="manual_test",
        payload=fake_payload,
    )

    print("Inserted test payload into raw.matches")


if __name__ == "__main__":
    main()
