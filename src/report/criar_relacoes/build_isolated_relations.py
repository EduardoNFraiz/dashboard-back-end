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

    # ==============================================================
    # RELAÇÕES ISOLATED
    # ==============================================================

    ("DELETE isolated",
    """
    MATCH (p:person)-[r:ISOLATED]->(p)
    DELETE r;
    """),

    # --- Commits isolados ---
    ("MERGE isolated_commits",
    """
    MATCH (p:person {organization:"leds-conectafapes"})<-[:created_by]-(c:commit)-[:committed_in]->(pr:pullrequest)
    WITH pr, collect(DISTINCT p) AS autores
    WHERE size(autores) = 1
    UNWIND autores AS isolado
    MERGE (isolado)-[r:ISOLATED {via:"commit"}]->(isolado)
      ON CREATE SET r.created_at = pr.created_at,
                    r.obj_id     = pr.id,
                    r.html_url   = pr.html_url,
                    r.title      = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.obj_id     = pr.id,
                    r.html_url   = pr.html_url,
                    r.title      = pr.title
    RETURN count(r) AS qtd;
    """),

    # --- PRs isolados ---
    ("MERGE isolated_prs",
    """
    MATCH (creator:person {organization:"leds-conectafapes"})<-[:created_by]-(pr:pullrequest)
    OPTIONAL MATCH (pr)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    OPTIONAL MATCH (pr)-[:reviewed_by]->(reviewer:person {organization:"leds-conectafapes"})
    WITH pr, collect(DISTINCT creator) + collect(DISTINCT assignee) + collect(DISTINCT reviewer) AS envolvidos
    WHERE size(envolvidos) = 1
    UNWIND envolvidos AS isolado
    MERGE (isolado)-[r:ISOLATED {via:"pr"}]->(isolado)
      ON CREATE SET r.created_at = pr.created_at,
                    r.obj_id     = pr.id,
                    r.html_url   = pr.html_url,
                    r.title      = pr.title,
                    r.ended_at   = pr.merged_at
      ON MATCH SET  r.created_at = pr.created_at,
                    r.ended_at   = pr.merged_at,
                    r.obj_id     = pr.id,
                    r.html_url   = pr.html_url,
                    r.title      = pr.title
    RETURN count(r) AS qtd;
    """),

    # --- Tasks isoladas ---
    ("MERGE isolated_tasks",
    """
    MATCH (t:developmenttask)<-[:created_by]-(creator:person {organization:"leds-conectafapes"})
    OPTIONAL MATCH (t)-[:assigned_to]->(assignee:person {organization:"leds-conectafapes"})
    WITH t, collect(DISTINCT creator) + collect(DISTINCT assignee) AS pessoas
    WHERE size(pessoas) = 1
    UNWIND pessoas AS isolado
    MERGE (isolado)-[r:ISOLATED {via:"task"}]->(isolado)
      ON CREATE SET r.created_at = t.created_at,
                    r.obj_id     = t.id,
                    r.title      = t.title,
                    r.ended_at   = t.ended_at
      ON MATCH SET  r.created_at = t.created_at,
                    r.ended_at   = t.ended_at,
                    r.obj_id     = t.id,
                    r.title      = t.title
    RETURN count(r) AS qtd;
    """),
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
        print("✅ Queries de ISOLATED executadas com sucesso!")

# === Main ===
if __name__ == "__main__":
    run_queries()
    driver.close()
