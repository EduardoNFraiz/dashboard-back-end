import os
import django
import datetime

# 1. Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from apps.core.extract_github.sink_django import SinkDjango
from apps.eo.models import Person, Team, OrganizationalTeam, Project

def run_test():
    print("🚀 Iniciando Teste de Integração EO...")
    sink = SinkDjango()

    # Dados de teste simulando a API do GitHub
    org_name = "TheBand-Labs"
    
    teams_data = [
        {"name": "Backend Team", "slug": "backend-team", "description": "Responsible for APIs and DB"},
        {"name": "Frontend Team", "slug": "frontend-team", "description": "Responsible for Vue.js Dashboard"}
    ]
    
    projects_data = [
        {"title": "Migration Phase 1", "description": "Migrating Neo4j to Postgres"}
    ]
    
    members_data = [
        {"login": "dev_senior", "email": "senior@theband.com", "team_slug": "backend-team"},
        {"login": "front_master", "email": "master@theband.com", "team_slug": "frontend-team"}
    ]

    print("💾 Salvando dados no Postgres através do SinkDjango...")
    
    try:
        stats = sink.save_extraction_data(
            organization_name=org_name,
            teams_data=teams_data,
            projects_data=projects_data,
            team_members_data=members_data
        )
        
        print("\n✅ Sucesso! Estatísticas do salvamento:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
            
        print("\n🔍 Validando no banco de dados...")
        print(f"  - Total de Pessoas: {Person.objects.count()}")
        print(f"  - Total de Times: {OrganizationalTeam.objects.count()}")
        print(f"  - Total de Projetos: {Project.objects.count()}")
        
        print("\n🌐 A API agora deve retornar esses dados em: http://localhost:8000/api/eo/team/")
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    run_test()
