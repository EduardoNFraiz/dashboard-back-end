from django.urls import path, register_converter, include
from rest_framework import routers
from .api_views import (
    ApplicationViewSet,
    ConfigurationViewSet,
    OrganizationViewSet,
    IssueView,
    RegisterAPIView,
    UserMeView,
    UserUpdateView,
)
'''OrganizationStatsView,
    RepositoryStatsView,
    RepositoriesGroupedStatsView,
    TeamStatsView,
    TeamDetailStatsView,        
    TeamWeeklyThroughputView,   
    TeamMonthlyThroughputView,  
    TeamReportsView,
    DeveloperSummaryStatsView,
    DeveloperDetailView,'''

router = routers.DefaultRouter()

router.register(r'application', ApplicationViewSet, basename='application')
router.register(r'configuration', ConfigurationViewSet, basename='configuration')
router.register(r'organization', OrganizationViewSet, basename='organization')

router.register(r'issue/repository/stats', IssueView, basename='stats')

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='register'),
    path('user/me', UserMeView.as_view(), name='user-me'),
    path('user/update', UserUpdateView.as_view(), name='user-update'),

    path('core/', include(router.urls))
]
'''
    path('organization/stats', OrganizationStatsView.as_view(), name='organization-stats'),
    path('repositories/stats', RepositoriesGroupedStatsView.as_view(), name='repositories-grouped-stats'),
    path('repositories/<str:repository_name>/stats', RepositoryStatsView.as_view(), name='repository-stats'),
    path('teams/stats', TeamStatsView.as_view(), name='team-stats'),
    path('teams/<str:team_name>/stats', TeamDetailStatsView.as_view(), name='team-detail-stats'),
    path('teams/<str:team_name>/throughput/weekly', TeamWeeklyThroughputView.as_view(), name='team-weekly-throughput'),
    path('teams/<str:team_name>/throughput/monthly', TeamMonthlyThroughputView.as_view(), name='team-monthly-throughput'),
    path('teams/<str:team_name>/reports', TeamReportsView.as_view(), name='team-reports'),
    path('developers/stats', DeveloperSummaryStatsView.as_view(), name='developer-summary-stats'),
    path('developers/<str:developer_name>/details', DeveloperDetailView.as_view(), name='developer-details'),'''