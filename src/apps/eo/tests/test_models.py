import pytest
from django.utils import timezone
from apps.eo.models import (
    Person, TeamMember, Team, OrganizationalRole, 
    TeamPurpose, TeamMembership, Project, 
    ProjectTeam, OrganizationalTeam
)
from apps.core.models import Organization

@pytest.mark.django_db
class TestEOModels:
    """
    Test suite for Enterprise Ontology (EO) models.
    """

    def test_person_creation(self):
        person = Person.objects.create(name="John Doe", email="john@example.com")
        assert person.name == "John Doe"
        assert str(person) == "John Doe"

    def test_team_member_link(self):
        person = Person.objects.create(name="Jane Doe")
        member = TeamMember.objects.create(person=person)
        assert member.person == person
        assert str(member) == "Member: Jane Doe"

    def test_team_and_purpose(self):
        team = Team.objects.create(name="Alpha Team")
        purpose = TeamPurpose.objects.create(team=team, description="To lead research")
        assert team.purposes.count() == 1
        assert team.purposes.first().description == "To lead research"

    def test_organizational_role(self):
        role = OrganizationalRole.objects.create(name="Coordinator", description="Handles organization")
        assert role.name == "Coordinator"

    def test_team_membership_complex_mediation(self):
        # Setup
        org = Organization.objects.create(name="University X")
        person = Person.objects.create(name="Dr. Smith")
        member = TeamMember.objects.create(person=person)
        team = Team.objects.create(name="Research Group A")
        role = OrganizationalRole.objects.create(name="Lead")
        
        # Act
        membership = TeamMembership.objects.create(
            team=team,
            member=member,
            role=role,
            start_date=timezone.now().date()
        )
        
        # Assert
        assert team.memberships.count() == 1
        assert membership.team == team
        assert membership.member == member
        assert membership.role == role

    def test_project_and_project_team(self):
        org = Organization.objects.create(name="Company Y")
        project = Project.objects.create(name="Project Z", organization=org)
        project_team = ProjectTeam.objects.create(name="Team Z", project=project)
        
        assert project.project_team == project_team
        assert project_team.project == project
        # Verify inheritance
        assert Team.objects.filter(id=project_team.id).exists()

    def test_organizational_team(self):
        org = Organization.objects.create(name="Dept of Science")
        org_team = OrganizationalTeam.objects.create(name="Lab 101", organization=org)
        
        assert org.teams.count() == 1
        assert org_team.organization == org
