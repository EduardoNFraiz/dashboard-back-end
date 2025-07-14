from celery import shared_task
from .extract_github.extract_eo import ExtractEO
from .extract_github.extract_cmpo import ExtractCMPO
from .extract_github.extract_ciro import ExtractCIRO
import logging
logger = logging.getLogger(__name__)
from celery import chain

def retrieve_github_data(organization, secret, repository):
    
    chain(
        retrieve_github_eo_data.si(organization,secret,repository),
        retrieve_github_cmpo_data.si(organization,secret,repository),
        retrieve_github_ciro_data.si(organization,secret,repository),
    )()
    

@shared_task
def retrieve_github_eo_data(organization, secret, repositories):
    logger.info (f" Retrieve EO Data")
    ExtractEO().run()
    logger.info (f"{organization} - {secret} - {repositories}")

@shared_task
def retrieve_github_cmpo_data(organization, secret, repositories):
    logger.info (f" Retrieve CMPO Data")
    ExtractCMPO().run()
    logger.info (f"{organization} - {secret} - {repositories}")

@shared_task
def retrieve_github_ciro_data(organization, secret, repositories):
    logger.info (f" Retrieve CIRO Data")
    ExtractCIRO().run()
    logger.info (f"{organization} - {secret} - {repositories}")