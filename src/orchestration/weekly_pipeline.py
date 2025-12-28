from prefect import flow
from src.orchestration.tasks import run_dbt, run_ratings, run_simulations


@flow(name="sports-intel-weekly-pipeline")
def weekly_pipeline():
    run_dbt()
    run_ratings()
    run_simulations()


if __name__ == "__main__":
    weekly_pipeline()