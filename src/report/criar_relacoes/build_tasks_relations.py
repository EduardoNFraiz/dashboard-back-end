from neo4j import GraphDatabase

from dotenv import load_dotenv
import os
from pathlib import Path

# ===== Carregar variáveis do .env =====
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

# Carregar o .env explicitamente
load_dotenv(dotenv_path=ENV_PATH)

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# === Queries ===
queries = [
    # 0. Limpeza
    ("DELETE task_assignee",
    """
    MATCH (c:person)-[r:COORDINATES {via:"task_assignee"}]->(a:person)
    DELETE r;
    """),

    # 1. Criador coordena assignees
    ("MERGE task_assignee",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(t:developmenttask)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    WHERE creator <> assignee
    MERGE (creator)-[r:COORDINATES {via:"task_assignee"}]->(assignee)
      ON CREATE SET r.created_at = t.created_at,
                    r.task_id    = t.id,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url, 
                    r.title      = t.title
      ON MATCH SET  r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url,
                    r.title      = t.title,
                    r.task_id    = t.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE task_self",
    """
    MATCH (c:person)-[r:SELF_COORDINATES {via:"task_self"}]->(a:person)
    DELETE r;
    """),

    # 2. Autocoordenação
    ("MERGE task_self",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(t:developmenttask)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    WHERE creator = assignee
    MERGE (creator)-[r:SELF_COORDINATES {via:"task_self"}]->(creator)
      ON CREATE SET r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,   
                    r.html_url   = t.html_url, 
                    r.title      = t.title,
                    r.task_id    = t.id
      ON MATCH SET  r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url,
                    r.title      = t.title,
                    r.task_id    = t.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE task_no_assignee",
    """
    MATCH (c:person)-[r:SELF_COORDINATES {via:"task_no_assignee"}]->(a:person)
    DELETE r;
    """),

    # 3. Criador sem assignee
    ("MERGE task_no_assignee",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(t:developmenttask)
    WHERE NOT (t)-[:assigned_to]->(:person {organization:"leds-conectafapes"})
    MERGE (creator)-[r:SELF_COORDINATES {via:"task_no_assignee"}]->(creator)
      ON CREATE SET r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url, 
                    r.title      = t.title,
                    r.task_id    = t.id
      ON MATCH SET  r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,   
                    r.html_url   = t.html_url, 
                    r.title      = t.title,
                    r.task_id    = t.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE co_assigned",
    """
    MATCH (c:person)-[r:CO_ASSIGNED {via:"task"}]->(a:person)
    DELETE r;
    """),

    # 4. Co-assignees
    ("MERGE co_assigned",
    """
    MATCH (t:developmenttask)-[:assigned_to]->(a1:person {organization:"leds-conectafapes"}),
          (t)-[:assigned_to]->(a2:person {organization:"leds-conectafapes"})
    WHERE a1 <> a2
    MERGE (a1)-[r:CO_ASSIGNED {via:"task"}]->(a2)
      ON CREATE SET r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url,
                    r.title      = t.title,
                    r.task_id    = t.id
      ON MATCH SET  r.created_at = t.created_at,
                    r.ended_at   = t.closed_at,  
                    r.html_url   = t.html_url, 
                    r.title      = t.title,
                    r.task_id    = t.id
    RETURN count(r) AS qtd;
    """)
]

# === Função para executar queries ===
def run_queries():
    with driver.session() as session:
        for i, (label, query) in enumerate(queries, start=1):
            print(f"Executando query {i} ({label})...")
            result = session.run(query)
            try:
                qtd = result.single().get("qtd")
                print(f" → Relações criadas/atualizadas: {qtd}")
            except Exception:
                print(" → Query sem retorno de contagem.")
        print("✅ Todas as queries de tarefas foram executadas com sucesso!")

# === Main ===
if __name__ == "__main__":
    run_queries()
    driver.close()
