from rest_framework import serializers
from .models import (
    Person, TeamMember, Team, OrganizationalRole, 
    TeamPurpose, TeamMembership, Project, 
    ProjectTeam, OrganizationalTeam
)
from apps.core.serializers import OrganizationReadSerializer

class PersonSerializer(serializers.ModelSerializer):
    """Serializer for the Person model."""
    class Meta:
        model = Person
        fields = '__all__'

class TeamMemberReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for TeamMember, including nested Person data."""
    person = PersonSerializer(read_only=True)
    
    class Meta:
        model = TeamMember
        fields = '__all__'

class TeamMemberWriteSerializer(serializers.ModelSerializer):
    """Write serializer for TeamMember."""
    class Meta:
        model = TeamMember
        fields = '__all__'

class TeamPurposeSerializer(serializers.ModelSerializer):
    """Serializer for the TeamPurpose model."""
    class Meta:
        model = TeamPurpose
        fields = '__all__'

class TeamReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for Team, including purposes."""
    purposes = TeamPurposeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = '__all__'

class TeamWriteSerializer(serializers.ModelSerializer):
    """Write serializer for Team."""
    class Meta:
        model = Team
        fields = '__all__'

class OrganizationalRoleSerializer(serializers.ModelSerializer):
    """Serializer for the OrganizationalRole model."""
    class Meta:
        model = OrganizationalRole
        fields = '__all__'

class TeamMembershipReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for TeamMembership, including nested data."""
    team = TeamReadSerializer(read_only=True)
    member = TeamMemberReadSerializer(read_only=True)
    role = OrganizationalRoleSerializer(read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = '__all__'

class TeamMembershipWriteSerializer(serializers.ModelSerializer):
    """Write serializer for TeamMembership."""
    class Meta:
        model = TeamMembership
        fields = '__all__'

class ProjectReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for Project, including nested organization."""
    organization = OrganizationReadSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'

class ProjectWriteSerializer(serializers.ModelSerializer):
    """Write serializer for Project."""
    class Meta:
        model = Project
        fields = '__all__'

class ProjectTeamSerializer(serializers.ModelSerializer):
    """Serializer for the ProjectTeam model."""
    class Meta:
        model = ProjectTeam
        fields = '__all__'

class OrganizationalTeamSerializer(serializers.ModelSerializer):
    """Serializer for the OrganizationalTeam model."""
    class Meta:
        model = OrganizationalTeam
        fields = '__all__'
