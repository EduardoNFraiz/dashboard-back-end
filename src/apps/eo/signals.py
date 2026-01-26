import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Person, Team, TeamMembership

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Person)
def post_save_person(sender, instance, created, **kwargs):
    """Signal triggered after a Person instance is saved."""
    action = "created" if created else "updated"
    logger.info(f"EO Persona {instance.name} (ID: {instance.id}) was {action}.")

@receiver(post_save, sender=Team)
def post_save_team(sender, instance, created, **kwargs):
    """Signal triggered after a Team instance is saved."""
    action = "created" if created else "updated"
    logger.info(f"EO Team {instance.name} (ID: {instance.id}) was {action}.")

@receiver(post_save, sender=TeamMembership)
def post_save_membership(sender, instance, created, **kwargs):
    """Signal triggered after a TeamMembership instance is saved."""
    if created:
        logger.info(
            f"EO Membership created: {instance.member.person.name} joined {instance.team.name} "
            f"as {instance.role.name}."
        )
