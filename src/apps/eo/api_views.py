from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_condition import Or
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, OAuth2Authentication
from rest_framework.authentication import SessionAuthentication
from rest_framework import filters
import django_filters.rest_framework

from apps.core.pagination import CustomPagination
from .models import (
    Person, TeamMember, Team, OrganizationalRole, 
    TeamMembership, Project, TeamPurpose,
    ProjectTeam, OrganizationalTeam
)
from .serializers import (
    PersonSerializer, 
    TeamMemberReadSerializer, TeamMemberWriteSerializer,
    TeamReadSerializer, TeamWriteSerializer,
    OrganizationalRoleSerializer,
    TeamMembershipReadSerializer, TeamMembershipWriteSerializer,
    ProjectReadSerializer, ProjectWriteSerializer,
    TeamPurposeSerializer,
    ProjectTeamSerializer, OrganizationalTeamSerializer
)

class EOBaseViewSet(ModelViewSet):
    """Base ViewSet for EO models with common configurations."""
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )
    ordering_fields = '__all__'
    ordering = ["id"]

class PersonViewSet(EOBaseViewSet):
    """ViewSet for the Person model."""
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filterset_fields = '__all__'
    search_fields = ['name', 'email']

class TeamMemberViewSet(EOBaseViewSet):
    """ViewSet for the TeamMember model."""
    queryset = TeamMember.objects.all()
    filterset_fields = '__all__'

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return TeamMemberReadSerializer
        return TeamMemberWriteSerializer

class TeamViewSet(EOBaseViewSet):
    """ViewSet for the Team model."""
    queryset = Team.objects.all()
    filterset_fields = '__all__'
    search_fields = ['name']

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return TeamReadSerializer
        return TeamWriteSerializer

class OrganizationalRoleViewSet(EOBaseViewSet):
    """ViewSet for the OrganizationalRole model."""
    queryset = OrganizationalRole.objects.all()
    serializer_class = OrganizationalRoleSerializer
    filterset_fields = '__all__'
    search_fields = ['name']

class TeamMembershipViewSet(EOBaseViewSet):
    """ViewSet for the TeamMembership model."""
    queryset = TeamMembership.objects.all()
    filterset_fields = ['team', 'member', 'role', 'start_date', 'end_date']

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return TeamMembershipReadSerializer
        return TeamMembershipWriteSerializer

class ProjectViewSet(EOBaseViewSet):
    """ViewSet for the Project model."""
    queryset = Project.objects.all()
    filterset_fields = '__all__'
    search_fields = ['name']

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ProjectReadSerializer
        return ProjectWriteSerializer

class TeamPurposeViewSet(EOBaseViewSet):
    """ViewSet for the TeamPurpose model."""
    queryset = TeamPurpose.objects.all()
    serializer_class = TeamPurposeSerializer
    filterset_fields = '__all__'

class ProjectTeamViewSet(EOBaseViewSet):
    """ViewSet for the ProjectTeam model."""
    queryset = ProjectTeam.objects.all()
    serializer_class = ProjectTeamSerializer
    filterset_fields = '__all__'

class OrganizationalTeamViewSet(EOBaseViewSet):
    """ViewSet for the OrganizationalTeam model."""
    queryset = OrganizationalTeam.objects.all()
    serializer_class = OrganizationalTeamSerializer
    filterset_fields = '__all__'
