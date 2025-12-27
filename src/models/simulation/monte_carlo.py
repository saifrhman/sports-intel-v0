import numpy as np
from typing import Dict, Tuple


def simulate_match(
    mu_home: float,
    sigma_home: float,
    mu_away: float,
    sigma_away: float,
    home_adv: float = 0.15,
    goal_scale: float = 1.2
) -> Tuple[int, int, str]:
    """
    Simulate a single match using sampled team strengths.
    """

    # Sample latent strengths
    home_strength = np.random.normal(mu_home + home_adv, sigma_home)
    away_strength = np.random.normal(mu_away, sigma_away)

    # Convert strength difference to expected goals
    lambda_home = np.exp(home_strength / goal_scale)
    lambda_away = np.exp(away_strength / goal_scale)

    home_goals = np.random.poisson(lambda_home)
    away_goals = np.random.poisson(lambda_away)

    if home_goals > away_goals:
        result = "H"
    elif away_goals > home_goals:
        result = "A"
    else:
        result = "D"

    return home_goals, away_goals, result
