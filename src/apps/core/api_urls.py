from django.urls import path, register_converter, include
from rest_framework import routers
from .api_views import (
    ApplicationViewSet,
    ConfigurationViewSet,
    OrganizationViewSet,
    IssueView,
    RegisterAPIView,
)
router = routers.DefaultRouter()

router.register(r'application', ApplicationViewSet, basename='application')
router.register(r'configuration', ConfigurationViewSet, basename='configuration')
router.register(r'organization', OrganizationViewSet, basename='organization')

router.register(r'issue/repository/stats', IssueView, basename='stats')

urlpatterns = [
    path('auth/register/', RegisterAPIView.as_view(), name='register'),
    path('core/', include(router.urls))
]
