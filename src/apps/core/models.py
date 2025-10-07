from django.db import models
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import User
User._meta.get_field('email')._unique = True

class Organization (models.Model):
    name = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'organization'
    
    def __str__(self):
        return self.name

class Application(models.Model):
    name = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'application'
    
    def __str__(self):
        return self.name

class Configuration(models.Model):
    
    secret = models.CharField(max_length=300, null=True, blank=True)
    user = models.CharField(max_length=300, null=True, blank=True)
    repository = models.CharField(max_length=300, null=True, blank=True)
    organization_configuration = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE, related_name="organization_%(class)s")
    application_configuration = models.ForeignKey(Application, blank=True, null=True, on_delete=models.CASCADE, related_name="application_%(class)s")
    '''start_date = models.DateTimeField(blank=True, null=True)'''
    

    def __str__(self):
        return f"{self.organization_configuration}-{self.application_configuration}-{self.secret}-{self.repository}"

    class Meta:
        db_table = 'configuration'

