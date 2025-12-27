import os
import psycopg2
import numpy as np
import pandas as pd

from src.utils.db_read import read_sql_df
from src.utils.db import get_connection
from src.models.simulation.monte_carlo import simulate_match


MODEL_VERSION = "bayes-v0"
N_SIMULATIONS = 5000


def main():
    ratings = read_sql_df("""
        SELECT team_id, mu, sigma
        FROM analytics.team_ratings_current
    """)

    teams = ratings.set_index("team_id").to_dict("index")

    team_stats: Dict[str, Dict[str, float]] = {
        t: {"win": 0, "draw": 0, "loss": 0, "gd": 0}
        for t in teams
    }

    conn = get_connection()
    cur = conn.cursor()

    for sim in range(N_SIMULATIONS):
        team_ids = list(teams.keys())
        np.random.shuffle(team_ids)

        # Pair teams randomly
        for i in range(0, len(team_ids) - 1, 2):
            home = team_ids[i]
            away = team_ids[i + 1]

            hg, ag, res = simulate_match(
                teams[home]["mu"], teams[home]["sigma"],
                teams[away]["mu"], teams[away]["sigma"],
            )

            # record
            cur.execute(
                """
                INSERT INTO analytics.match_simulations
                  (simulation_id, match_id, home_team_id, away_team_id,
                   home_goals, away_goals, result)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (sim, f"sim_{sim}_{home}_{away}", home, away, hg, ag, res)
            )

            if res == "H":
                team_stats[home]["win"] += 1
                team_stats[away]["loss"] += 1
            elif res == "A":
                team_stats[away]["win"] += 1
                team_stats[home]["loss"] += 1
            else:
                team_stats[home]["draw"] += 1
                team_stats[away]["draw"] += 1

            team_stats[home]["gd"] += hg - ag
            team_stats[away]["gd"] += ag - hg

    # Write summary
    for team_id, s in team_stats.items():
        total = s["win"] + s["draw"] + s["loss"]
        cur.execute(
            """
            INSERT INTO analytics.team_simulation_summary
              (team_id, p_win, p_draw, p_loss, avg_goal_diff,
               simulations, model_version)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (team_id) DO UPDATE SET
              p_win=EXCLUDED.p_win,
              p_draw=EXCLUDED.p_draw,
              p_loss=EXCLUDED.p_loss,
              avg_goal_diff=EXCLUDED.avg_goal_diff,
              simulations=EXCLUDED.simulations,
              model_version=EXCLUDED.model_version,
              updated_at=now()
            """,
            (
                team_id,
                s["win"] / total,
                s["draw"] / total,
                s["loss"] / total,
                s["gd"] / total,
                total,
                MODEL_VERSION,
            )
        )

    conn.commit()
    conn.close()

    print(f"Completed {N_SIMULATIONS} Monte Carlo simulations.")


if __name__ == "__main__":
    main()
