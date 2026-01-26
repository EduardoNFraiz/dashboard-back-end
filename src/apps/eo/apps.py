from django.apps import AppConfig

class EoConfig(AppConfig):
    """
    Configuration for the EO app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.eo'
    label = 'eo'

    def ready(self):
        import apps.eo.signals
