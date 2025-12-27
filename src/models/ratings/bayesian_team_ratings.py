from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple, Optional

import numpy as np
from scipy.special import expit  # sigmoid


@dataclass
class TeamState:
    mu: float
    var: float  # sigma^2
    last_date: Optional[date] = None


@dataclass
class ModelConfig:
    model_version: str = "bayes-v0"
    home_adv_mu: float = 0.15          # prior mean for home advantage
    home_adv_sigma: float = 0.25       # prior std for home advantage
    init_mu: float = 0.0               # prior mean team skill
    init_sigma: float = 1.0            # prior std team skill
    perf_beta: float = 1.0             # performance noise scale (higher = more uncertainty)
    tau_per_day: float = 0.01          # uncertainty growth per day (recency/decay)
    draw_margin: float = 0.20          # margin to model draws (bigger => more draws)
    max_step: float = 0.75             # cap update step for stability


class BayesianTeamRater:
    """
    Online Bayesian updates for team skill modeled as Normal(mu, var).
    Likelihood: ordered logistic style using skill difference + home advantage.
    We update mu and var via a Newton/Laplace-like step (assumed density filtering).
    """

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.teams: Dict[str, TeamState] = {}
        self.home_adv_mu = cfg.home_adv_mu
        self.home_adv_var = cfg.home_adv_sigma**2

    def _get_team(self, team_id: str) -> TeamState:
        if team_id not in self.teams:
            self.teams[team_id] = TeamState(mu=self.cfg.init_mu, var=self.cfg.init_sigma**2)
        return self.teams[team_id]

    def _apply_time_decay(self, team: TeamState, current_date: date) -> None:
        if team.last_date is None:
            team.last_date = current_date
            return
        delta_days = (current_date - team.last_date).days
        if delta_days > 0:
            # inflate uncertainty over time (recency/decay)
            team.var = team.var + (self.cfg.tau_per_day**2) * float(delta_days)
            team.last_date = current_date

    def predict_probs(self, home_id: str, away_id: str, is_home: bool = True) -> Tuple[float, float, float]:
        h = self._get_team(home_id)
        a = self._get_team(away_id)

        # Skill difference with home advantage
        home_adv = self.home_adv_mu if is_home else 0.0
        d = (h.mu - a.mu) + home_adv

        # Draw model via margin on latent scale
        m = self.cfg.draw_margin
        # p_home = P(d + eps > m), p_away = P(d + eps < -m), p_draw = remainder
        # eps ~ logistic(0, beta) -> sigmoid((x)/beta)
        beta = self.cfg.perf_beta
        p_home = expit((d - m) / beta)
        p_away = expit((-d - m) / beta)
        p_draw = max(0.0, 1.0 - p_home - p_away)

        # Normalize defensively
        s = p_home + p_draw + p_away
        if s <= 0:
            return (1/3, 1/3, 1/3)
        return (p_home / s, p_draw / s, p_away / s)

    def _loglik_grad_hess(self, d: float, y: str) -> Tuple[float, float]:
        """
        Compute gradient and Hessian of log-likelihood w.r.t. d (skill diff).
        y in {'H','D','A'}.
        Uses the same draw-margin probabilities.
        """
        beta = self.cfg.perf_beta
        m = self.cfg.draw_margin

        pH = expit((d - m) / beta)
        pA = expit((-d - m) / beta)
        pD = max(1e-12, 1.0 - pH - pA)

        # derivatives for pH and pA
        d_pH = (pH * (1.0 - pH)) / beta
        d_pA = -(pA * (1.0 - pA)) / beta  # derivative of expit((-d-m)/beta)

        # pD = 1 - pH - pA
        d_pD = -(d_pH + d_pA)

        # second derivatives
        dd_pH = (d_pH * (1.0 - 2.0 * pH)) / beta
        dd_pA = (d_pA * (1.0 - 2.0 * pA)) / beta
        dd_pD = -(dd_pH + dd_pA)

        if y == "H":
            p = max(1e-12, pH)
            dp = d_pH
            ddp = dd_pH
        elif y == "A":
            p = max(1e-12, pA)
            dp = d_pA
            ddp = dd_pA
        else:
            p = pD
            dp = d_pD
            ddp = dd_pD

        # log p: grad = dp/p ; hess = (ddp/p) - (dp^2/p^2)
        grad = dp / p
        hess = (ddp / p) - (dp * dp) / (p * p)

        # hess should be negative near optimum; keep stable
        return grad, hess

    def update_match(self, match_date: date, home_id: str, away_id: str, result: str) -> Dict[str, float]:
        """
        Update home and away team posteriors given result in {'H','D','A'}.
        Returns prediction probs before update.
        """
        home = self._get_team(home_id)
        away = self._get_team(away_id)

        # recency/decay
        self._apply_time_decay(home, match_date)
        self._apply_time_decay(away, match_date)

        p_home, p_draw, p_away = self.predict_probs(home_id, away_id, is_home=True)

        # latent diff
        d = (home.mu - away.mu) + self.home_adv_mu

        grad_d, hess_d = self._loglik_grad_hess(d, result)

        # Prior on d: var_d = var_home + var_away + var_home_adv + beta^2 (extra noise)
        var_d = home.var + away.var + self.home_adv_var + (self.cfg.perf_beta**2)

        # Newton step on d with prior regularization:
        # posterior approx: grad_total = grad_lik - d/var_d ; hess_total = hess_lik - 1/var_d
        grad_total = grad_d - (d / var_d)
        hess_total = hess_d - (1.0 / var_d)

        # step = -grad/hess
        step = 0.0
        if hess_total != 0.0:
            step = -grad_total / hess_total
        step = float(np.clip(step, -self.cfg.max_step, self.cfg.max_step))

        # Allocate step to home/away proportional to their variances (more uncertain updates more)
        denom = home.var + away.var + 1e-12
        w_home = home.var / denom
        w_away = away.var / denom

        home.mu += w_home * step
        away.mu -= w_away * step

        # Update variances: simple shrinkage based on information gain
        info_gain = max(1e-9, -hess_total)
        # reduce uncertainty modestly; keep floors
        home.var = max(1e-4, home.var * (1.0 / (1.0 + w_home * info_gain * home.var)))
        away.var = max(1e-4, away.var * (1.0 / (1.0 + w_away * info_gain * away.var)))

        return {"p_home_win": p_home, "p_draw": p_draw, "p_away_win": p_away}
