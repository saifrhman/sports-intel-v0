from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from src.orchestration.weekly_pipeline import weekly_pipeline

Deployment.build_from_flow(
    flow=weekly_pipeline,
    name="weekly-sports-intel",
    schedules=[
        CronSchedule(cron="0 6 * * 1")  # Mondays at 06:00
    ],
    work_queue_name="default",
).apply()
