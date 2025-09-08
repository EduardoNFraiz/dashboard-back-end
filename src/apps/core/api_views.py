from .models import (
    Application, Configuration, Organization
)
from .serializers import (
    ApplicationReadSerializer, ApplicationWriteSerializer,
    ConfigurationReadSerializer, ConfigurationWriteSerializer,
    OrganizationReadSerializer,OrganizationWriteSerializer
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

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny 
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import logging

telemetry_logger = logging.getLogger('telemetry_events')

@api_view(['POST'])
@permission_classes([AllowAny])
def telemetry_event(request):
    """
    Endpoint para receber eventos de telemetria do frontend.
    """
    event_name = request.data.get('event_name')
    event_data = request.data.get('event_data', {})
    
    if not event_name:
        return Response({'error': 'Event name is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Adicione a telemetria ao logger
    telemetry_logger.info(f"Event: {event_name}", extra={'data': event_data})
    
    return Response({'status': 'Event received.'}, status=status.HTTP_200_OK)




User = get_user_model()

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')

        if not all([email, password, name]):
            return Response(
                {"error": "E-mail, senha e nome são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "Já existe um usuário com esse e-mail."},
                status=status.HTTP_409_CONFLICT
            )
            
        if User.objects.filter(username__iexact=name).exists():
            return Response(
                {"error": "Este nome já foi escolhido."},
                status=status.HTTP_409_CONFLICT
            )

        try:
            user = User.objects.create_user(
                username=name,
                email=email,
                password=password
            )
            

            return Response(
                {"message": "Usuário cadastrado com sucesso."},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


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
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ApplicationReadSerializer
        return ApplicationWriteSerializer


class ConfigurationViewSet(ModelViewSet):
    queryset = Configuration.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = '__all__'
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return ConfigurationReadSerializer
        return ConfigurationWriteSerializer
    
class OrganizationViewSet(ModelViewSet):
    queryset = Organization.objects.all()
    pagination_class = CustomPagination
    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    )
    filterset_fields = '__all__'
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ["id"]
    
    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return OrganizationReadSerializer
        return OrganizationWriteSerializer


class IssueView(ViewSet):

    authentication_classes = [OAuth2Authentication, SessionAuthentication]
    permission_classes = [Or(IsAdminUser, TokenHasReadWriteScope)]
   
    def list(self, request):
        try:
            skip = int(request.query_params.get("skip", 0))
            limit = int(request.query_params.get("limit", 50))
        except ValueError:
            return Response({"error": "Invalid pagination parameters."}, status=status.HTTP_400_BAD_REQUEST)

        repo = IssueRepository()
        try:
            data = repo.get_all_issue_repositories(skip=skip, limit=limit)
            return Response({
                "data": data,
                "pagination": {
                    "skip": skip,
                    "limit": limit
                }
            })
        finally:
            repo.close()
            
    def retrieve(self, request, pk=None):
        """
        Retorna uma única issue pelo ID (pk).
        """
        if pk is None:
            return Response({"error": "Issue id (pk) is required."}, status=status.HTTP_400_BAD_REQUEST)

        repo = IssueRepository()
        try:
            issue = repo.get_issue_by_id(pk)  # ajuste o nome se no seu repo for diferente
            if not issue:
                return Response({"error": "Issue not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"data": issue}, status=status.HTTP_200_OK)
        finally:
            repo.close()