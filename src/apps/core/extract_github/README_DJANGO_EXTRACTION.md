# GitHub Data Extraction to Django Models

## Overview

This implementation provides a **Django ORM-based data sink** for extracting GitHub organizational data (teams, projects, and team members) and persisting it into PostgreSQL relational database models instead of Neo4j graph database.

## Architecture

### Components

1. **`sink_django.py`** - Django ORM sink that replaces `sink_neo4j.py`
   - Handles CRUD operations for Django models
   - Provides transactional data persistence
   - Maps graph-like relationships to relational foreign keys

2. **`extract_eo_django.py`** - Django-based EO extractor
   - Extends the refactored `ExtractBase` to support relational-only mode
   - Fetches data from GitHub via Airbyte
   - Transforms and saves data using `SinkDjango`
   - Manages incremental retrieval state via Django's `Configuration` model

3. **`extract_base.py`** - Refactored base class
   - Now supports dynamic sink initialization
   - Default Neo4j sink is optional and doesn't crash if missing
   - Provides hooks for custom configuration management

### Data Flow

```
GitHub API → Airbyte → PostgreSQL Cache → Pandas DataFrames → Django ORM → PostgreSQL Database
```

## Models Used

### From `apps.eo.models`:
- **Person** - Individual GitHub users
- **TeamMember** - Specialization of Person for team context
- **Team** - Base team entity
- **OrganizationalTeam** - Team belonging to an organization
- **Project** - GitHub projects
- **OrganizationalRole** - Roles within teams
- **TeamMembership** - Many-to-many relationship between teams and members

### From `apps.core.models`:
- **Organization** - GitHub organization

## Usage

### Method 1: Django Management Command

```bash
# Using command-line arguments
python manage.py extract_github_eo \
    --org "your-org-name" \
    --repo "your-org/your-repo" \
    --token "ghp_your_github_token"

# Using environment variables
export GITHUB_ORGANIZATION="your-org-name"
export GITHUB_REPOSITORY="your-org/your-repo"
export GITHUB_TOKEN="ghp_your_github_token"

python manage.py extract_github_eo --use-env
```

### Method 2: Python Script

```python
from apps.core.extract_github.extract_eo_django import ExtractEODjango

# Initialize extractor
extractor = ExtractEODjango(
    organization="your-org-name",
    secret="ghp_your_github_token",
    repository="your-org/your-repo"
)

# Run extraction
result = extractor.run()

# Check results
if result['status'] == 'success':
    print(f"Statistics: {result['statistics']}")
else:
    print(f"Error: {result['message']}")
```

### Method 3: API Endpoint (Future)

You can create a Django REST API endpoint to trigger extraction:

```python
# In apps/core/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.core.extract_github.extract_eo_django import ExtractEODjango

@api_view(['POST'])
def trigger_github_extraction(request):
    org = request.data.get('organization')
    repo = request.data.get('repository')
    token = request.data.get('token')
    
    extractor = ExtractEODjango(organization=org, secret=token, repository=repo)
    result = extractor.run()
    
    return Response(result)
```

## Configuration

### Environment Variables

Create a `.env` file or set these in your environment:

```bash
# GitHub Configuration
GITHUB_ORGANIZATION=your-org-name
GITHUB_REPOSITORY=your-org/your-repo
GITHUB_TOKEN=ghp_your_personal_access_token

# Database Configuration (for Airbyte cache)
DB_HOST_LOCAL=localhost
DB_PORT_LOCAL=5432
DB_USER_LOCAL=postgres
DB_PASSWORD_LOCAL=your_password
DB_NAME_LOCAL=your_database
```

## Key Features

### 1. Transactional Safety
All data is saved in a single database transaction. If any error occurs, the entire operation is rolled back.

```python
@transaction.atomic
def save_extraction_data(self, ...):
    # All operations are atomic
```

### 2. Idempotent Operations
Uses `get_or_create` patterns to avoid duplicates:

```python
person, created = Person.objects.get_or_create(
    email=email,
    defaults={'name': login}
)
```

### 3. Relationship Mapping

Graph relationships are mapped to relational foreign keys:

| Neo4j Relationship | Django Model Relationship |
|-------------------|---------------------------|
| Person → PRESENT_IN → Organization | Person (via TeamMember → Team → OrganizationalTeam → Organization) |
| TeamMember → DONE_FOR → Team | TeamMembership.team (ForeignKey) |
| TeamMember → ALLOCATES → Person | TeamMember.person (OneToOneField) |
| Organization → HAS → Team | OrganizationalTeam.organization (ForeignKey) |
| Organization → HAS → Project | Project.organization (ForeignKey) |

## Data Transformation

### Teams
```python
# GitHub API data
{
    "name": "Backend Team",
    "slug": "backend-team",
    "description": "Backend development team"
}

# Saved as OrganizationalTeam
OrganizationalTeam(
    name="Backend Team",
    organization=<Organization>,
    created_at=<timestamp>
)
```

### Projects
```python
# GitHub API data
{
    "title": "Q1 2024 Project",
    "short_description": "First quarter initiatives"
}

# Saved as Project
Project(
    name="Q1 2024 Project",
    description="First quarter initiatives",
    organization=<Organization>
)
```

### Team Members
```python
# GitHub API data
{
    "login": "john_doe",
    "email": "john@example.com",
    "team_slug": "backend-team"
}

# Saved as:
# 1. Person
Person(name="john_doe", email="john@example.com")

# 2. TeamMember
TeamMember(person=<Person>)

# 3. TeamMembership
TeamMembership(
    team=<Team>,
    member=<TeamMember>,
    role=<OrganizationalRole: "Member">,
    start_date=<today>
)
```

## Differences from Neo4j Version

| Aspect | Neo4j Version | Django Version |
|--------|--------------|----------------|
| **Storage** | Graph database | Relational database (PostgreSQL) |
| **Relationships** | Native graph edges | Foreign keys |
| **Queries** | Cypher queries | Django ORM / SQL |
| **Transactions** | Graph transactions | Django atomic transactions |
| **Schema** | Schema-less | Strict schema with migrations |
| **Scalability** | Graph traversal | JOIN operations |

## Next Steps

### Phase 1: Current Implementation ✅
- [x] Create `SinkDjango` class
- [x] Create `ExtractEODjango` class
- [x] Create management command
- [x] Document usage

### Phase 2: Real GitHub Data Integration 🔄
- [ ] Configure Airbyte GitHub connector
- [ ] Test with real GitHub organization
- [ ] Handle API rate limiting
- [ ] Add incremental updates support
- [ ] Store last extraction timestamp

### Phase 3: API Integration 📋
- [ ] Create REST API endpoint for triggering extraction
- [ ] Add authentication and permissions
- [ ] Create scheduled tasks (Celery)
- [ ] Add extraction status monitoring

### Phase 4: Frontend Integration 📋
- [ ] Display extracted teams in frontend
- [ ] Show team members and their roles
- [ ] Visualize projects and assignments
- [ ] Add filters and search

## Troubleshooting

### Issue: Django not configured
```python
django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS...
```
**Solution**: Ensure `DJANGO_SETTINGS_MODULE` is set in `sink_django.py`

### Issue: Duplicate entries
```python
django.db.utils.IntegrityError: duplicate key value violates unique constraint
```
**Solution**: The code uses `get_or_create` to handle duplicates. Check if unique constraints match the logic.

### Issue: Missing organization
```python
Organization matching query does not exist
```
**Solution**: Ensure the organization is created first or use `get_or_create_organization`

## Testing

```bash
# Run Django tests
python manage.py test apps.core.tests.test_extract_github

# Test with sample data
python manage.py extract_github_eo \
    --org "test-org" \
    --repo "test-org/test-repo" \
    --token "test_token"
```

## License

This implementation follows the same license as the main project.
