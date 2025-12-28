# Sports Intelligence v0

End-to-end sports analytics and decision support system for team evaluation, probabilistic modeling, and simulation-driven insights.
This project demonstrates production-grade data engineering, Bayesian modeling, and simulation-based decision support, built as a founding-level v0 system.

## Overview

The platform ingests real-world football match data, normalizes it into analytics-ready schemas, applies Bayesian team rating models with uncertainty and recency effects, and runs Monte Carlo simulations to produce probabilistic outcomes.

It is designed for:
- Team and league evaluation
- Scenario analysis
- Investment-grade decision support (probabilities, not point estimates)

## Architecture
External APIs
     ↓
Python Ingestion
     ↓
PostgreSQL (raw)
     ↓
dbt (staging → analytics)
     ↓
Bayesian Rating Model (Python)
     ↓
Monte Carlo Simulations
     ↓
PostgreSQL (decision tables)
     ↓
Prefect Orchestration (scheduled, retryable)

### Key principle:

- dbt handles SQL transformations only
- Python (src/) handles modeling, simulation, orchestration

## Data Pipeline
1. Ingestion (Python)
   - API ingestion with incremental updates
   - Raw JSON stored in PostgreSQL
   - Handles missing fields and partial updates

2. Transformations (dbt)
   - raw → staging → analytics
   - Analytics-ready schemas
   - Data quality tests and documentation via dbt
   - Explicit modeling grain (team–match level)

3. Modeling Inputs
   - One row per team per match
   - Home/away context
   - Goals for/against
   - Win/draw/loss encoded numerically

## Bayesian Team Rating Model
Each team’s strength is modeled as a Normal distribution:
> skill_team ~ Normal(μ, σ²)
### Model characteristics
- Bayesian priors for new teams
- Online posterior updates after each match
- Uncertainty tracking (σ reflects confidence)
- Recency/decay via time-based variance inflation
- Home advantage modeled explicitly
- Probabilistic outcomes (win / draw / loss)

## Monte Carlo Simulations
Using posterior team skill distributions:
- Thousands of simulated matches are run
- Team strengths are sampled from their posteriors
- Goals are generated probabilistically
- Outcome distributions are aggregated

### Outputs
- Win / draw / loss probabilities
- Average goal differential
- Risk-aware team profiles
This enables decision-making under uncertainty, not point estimates.

## Orchestration (Prefect)
The entire system is orchestrated using **Prefect 2.x**:
### Flow
> dbt run
> → Bayesian ratings update
> → Monte Carlo simulations
### Features
- Retries and failure handling
- Observable runs via Prefect UI
- Schedulable (e.g. weekly refresh)
- Ready for backfills and extensions

## Tech Stack
- Python (data ingestion, modeling, simulation)
- PostgreSQL (core data store)
- dbt (transformations, tests, documentation)
- Prefect 2.x (orchestration)
- NumPy / SciPy / Pandas (probabilistic modeling)
- Docker (local infra)

## Project Structure
sports-intel-v0/
├── src/                  # Python application layer
│   ├── ingestion/
│   ├── models/
│   │   ├── ratings/
│   │   └── simulation/
│   ├── orchestration/
│   └── utils/
├── dbt/                  # SQL transformations only
│   └── sports_intel/
├── infra/
└── README.md

## Next Extensions (Planned)

- FastAPI internal endpoints
- Player-level Bayesian models
- Calibration & reliability analysis
- Betting market integration
- Scenario-based league projections

## How to Run Locally
# activate environment
source .venv/bin/activate

# run dbt
dbt run

# update ratings
python -m src.models.backtest.run_ratings

# run simulations
python -m src.models.simulation.run_simulations

# orchestrated run
python -m src.orchestration.weekly_pipeline



### Evaluation
- Backtested on historical matches
- Log loss computed per match
- Results persisted to Postgres for analysis


## End-to-end sports data + modeling pipeline:
- Ingestion (APIs/scraping)
- Orchestration (Prefect)
- Storage (PostgreSQL)
- Transformations (dbt)
- Modeling (Bayesian ratings)
- Serving (FastAPI)
- Analyst tool (Streamlit)

## Repo layout
- src/: core Python package
- orchestration/: Prefect flows
- dbt/: transformations + tests
- apps/: API + analyst console
- infra/: docker-compose and infrastructure

  ## Author
  Built by Saif Ur Rehman
  Focus: Data Engineering, Probablistic Modelling, Decision Grade Sports Analytics
