from .models import (
    Application,
)
from .serializers import (
    ApplicationReadSerializer, ApplicationWriteSerializer,
)

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_condition import And, Or
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, OAuth2Authentication
from rest_framework.authentication import SessionAuthentication
from .pagination import CustomPagination
from rest_framework import generics
from rest_framework import filters
import django_filters.rest_framework

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .repository.IssueRepository import IssueRepository


class ApplicationViewSet(ModelViewSet):
    queryset = Application.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = '__all__'
    search_fields = ['github', 'repository']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ApplicationReadSerializer
        return ApplicationWriteSerializer

class IssueView(ViewSet):
    def list(self, request):
        try:
            skip = int(request.query_params.get("skip", 0))
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            return Response({"error": "Invalid pagination parameters."}, status=status.HTTP_400_BAD_REQUEST)

        repo = IssueRepository()
        try:
            data = repo.get_all(skip=skip, limit=limit)
            return Response({
                "data": data,
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            })
        finally:
            repo.close()