# Sports Intelligence v0

End-to-end sports data + modeling pipeline:
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
