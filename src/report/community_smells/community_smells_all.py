from neo4j import GraphDatabase 
import pandas as pd
import networkx as nx
from networkx.algorithms import community
import sys
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


sys.stdout.reconfigure(encoding="utf-8")

# === Função para remover acentos ===
def remover_acentos(txt):
    if not isinstance(txt, str):
        return txt
    return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8")



# === Query global ===
query_network = """
// Colaboração
MATCH (p1:person)-[r:CO_COMMIT_IN|CO_ASSIGNED]-(p2:person)
WHERE r.created_at IS NOT NULL 
  AND p1.organization = "leds-conectafapes" 
  AND p2.organization = "leds-conectafapes" 
  AND coalesce(p1.role, "none") <> "consultant"
  AND coalesce(p2.role, "none") <> "consultant"  
RETURN p1.team_slug AS team1,
       p2.team_slug AS team2,
       p1.name AS source,
       p2.name AS target,
       type(r) AS relation,
       r.created_at AS created_at,
       p1.role AS role1,
       p2.role AS role2

UNION

// Coordenação
MATCH (c:person)-[r:COORDINATES]->(a:person)
WHERE r.created_at IS NOT NULL 
  AND c.organization = "leds-conectafapes" 
  AND a.organization = "leds-conectafapes" 
  AND coalesce(c.role, "none") <> "consultant"
  AND coalesce(a.role, "none") <> "consultant"  
RETURN c.team_slug AS team1,
       a.team_slug AS team2,
       c.name AS source,
       a.name AS target,
       "COORDINATES" AS relation,
       r.created_at AS created_at,
       c.role AS role1,
       a.role AS role2

UNION

// Isolados (auto-relação ISOLATED)
MATCH (c:person)-[r:ISOLATED]->(a:person)
WHERE r.created_at IS NOT NULL 
  AND c.organization = "leds-conectafapes" 
  AND a.organization = "leds-conectafapes" 
  AND coalesce(c.role, "none") <> "consultant"
  AND coalesce(a.role, "none") <> "consultant"  
RETURN c.team_slug AS team1,
       a.team_slug AS team2,
       c.name AS source,
       a.name AS target,
       "ISOLATED" AS relation,      // ✅ corrigido
       r.created_at AS created_at,
       c.role AS role1,
       a.role AS role2
 
"""

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(record) for record in result])

# === Buscar dados ===
df_edges = run_query(query_network)

# Converter datas
if "created_at" in df_edges.columns and df_edges["created_at"].notna().any():
    df_edges["created_at"] = pd.to_datetime(df_edges["created_at"], errors="coerce")
    data_inicio = df_edges["created_at"].min()
    data_fim = df_edges["created_at"].max()
else:
    data_inicio, data_fim = None, None

# Montar labels com (time)
df_edges["source"] = df_edges.apply(lambda x: f"{x['source']} ({x['team1']})" if x["team1"] else x["source"], axis=1)
df_edges["target"] = df_edges.apply(lambda x: f"{x['target']} ({x['team2']})" if x["target"] and x["team2"] else x["target"], axis=1)

print("Prévia das relações extraídas:")
print(df_edges.head())

# === Criar grafo global ===
G = nx.DiGraph()
roles_map = {}

for _, row in df_edges.iterrows():
    if row["relation"] == "ISOLATED":
        G.add_node(
            row["source"],
            relation="ISOLATED",
            role=row.get("role1"),
            via=row.get("via", "none")
        )

    elif row["relation"] in ["CO_COMMIT_IN", "CO_ASSIGNED"]:
        G.add_edge(row["source"], row["target"], relation=row["relation"])
        G.add_edge(row["target"], row["source"], relation=row["relation"])
    else:
        G.add_edge(row["source"], row["target"], relation=row["relation"])

    if row.get("role1"):
        roles_map[row["source"]] = row["role1"]
    if row.get("role2") and row["target"]:
        roles_map[row["target"]] = row["role2"]


analises = ["=== Análise Global de Community Smells ==="]

if data_inicio and data_fim:
    analises.append(f"Período dos dados: {data_inicio.date()} até {data_fim.date()}")

if G.number_of_nodes() > 0:
    undirected_G = G.to_undirected()

    # === Organizational Silos ===
    communities_mod = list(community.greedy_modularity_communities(undirected_G))
    analises.append(f"Organizational Silos: {len(communities_mod)} comunidades")
    for i, c in enumerate(communities_mod):
        analises.append(f"- Comunidade {i+1}: {', '.join(c)}")

    # === Truck Factor (articulation points globais) ===
    articulation = list(nx.articulation_points(undirected_G))
    if articulation:
        analises.append(f"Truck Factor (pessoas críticas): {', '.join(articulation)}")
    else:
        analises.append("Nenhuma pessoa crítica (Truck Factor) identificada")


    # === Bottleneck de líderes ===
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, normalized=True)

    # Cotas "justas"
    num_pessoas = G.number_of_nodes()
    cota_degree = sum(degree_centrality.values()) / num_pessoas
    cota_betw = sum(betweenness.values()) / num_pessoas

    bottlenecks = []
    for n in G.nodes():
        if roles_map.get(n) == "leader":
            grau = degree_centrality.get(n, 0)
            betw = betweenness.get(n, 0)
            if grau >= 2 * cota_degree or betw >= 2 * cota_betw:
                bottlenecks.append(f"{n} (deg={grau:.2f}, betw={betw:.2f})")

    analises.append(f"Bottleneck Líderes: {', '.join(bottlenecks) if bottlenecks else 'nenhum identificado'}")




    # === Lone Wolves ===
    isolados = [n for n, d in G.degree() if d == 0]
    if isolados:
        isolados_info = []
        for n in isolados:
            attrs = G.nodes[n]
            via = attrs.get("via", "none")
            role = attrs.get("role", "unknown")
            isolados_info.append(f"{n} [via={via}, role={role}]")
        analises.append(f"Lone Wolves: {', '.join(isolados_info)}")
    else:
        analises.append("Lone Wolves: nenhum identificado")


driver.close()

# === Exportar relatório ===
with open("./reports/analyse_community_smells_global.md", "w", encoding="utf-8") as f:
    f.write("# Relatório Global de Community Smells\n\n")
    for bloco in analises:
        f.write(f"- {remover_acentos(bloco)}\n")

print("\n✅ Análise global concluída e salva em analyse_community_smells_global.md")
