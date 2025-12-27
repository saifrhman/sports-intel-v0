import os
from math import log
from datetime import datetime

import pandas as pd
import psycopg2

from src.utils.db_read import read_sql_df
from src.utils.db import get_connection
from src.models.ratings.bayesian_team_ratings import BayesianTeamRater, ModelConfig


def safe_log(x: float) -> float:
    return log(max(1e-12, min(1.0, x)))


def main():
    # Ensure env var set
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")

    cfg = ModelConfig(model_version="bayes-v0")
    rater = BayesianTeamRater(cfg)

    # Pull finished matches in time order
    df = read_sql_df("""
        SELECT
          match_id,
          match_date,
          home_team_id,
          away_team_id,
          result
        FROM analytics.fact_matches
        WHERE is_finished = true
          AND result IS NOT NULL
        ORDER BY match_date ASC, match_id ASC
    """)

    if df.empty:
        print("No finished matches available in analytics.fact_matches yet.")
        return

    preds = []

    for row in df.itertuples(index=False):
        match_id = str(row.match_id)
        match_date = pd.to_datetime(row.match_date).date()
        home_id = str(row.home_team_id)
        away_id = str(row.away_team_id)
        result = str(row.result)

        p = rater.update_match(match_date, home_id, away_id, result)

        # log loss for 3-class
        if result == "H":
            ll = -safe_log(p["p_home_win"])
        elif result == "A":
            ll = -safe_log(p["p_away_win"])
        else:
            ll = -safe_log(p["p_draw"])

        preds.append({
            "match_id": match_id,
            "match_date": match_date,
            "home_team_id": home_id,
            "away_team_id": away_id,
            "p_home_win": p["p_home_win"],
            "p_draw": p["p_draw"],
            "p_away_win": p["p_away_win"],
            "actual_result": result,
            "log_loss": ll,
        })

    preds_df = pd.DataFrame(preds)

    # Write match_predictions + team_ratings_current
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Upsert predictions
            for r in preds_df.itertuples(index=False):
                cur.execute(
                    """
                    INSERT INTO analytics.match_predictions
                      (match_id, match_date, home_team_id, away_team_id,
                       p_home_win, p_draw, p_away_win, actual_result, log_loss, model_version)
                    VALUES
                      (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (match_id) DO UPDATE SET
                      match_date=EXCLUDED.match_date,
                      home_team_id=EXCLUDED.home_team_id,
                      away_team_id=EXCLUDED.away_team_id,
                      p_home_win=EXCLUDED.p_home_win,
                      p_draw=EXCLUDED.p_draw,
                      p_away_win=EXCLUDED.p_away_win,
                      actual_result=EXCLUDED.actual_result,
                      log_loss=EXCLUDED.log_loss,
                      model_version=EXCLUDED.model_version,
                      created_at=now()
                    """,
                    (r.match_id, r.match_date, r.home_team_id, r.away_team_id,
                     float(r.p_home_win), float(r.p_draw), float(r.p_away_win),
                     r.actual_result, float(r.log_loss), cfg.model_version)
                )

            # Upsert current ratings
            now = datetime.utcnow()
            for team_id, st in rater.teams.items():
                sigma = st.var ** 0.5
                cur.execute(
                    """
                    INSERT INTO analytics.team_ratings_current
                      (team_id, mu, sigma, last_match_date, model_version, updated_at)
                    VALUES
                      (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (team_id) DO UPDATE SET
                      mu=EXCLUDED.mu,
                      sigma=EXCLUDED.sigma,
                      last_match_date=EXCLUDED.last_match_date,
                      model_version=EXCLUDED.model_version,
                      updated_at=EXCLUDED.updated_at
                    """,
                    (team_id, float(st.mu), float(sigma), st.last_date, cfg.model_version, now)
                )

        conn.commit()
    finally:
        conn.close()

    print(f"Done. Wrote {len(preds_df)} predictions and {len(rater.teams)} team ratings.")
    print(f"Mean log loss: {preds_df['log_loss'].mean():.4f}")


if __name__ == "__main__":
    main()
