from neo4j import GraphDatabase
import pandas as pd
import os

# === Conexão com Neo4j ===
uri = "bolt://localhost:7687"
user = "neo4j"
password = "G7q!rX#9Lp@eZ1vK"
driver = GraphDatabase.driver(uri, auth=(user, password))

OUT_DIR = "."
os.makedirs(OUT_DIR, exist_ok=True)

# === Query de exportação ===
EXPORT_QUERY = r"""
MATCH (src:person)-[r]->(dst:person)
WHERE type(r) IN [
  'COORDINATES','SELF_COORDINATES','CO_ASSIGNED','CO_COMMIT_IN'
]
RETURN
    elementId(src) AS src_element_id,
    coalesce(src.id, src.login, src.username) AS src_id,
    coalesce(src.name, src.login, src.username) AS src_name,
    src.organization AS src_org,
    elementId(dst) AS dst_element_id,
    coalesce(dst.id, dst.login, dst.username) AS dst_id,
    coalesce(dst.name, dst.login, dst.username) AS dst_name,
    dst.organization AS dst_org,
    type(r) AS rel_type,
    r.via AS via,
    r.created_at AS created_at,
    r.ended_at AS ended_at,
    r.pr_id AS pr_id,
    r.title AS title,
    r.html_url AS html_url
ORDER BY rel_type, via, src_name, dst_name
"""

def export_relations():
    with driver.session() as session:
        print("Consultando relações detalhadas...")
        result = session.run(EXPORT_QUERY)
        rows = [record.data() for record in result]

    if not rows:
        print("⚠ Nenhuma relação encontrada para exportar.")
        return

    df = pd.DataFrame(rows)
    out_csv = os.path.join(OUT_DIR, "relations_export.csv")
    df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"✔ Relações exportadas: {out_csv} ({len(df)} linhas)")

if __name__ == "__main__":
    export_relations()
    driver.close()
