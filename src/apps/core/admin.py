from django.contrib import admin
from .models import Application, Configuration, Organization

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['id', 'organization_configuration','application_configuration', 'repository']
    list_display_links = ['id', 'organization_configuration','application_configuration','repository']
    search_fields = ['id', 'organization_configuration','application_configuration']
    list_per_page = 25
    ordering = ['-id']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    search_fields = ['id', 'name' ]
    list_per_page = 25
    ordering = ['-id']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']
    search_fields = ['id', 'name']
    list_per_page = 25
    ordering = ['-id']

