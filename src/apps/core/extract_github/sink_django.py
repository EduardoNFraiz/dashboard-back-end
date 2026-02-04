"""Django ORM Sink for GitHub data extraction.

This module provides a sink implementation that persists extracted GitHub data
into Django models using the ORM, replacing the Neo4j graph database approach.
"""

import os
import django
from typing import Any, Dict, Optional
from datetime import datetime, timezone, date
from django.db import transaction
from django.utils import timezone as django_timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from apps.eo.models import (
    Person, TeamMember, Team, OrganizationalRole,
    TeamMembership, Project, TeamPurpose,
    ProjectTeam, OrganizationalTeam
)
from apps.core.models import Organization, Configuration


class SinkDjango:
    """Handles connections and interactions with Django ORM for data persistence.
    
    This class provides methods to persist entities and relationships
    using Django's relational database models, mirroring the Neo4j sink interface.
    """
    
    def __init__(self) -> None:
        """Initialize the Django sink.
        
        No special initialization needed as Django ORM is already configured.
        """
        pass
    
    def get_or_create_organization(self, org_name: str) -> Organization:
        """Get or create an Organization instance by name.
        
        Args:
            org_name: Name of the organization
            
        Returns:
            Organization instance
        """
        org, created = Organization.objects.get_or_create(
            name=org_name
        )
        return org
    
    def get_or_create_person(self, login: str, email: Optional[str] = None) -> Person:
        """Get or create a Person instance.
        
        Args:
            login: GitHub login/username
            email: Optional email address
            
        Returns:
            Person instance
        """
        # Try to find by email first if provided
        if email:
            person, created = Person.objects.get_or_create(
                email=email,
                defaults={'name': login}
            )
            if not created and person.name != login:
                # Update name if it changed
                person.name = login
                person.save()
        else:
            # Find or create by name
            person, created = Person.objects.get_or_create(
                name=login,
                defaults={'email': None}
            )
        
        return person
    
    def get_or_create_team_member(self, person: Person) -> TeamMember:
        """Get or create a TeamMember instance for a Person.
        
        Args:
            person: Person instance
            
        Returns:
            TeamMember instance
        """
        team_member, created = TeamMember.objects.get_or_create(
            person=person
        )
        return team_member
    
    def get_or_create_team(self, team_data: Dict[str, Any], organization: Organization) -> Team:
        """Get or create a Team instance.
        
        Args:
            team_data: Dictionary containing team information (name, slug, etc.)
            organization: Organization instance
            
        Returns:
            OrganizationalTeam instance (specialized Team)
        """
        team_name = team_data.get('name', team_data.get('slug', 'Unknown Team'))
        
        # Create or get OrganizationalTeam (which inherits from Team)
        team, created = OrganizationalTeam.objects.get_or_create(
            name=team_name,
            organization=organization,
            defaults={'created_at': django_timezone.now()}
        )
        
        # Add purpose if available in team_data
        purpose_desc = team_data.get('description')
        if purpose_desc:
            TeamPurpose.objects.get_or_create(
                team=team,
                defaults={'description': purpose_desc}
            )
        
        return team
    
    def get_team_by_slug(self, slug: str) -> Optional[Team]:
        """Get a Team by its slug (name).
        
        Args:
            slug: Team slug/name
            
        Returns:
            Team instance or None
        """
        try:
            return Team.objects.get(name=slug)
        except Team.DoesNotExist:
            return None
    
    def get_or_create_project(self, project_data: Dict[str, Any], organization: Organization) -> Project:
        """Get or create a Project instance.
        
        Args:
            project_data: Dictionary containing project information
            organization: Organization instance
            
        Returns:
            Project instance
        """
        project_name = project_data.get('title', project_data.get('name', 'Unknown Project'))
        project_description = project_data.get('short_description', project_data.get('description', ''))
        
        project, created = Project.objects.get_or_create(
            name=project_name,
            organization=organization,
            defaults={'description': project_description}
        )
        
        if not created and project.description != project_description:
            project.description = project_description
            project.save()
        
        return project
    
    def get_or_create_organizational_role(self, role_name: str = "Member") -> OrganizationalRole:
        """Get or create an OrganizationalRole instance.
        
        Args:
            role_name: Name of the role (default: "Member")
            
        Returns:
            OrganizationalRole instance
        """
        role, created = OrganizationalRole.objects.get_or_create(
            name=role_name,
            defaults={'description': f'Default {role_name} role'}
        )
        return role
    
    def create_team_membership(
        self,
        team: Team,
        team_member: TeamMember,
        role: OrganizationalRole,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TeamMembership:
        """Create or update a TeamMembership.
        
        Args:
            team: Team instance
            team_member: TeamMember instance
            role: OrganizationalRole instance
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            TeamMembership instance
        """
        if start_date is None:
            start_date = datetime.now().date()
        
        membership, created = TeamMembership.objects.get_or_create(
            team=team,
            member=team_member,
            role=role,
            start_date=start_date,
            defaults={'end_date': end_date}
        )
        
        if not created and membership.end_date != end_date:
            membership.end_date = end_date
            membership.save()
        
        return membership
    
    @transaction.atomic
    def save_extraction_data(
        self,
        organization_name: str,
        teams_data: list,
        projects_data: list,
        team_members_data: list
    ) -> Dict[str, int]:
        """Save all extracted data in a single transaction.
        
        Args:
            organization_name: Organization name
            teams_data: List of team dictionaries
            projects_data: List of project dictionaries
            team_members_data: List of team member dictionaries
            
        Returns:
            Dictionary with counts of created/updated entities
        """
        stats = {
            'organizations': 0,
            'teams': 0,
            'projects': 0,
            'persons': 0,
            'team_members': 0,
            'memberships': 0
        }
        
        # Create/get organization
        organization = self.get_or_create_organization(organization_name)
        stats['organizations'] = 1
        
        # Create teams
        for team_data in teams_data:
            self.get_or_create_team(team_data, organization)
            stats['teams'] += 1
        
        # Create projects
        for project_data in projects_data:
            self.get_or_create_project(project_data, organization)
            stats['projects'] += 1
        
        # Create team members and memberships
        default_role = self.get_or_create_organizational_role("Member")
        
        for member_data in team_members_data:
            login = member_data.get('login')
            email = member_data.get('email')
            team_slug = member_data.get('team_slug')
            
            if not login:
                continue
            
            # Create person
            person = self.get_or_create_person(login, email)
            stats['persons'] += 1
            
            # Create team member
            team_member = self.get_or_create_team_member(person)
            stats['team_members'] += 1
            
            # Create membership if team exists
            if team_slug:
                team = self.get_team_by_slug(team_slug)
                if team:
                    self.create_team_membership(team, team_member, default_role)
                    stats['memberships'] += 1
        
        return stats

    def get_configuration(self, organization: Organization, repository: str) -> Optional[Configuration]:
        """Get the configuration for a specific organization and repository.
        
        Args:
            organization: Organization instance
            repository: Repository name
            
        Returns:
            Configuration instance or None
        """
        try:
            return Configuration.objects.filter(
                organization_configuration=organization,
                repository=repository
            ).first()
        except Exception:
            return None

    def save_configuration(self, organization: Organization, repository: str, last_retrieve_date: datetime) -> Configuration:
        """Save or update the configuration with the last retrieval date.
        
        Args:
            organization: Organization instance
            repository: Repository name
            last_retrieve_date: The date/time of the extraction
            
        Returns:
            Configuration instance
        """
        config, created = Configuration.objects.update_or_create(
            organization_configuration=organization,
            repository=repository,
            defaults={'start_date': last_retrieve_date}
        )
        return config
