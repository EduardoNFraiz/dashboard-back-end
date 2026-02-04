from django.urls import path, include
from rest_framework import routers
from .api_views import (
    PersonViewSet, TeamMemberViewSet, TeamViewSet,
    OrganizationalRoleViewSet, TeamMembershipViewSet,
    ProjectViewSet, TeamPurposeViewSet,
    ProjectTeamViewSet, OrganizationalTeamViewSet
)

router = routers.DefaultRouter()

router.register(r'person', PersonViewSet, basename='person')
router.register(r'team-member', TeamMemberViewSet, basename='team-member')
router.register(r'team', TeamViewSet, basename='team')
router.register(r'role', OrganizationalRoleViewSet, basename='role')
router.register(r'membership', TeamMembershipViewSet, basename='membership')
router.register(r'project', ProjectViewSet, basename='project')
router.register(r'purpose', TeamPurposeViewSet, basename='purpose')
router.register(r'project-team', ProjectTeamViewSet, basename='project-team')
router.register(r'organizational-team', OrganizationalTeamViewSet, basename='organizational-team')

urlpatterns = [
    path('eo/', include(router.urls))
]
