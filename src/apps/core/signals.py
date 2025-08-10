from .models import Configuration, Organization
import logging
from .services import retrive_data
from django.db.models.signals import (
    
    post_save,
    
    
)
from django.dispatch import receiver


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Configuration)
def post_save_configuration(sender, instance, created, raw, using, update_fields, **kwargs):
    logger.info(f"Signal::Configuration - {instance}")
    
    application = instance.application_configuration.name
    organization = instance.organization_configuration.name
    secret = instance.secret
    repository = instance.respository
    user = instance.user

    retrive_data(application=application, organization=organization, secret=secret, user=user,repository=repository),

@receiver(post_save, sender=Organization)
def post_save_configuration(sender, instance, created, raw, using, update_fields, **kwargs):
    logger.info(f"Signal::Organization - {instance}")
    
    
