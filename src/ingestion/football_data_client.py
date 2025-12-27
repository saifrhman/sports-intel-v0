import httpx


BASE_URL = "https://api.football-data.org/v4"


def fetch_matches(api_token: str, date_from: str, date_to: str) -> dict:
    """
    Fetch matches between two dates from football-data.org
    """
    headers = {"X-Auth-Token": api_token}
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
    }

    response = httpx.get(
        f"{BASE_URL}/matches",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
