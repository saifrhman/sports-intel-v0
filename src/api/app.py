from fastapi import FastAPI, HTTPException
from typing import List, Dict
import math

from src.utils.db_read import read_sql_df
from src.models.ratings.bayesian_team_ratings import BayesianTeamRater, ModelConfig

app = FastAPI(
    title="Sports Intelligence Internal API",
    description="Internal decision-support API for ratings and simulations",
    version="0.1.0",
)

MODEL_VERSION = "bayes-v0"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/teams/ratings")
def get_team_ratings():
    df = read_sql_df("""
        SELECT
            team_id,
            mu,
            sigma,
            last_match_date,
            model_version,
            updated_at
        FROM analytics.team_ratings_current
        WHERE model_version = %s
        ORDER BY mu DESC
    """, params=(MODEL_VERSION,))

    return df.to_dict(orient="records")


@app.get("/teams/simulations")
def get_team_simulations():
    df = read_sql_df("""
        SELECT
            team_id,
            p_win,
            p_draw,
            p_loss,
            avg_goal_diff,
            simulations,
            model_version,
            updated_at
        FROM analytics.team_simulation_summary
        WHERE model_version = %s
        ORDER BY p_win DESC
    """, params=(MODEL_VERSION,))

    return df.to_dict(orient="records")


@app.get("/predict")
def predict_match(home_team_id: str, away_team_id: str):
    ratings = read_sql_df("""
        SELECT team_id, mu, sigma
        FROM analytics.team_ratings_current
        WHERE team_id IN (%s, %s)
    """, params=(home_team_id, away_team_id))

    if len(ratings) != 2:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    data = ratings.set_index("team_id").to_dict("index")

    rater = BayesianTeamRater(ModelConfig(model_version=MODEL_VERSION))
    rater.teams[home_team_id] = rater._get_team(home_team_id)
    rater.teams[away_team_id] = rater._get_team(away_team_id)

    rater.teams[home_team_id].mu = data[home_team_id]["mu"]
    rater.teams[home_team_id].var = data[home_team_id]["sigma"] ** 2

    rater.teams[away_team_id].mu = data[away_team_id]["mu"]
    rater.teams[away_team_id].var = data[away_team_id]["sigma"] ** 2

    p_home, p_draw, p_away = rater.predict_probs(
        home_team_id, away_team_id, is_home=True
    )

    return {
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "p_home_win": p_home,
        "p_draw": p_draw,
        "p_away_win": p_away,
    }
