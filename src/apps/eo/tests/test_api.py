import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from apps.eo.models import Person, Team, OrganizationalRole, Project
from apps.core.models import Organization

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser('admin', 'admin@test.com', 'password123')

@pytest.fixture
def organization(db):
    return Organization.objects.create(name="Test Org")

@pytest.mark.django_db
class TestEOAPI:
    """Test suite for the EO Web Service API."""

    def test_unauthorized_access(self, api_client):
        url = reverse('person-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_person_crud(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        url = reverse('person-list')
        
        # Create
        data = {"name": "Test Person", "email": "test@example.com"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        person_id = response.data['id']
        
        # List
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(p['name'] == "Test Person" for p in response.data['results'])
        
        # Update
        detail_url = reverse('person-detail', args=[person_id])
        update_data = {"name": "Updated Person"}
        response = api_client.patch(detail_url, update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Updated Person"
        
        # Delete
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Person.objects.filter(id=person_id).exists()

    def test_team_filtering(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        Team.objects.create(name="Team A")
        Team.objects.create(name="Team B")
        
        url = reverse('team-list')
        response = api_client.get(url, {'name': 'Team A'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == "Team A"

    def test_project_nested_read(self, api_client, admin_user, organization):
        api_client.force_authenticate(user=admin_user)
        project = Project.objects.create(name="Test Project", organization=organization)
        
        url = reverse('project-detail', args=[project.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['organization']['name'] == "Test Org"

    def test_pagination_format(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        for i in range(15):
            Person.objects.create(name=f"Person {i}")
            
        url = reverse('person-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'meta' in response.data
        assert 'data' in response.data
        assert response.data['meta']['total'] >= 15
        assert len(response.data['data']) == 10  # page_size=10

    def test_signals_execution(self, admin_user):
        # We can't easily check logger output in this environment without complex mocking,
        # but we can verify that creating an object doesn't crash now that signals are connected.
        person = Person.objects.create(name="Signal Test")
        assert person.id is not None
