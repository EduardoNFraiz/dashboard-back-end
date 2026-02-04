from django.contrib import admin
from .models import (
    Person, TeamMember, Team, OrganizationalRole, 
    TeamPurpose, TeamMembership, Project, 
    ProjectTeam, OrganizationalTeam
)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Person model.
    """
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TeamMember model.
    """
    list_display = ('person',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Team model.
    """
    list_display = ('name', 'created_at')

@admin.register(OrganizationalRole)
class OrganizationalRoleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the OrganizationalRole model.
    """
    list_display = ('name',)

@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    """
    Admin configuration for the TeamMembership model.
    """
    list_display = ('team', 'member', 'role', 'start_date', 'end_date')
    list_filter = ('team', 'role')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Project model.
    """
    list_display = ('name', 'organization')

admin.site.register(TeamPurpose)
admin.site.register(ProjectTeam)
admin.site.register(OrganizationalTeam)
