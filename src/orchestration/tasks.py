import subprocess
from prefect import task


@task(retries=3, retry_delay_seconds=30)
def run_dbt():
    subprocess.run(
        ["dbt", "run"],
        cwd="dbt/sports_intel",
        check=True,
    )


@task(retries=3, retry_delay_seconds=30)
def run_ratings():
    subprocess.run(
        ["python", "-m", "src.models.backtest.run_ratings"],
        check=True,
    )


@task(retries=2, retry_delay_seconds=30)
def run_simulations():
    subprocess.run(
        ["python", "-m", "src.models.simulation.run_simulations"],
        check=True,
    )
