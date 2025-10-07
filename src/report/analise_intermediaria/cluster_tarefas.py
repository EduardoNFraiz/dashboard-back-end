from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import re
import unicodedata

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


# ===== Config das tarefas =====
TASK_LABEL = "developmenttask"

# ===== Arquivos de saída =====
CSV_DETALHES = "tasks_grouped_by_tema.csv"
CSV_SUMARIO  = "tasks_tema_summary.csv"

def build_task_query(label: str) -> str:
    return f"""
    MATCH (t:`{label}`)
    RETURN
        labels(t)        AS labels,
        t.title          AS title,
        t.created_at     AS create_date,
        t.description    AS description
    ORDER BY
        coalesce(t.created_at, datetime('1970-01-01T00:00:00')) DESC,
        toLower(t.title) ASC
    """

def run(query: str) -> pd.DataFrame:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        with driver.session() as session:
            res = session.run(query)
            return pd.DataFrame([dict(r) for r in res])
    finally:
        driver.close()

def strip_accents_lower(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    return s.lower()

if __name__ == "__main__":
    df = run(build_task_query(TASK_LABEL))

    # --- Extrair blocos de prefixos do início do título ---
    df["prefix_block"] = df["title"].str.extract(r"^(\s*(?:\[[^\]]+\]\s*)+)", expand=False)

    def extract_prefix_list(block):
        if isinstance(block, str):
            return re.findall(r"\[([^\]]+)\]", block)
        return []

    df["prefix_list"] = df["prefix_block"].apply(extract_prefix_list)
    df["prefix_tag"]  = df["prefix_list"].apply(lambda lst: lst[0] if lst else None)

    def strip_prefix(title, block):
        if isinstance(block, str):
            return title[len(block):].strip()
        return title

    df["title_wo_prefix"] = df.apply(lambda r: strip_prefix(r["title"], r["prefix_block"]), axis=1)

    # Normaliza datas
    if "create_date" in df.columns:
        df["create_date"] = pd.to_datetime(df["create_date"], errors="coerce")

    # === Tema (primeiro prefixo normalizado) ===
    df["tema"] = df["prefix_tag"].apply(lambda x: (x or "NO_PREFIX").strip().upper())

    # === REUNIAO: quando houver "reunião/reuniao" no título (acento-insensitive) ===
    df["title_norm"] = df["title"].fillna("").apply(strip_accents_lower)
    mask_reuniao = df["title_norm"].str.contains(r"\breuniao\b", regex=True)
    df.loc[mask_reuniao, "tema"] = "REUNIAO"

    # === Unificar BUG, HOTFIX e FIX em BUG ===
    # === Unificações de tema ===
    EQUIV = {
        # bugfix
        "FIX": "BUG",
        "HOTFIX": "BUG",
        "HOT-FIX": "BUG",
        "FIX+FEAT": "BUG",
        "FEAT+FIX": "BUG",

        # feature
        "FEAT": "FEATURE",

        # combos / otimização -> refatoração
        "FEAT+REFACTOR": "REFRACTOR",
        "OTIMIZACAO": "REFRACTOR",
        "OTIMIZAÇÃO": "REFRACTOR",
        "OTIMIZATION": "REFRACTOR",
        "OTIMIZATION": "REFRACTOR",
        "Teste" : "TESTE",
        "Testes" : "TEST",
        "Test" : "TEST",
        "QA" : "TEST",

        # pedido do usuário
        "REFACT": "REFRACTOR",     # <- novo
        # (opcional) padronizar também REFACTOR:
        "REFACTOR": "REFRACTOR",
    }
    df["tema"] = df["tema"].replace(EQUIV)


    # ---- CSV detalhado agrupado (ordenado por tema e data desc) ----
    cols = ["tema", "labels", "prefix_tag", "prefix_list", "title", "title_wo_prefix", "create_date", "description"]
    cols = [c for c in cols if c in df.columns]
    df_sorted = df.sort_values(["tema", "create_date"], ascending=[True, False]).copy()

    # Formata data para string no CSV
    if "create_date" in df_sorted.columns:
        df_sorted["create_date"] = df_sorted["create_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    df_sorted[cols].to_csv(CSV_DETALHES, index=False, encoding="utf-8")

    # ---- Sumário por tema (maiores primeiro) ----
    sumario = (df
        .groupby("tema", dropna=False)
        .agg(qtd=("title", "size"),
             ultima_data=("create_date", "max"))
        .reset_index()
        .sort_values(["qtd", "ultima_data"], ascending=[False, False])
    )

    sumario["ultima_data"] = pd.to_datetime(sumario["ultima_data"], errors="coerce") \
                               .dt.strftime("%Y-%m-%d %H:%M:%S")

    sumario.to_csv(CSV_SUMARIO, index=False, encoding="utf-8")

    print(f"✅ CSV detalhado gerado: {CSV_DETALHES} ({len(df_sorted)} linhas)")
    print(f"✅ CSV sumário por tema: {CSV_SUMARIO} ({len(sumario)} temas)")
