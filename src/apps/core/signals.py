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
    """Signal to retrieve data after a Configuration instance is saved."""
    application = instance.application_configuration.name
    organization = instance.organization_configuration.name
    secret = instance.secret
    repository = instance.repository
    user = instance.user
    start_date=instance.start_date

    retrive_data(application=application, 
                 organization=organization, 
                 secret=secret, 
                 user=user,
                 repository=repository,
                 start_date=start_date
                 ),

    
    
