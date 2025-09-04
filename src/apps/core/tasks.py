
import logging
from celery import shared_task, chain
from .extract_github.extract_eo import ExtractEO
from .extract_github.extract_cmpo import ExtractCMPO
from .extract_github.extract_ciro import ExtractCIRO
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db.utils import OperationalError, ProgrammingError
import json


logger = logging.getLogger(__name__)

@shared_task
def retrieve_github_data(organization, secret, repository):
    
    chain(
        retrieve_github_eo_data.si(organization,secret,repository),
        retrieve_github_cmpo_data.si(organization,secret,repository),
        retrieve_github_ciro_data.si(organization,secret,repository),
    )()


def setup_periodic_tasks(organization, secret, repository):
    try:
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.DAYS,
        )

        PeriodicTask.objects.update_or_create(
            name="Retrieve GitHub Data Daily",
            defaults={
                "interval": schedule,
                "task": "apps.core.services.retrieve_github_data",
                "args": json.dumps([organization, secret, repository]),
            },
        )

    except (OperationalError, ProgrammingError):
        pass    

@shared_task
def retrieve_github_eo_data(organization, secret, repository):
    logger.info (f" Retrieve EO Data")
    instance = ExtractEO(organization=organization, secret=secret, repository=repository)
    instance.run()
    logger.info (f"{organization} - {secret} - {repository}")

@shared_task
def retrieve_github_cmpo_data(organization, secret, repository):
    logger.info (f" Retrieve CMPO Data")
    instance = ExtractCMPO(organization=organization, secret=secret, repository=repository)
    instance.run()
    logger.info (f"{organization} - {secret} - {repository}")

@shared_task
def retrieve_github_ciro_data(organization, secret, repository):
    logger.info (f" Retrieve CIRO Data")
    instance = ExtractCIRO(organization=organization, secret=secret, repository=repository)
    instance.run()
    logger.info (f"{organization} - {secret} - {repository}")
