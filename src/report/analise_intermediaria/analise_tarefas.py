from neo4j import GraphDatabase
import pandas as pd
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

# ===== Config das tarefas =====
TASK_LABEL = "developmenttask"   # ajuste a capitalização do label se preciso

# Filtros opcionais (deixe como None para ignorar)
TASK_FILTERS = {
    "status":   None,            # ex.: "open", "done"
    "assignee": None,            # ex.: "felipe"
    "q":        None,            # busca em title/description
    "due_from": None,            # ex.: "2025-01-01"
    "due_to":   None             # ex.: "2025-12-31"
}

# Arquivo de saída
OUTPUT_CSV = "tasks_list.csv"

def build_task_query(label: str) -> str:
    return f"""
    MATCH (t:`{label}`)
    RETURN
        labels(t)      AS labels,
        t.title        AS title,
        t.created_at AS create_date,
        t.description  AS description
     ORDER BY
        coalesce(t.created_at, datetime('1970-01-01T00:00:00')) DESC
    """


def run(query: str, params: dict) -> pd.DataFrame:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        with driver.session() as session:
            res = session.run(query, parameters=params)
            return pd.DataFrame([dict(r) for r in res])
    finally:
        driver.close()

if __name__ == "__main__":
    params = {
        "status":   TASK_FILTERS.get("status"),
        "assignee": TASK_FILTERS.get("assignee"),
        "q":        TASK_FILTERS.get("q"),
        "due_from": TASK_FILTERS.get("due_from"),
        "due_to":   TASK_FILTERS.get("due_to"),
    }
    df = run(build_task_query(TASK_LABEL), params)

    # Conversões leves (se existirem)
    for col in ["created_at", "updated_at", "due_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"✅ CSV gerado: {OUTPUT_CSV} ({len(df)} linhas)")
