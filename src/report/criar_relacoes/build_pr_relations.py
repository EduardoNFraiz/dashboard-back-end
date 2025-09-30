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

# === Queries com labels e contagem ===
queries = [

    ("DELETE pr_assignee",
    """
    MATCH (c:person)-[r:COORDINATES {via:"pr_assignee"}]->(a:person)
    DELETE r;
    """),

    ("MERGE pr_assignee",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(pr:pullrequest)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    WHERE creator <> assignee
    MERGE (creator)-[r:COORDINATES {via:"pr_assignee"}]->(assignee)
      ON CREATE SET r.created_at = pr.created_at,
                    r.pr_id      = pr.id,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE pr_self",
    """
    MATCH (c:person)-[r:SELF_COORDINATES {via:"pr_self"}]->(a:person)
    DELETE r;
    """),

    ("MERGE pr_self",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(pr:pullrequest)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    WHERE creator = assignee
    MERGE (creator)-[r:SELF_COORDINATES {via:"pr_self"}]->(creator)
      ON CREATE SET r.created_at = pr.created_at,
                    r.pr_id      = pr.id,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE pr_no_assignee",
    """
    MATCH (c:person)-[r:SELF_COORDINATES {via:"pr_no_assignee"}]->(a:person)
    DELETE r;
    """),

    ("MERGE pr_no_assignee",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(pr:pullrequest)
    WHERE NOT (pr)-[:assigned_to]->(:person {organization:"leds-conectafapes"})
    MERGE (creator)-[r:SELF_COORDINATES {via:"pr_no_assignee"}]->(creator)
      ON CREATE SET r.created_at = pr.created_at,
                    r.pr_id      = pr.id,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE co_assigned",
    """
    MATCH (c:person)-[r:CO_ASSIGNED {via:"pr"}]->(a:person)
    DELETE r;
    """),

    ("MERGE co_assigned",
    """
    MATCH (pr:pullrequest)-[:assigned_to]->(a1:person {organization:"leds-conectafapes"}),
          (pr)-[:assigned_to]->(a2:person {organization:"leds-conectafapes"})
    WHERE a1 <> a2
    MERGE (a1)-[r:CO_ASSIGNED {via:"pr"}]->(a2)
      ON CREATE SET r.created_at = pr.created_at,
                    r.pr_id      = pr.id,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE pr_review",
    """
    MATCH (c:person)-[r:COORDINATES {via:"pr_review"}]->(a:person)
    DELETE r;
    """),

    ("MERGE pr_review",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(pr:pullrequest)-[:reviewed_by]->(reviewer:person {organization:"leds-conectafapes"})
    WHERE creator <> reviewer
    MERGE (creator)-[r:COORDINATES {via:"pr_review"}]->(reviewer)
      ON CREATE SET r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
    RETURN count(r) AS qtd;
    """),

    ("DELETE pr_commits",
    """
    MATCH (c:person)-[r:CO_COMMIT_IN {via:"pr_commits"}]->(a:person)
    DELETE r;
    """),

    ("MERGE pr_commits",
    """
    MATCH (p1:person {organization:"leds-conectafapes"})<-[:created_by]-(c1:commit)-[:committed_in]->(pr:pullrequest)<-[:committed_in]-(c2:commit)-[:created_by]->(p2:person {organization:"leds-conectafapes"})
    WHERE p1 <> p2
    MERGE (p1)-[r:CO_COMMIT_IN {via:"pr_commits"}]->(p2)
      ON CREATE SET r.created_at = pr.created_at,
                    r.pr_id      = pr.id,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.html_url   = pr.html_url, r.title = pr.title,
                    r.pr_id      = pr.id
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
        print("✅ Todas as queries de Pull Requests foram executadas com sucesso!")

# === Main ===
if __name__ == "__main__":
    run_queries()
    driver.close()
