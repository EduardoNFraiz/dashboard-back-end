from django.db import models
from apps.core.models import Organization

class Person(models.Model):
    """
    Represents an individual person.

    Attributes:
        name (str): The full name of the person.
        email (str): The unique email address of the person.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of when the record was last updated.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'eo_person'
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    """
    Represents a specialization of a Person playing a role within teams.

    Attributes:
        person (Person): Reference to the base Person record.
    """
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='team_member')
    
    class Meta:
        db_table = 'eo_team_member'

    def __str__(self):
        return f"Member: {self.person.name}"

class Team(models.Model):
    """
    Base entity representing a collective unit or team.

    Attributes:
        name (str): The name of the team.
        created_at (datetime): Timestamp of when the record was created.
    """
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'eo_team'

    def __str__(self):
        return self.name

class OrganizationalRole(models.Model):
    """
    Defines available roles within an organization or team.

    Attributes:
        name (str): Unique name of the role (e.g., Coordinator, Member).
        description (str): Detailed description of the role's responsibilities.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'eo_organizational_role'

    def __str__(self):
        return self.name

class TeamPurpose(models.Model):
    """
    Defines the objective or purpose of a specific Team.

    Attributes:
        team (Team): The team this purpose belongs to.
        description (str): Statement of purpose.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='purposes')
    description = models.TextField()

    class Meta:
        db_table = 'eo_team_purpose'

class TeamMembership(models.Model):
    """
    Mediates the relationship between a Team, a TeamMember, and an OrganizationalRole.

    Acts as a bridge to document when and in what capacity a person participated in a team.

    Attributes:
        team (Team): Reference to the specific Team.
        member (TeamMember): Reference to the specific TeamMember.
        role (OrganizationalRole): The role played by the member.
        start_date (date): Date when the membership started.
        end_date (date): Optional date when the membership ended.
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    member = models.ForeignKey(TeamMember, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(OrganizationalRole, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'eo_team_membership'
        unique_together = ('team', 'member', 'role', 'start_date')

class Project(models.Model):
    """
    Represents a specific project or initiative.

    Attributes:
        name (str): The title of the project.
        description (str): Brief summary of the project.
        organization (Organization): The organization overseeing the project.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')

    class Meta:
        db_table = 'eo_project'

    def __str__(self):
        return self.name

class ProjectTeam(Team):
    """
    A specialized Team that is formed specifically for a Project.

    Attributes:
        project (Project): The project this team is dedicated to.
    """
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='project_team')

    class Meta:
        db_table = 'eo_project_team'

class OrganizationalTeam(Team):
    """
    A specialized Team that belongs to an Organization.

    Attributes:
        organization (Organization): The organization this team belongs to.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')

    class Meta:
        db_table = 'eo_organizational_team'
