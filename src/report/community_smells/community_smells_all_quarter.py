from neo4j import GraphDatabase 
import pandas as pd
import networkx as nx
from networkx.algorithms import community
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
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
       "ISOLATED" AS relation,      
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
df_edges["created_at"] = pd.to_datetime(df_edges["created_at"], errors="coerce")
data_inicio = df_edges["created_at"].min()
data_fim = df_edges["created_at"].max()

if pd.isna(data_inicio) or pd.isna(data_fim):
    raise ValueError("Não há dados de created_at válidos para definir os períodos")

# Separar isolados globais (created_at = NULL)
df_isolados = df_edges[df_edges["relation"] == "ISOLATED"].copy()


if not df_isolados.empty:
    df_isolados.to_csv("isolados.csv", index=False, encoding="utf-8")
    print(f"✅ {len(df_isolados)} isolados exportados para 'isolados.csv'")
else:
    print("⚠️ Nenhum isolado encontrado para exportar")



# Montar labels com (time)
df_edges["source"] = df_edges.apply(lambda x: f"{x['source']} ({x['team1']})" if x["team1"] else x["source"], axis=1)
df_edges["target"] = df_edges.apply(lambda x: f"{x['target']} ({x['team2']})" if x["target"] and x["team2"] else x["target"], axis=1)
df_isolados["source"] = df_isolados.apply(lambda x: f"{x['source']} ({x['team1']})" if x["team1"] else x["source"], axis=1)

print("Prévia das relações extraídas:")
print(df_edges.head())

# === Definir períodos trimestrais ===
periodos = []
inicio = data_inicio
while inicio < data_fim:
    fim = inicio + relativedelta(months=3)
    periodos.append((inicio, min(fim, data_fim)))
    inicio = fim
    
    
print("\n📅 Períodos trimestrais detectados:")
for i, (ini, fim) in enumerate(periodos, start=1):
    print(f"Trimestre {i}: {ini.date()} → {fim.date()}")


analises = []
stats = []  # para gráfico

# === Rodar análise por trimestre ===
for (inicio, fim) in periodos:
    df_periodo = df_edges[
        (df_edges["created_at"].notna()) &
        (df_edges["created_at"] >= inicio) &
        (df_edges["created_at"] < fim)
    ]

    sintese = [f"=== {inicio.date()} → {fim.date()} ==="]

    if df_periodo.empty and df_isolados.empty:
        sintese.append("Nenhum dado disponível")
        analises.append("\n".join(sintese))
        stats.append({"periodo": fim.date(), "silos": 0, "truck": 0, "boundary": 0, "bottlenecks": 0, "lone": 0})
        continue

    G = nx.DiGraph()
    roles_map = {}

    # 1) Adicionar arestas do período
    for _, row in df_periodo.iterrows():
        if row["relation"] in ["CO_COMMIT_IN", "CO_ASSIGNED"]:
            G.add_edge(row["source"], row["target"], relation=row["relation"])
            G.add_edge(row["target"], row["source"], relation=row["relation"])
        elif row["relation"] == "COORDINATES":
            G.add_edge(row["source"], row["target"], relation="COORDINATES")

        if row.get("role1"):
            roles_map[row["source"]] = row["role1"]
        if row.get("role2") and row["target"]:
            roles_map[row["target"]] = row["role2"]

    # 2) Garantir inclusão de isolados globais
    for m in df_isolados["source"].unique():
        if m not in G.nodes():
            G.add_node(m, relation="ISOLATED")

    undirected_G = G.to_undirected()

    # === Organizational Silos (inclui todos os nós, até isolados) ===
    communities_mod = list(community.greedy_modularity_communities(undirected_G))
    sintese.append(f"Organizational Silos: {len(communities_mod)} comunidades")
    for i, c in enumerate(communities_mod, 1):
        sintese.append(f"- Comunidade {i}: {', '.join(sorted(c))}")

    # === Truck Factor ===
    articulation = list(nx.articulation_points(undirected_G))
    sintese.append(f"Truck Factor: {', '.join(articulation) if articulation else 'nenhum'}")

    # === Boundary Spanners ===
    boundary_spanners = []
    for n in articulation:
        vizinhos = set(G.neighbors(n)) | set(G.predecessors(n))
        times_vizinhos = {v.split("(")[-1].replace(")", "") for v in vizinhos if "(" in v}
        if len(times_vizinhos) >= 2:  # conecta mais de dois time
            boundary_spanners.append(n)
    sintese.append(f"Boundary Spanners: {', '.join(boundary_spanners) if boundary_spanners else 'nenhum'}")

    # === Bottleneck líderes ===
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, normalized=True)

    num_pessoas = G.number_of_nodes()
    cota_degree = sum(degree_centrality.values()) / num_pessoas if num_pessoas else 0
    cota_betw = sum(betweenness.values()) / num_pessoas if num_pessoas else 0

    bottlenecks = []
    for n in G.nodes():
        if roles_map.get(n) == "leader":
            grau = degree_centrality.get(n, 0)
            betw = betweenness.get(n, 0)
            if grau >= 2 * cota_degree or betw >= 2 * cota_betw:
                bottlenecks.append(n)

    sintese.append(f"Bottleneck Líderes: {', '.join(bottlenecks) if bottlenecks else 'nenhum'}")

    # === Lone Wolves ===
    isolados = [n for n, d in G.degree() if d == 0]
    sintese.append(f"Lone Wolves: {', '.join(isolados) if isolados else 'nenhum'}")

    analises.append("\n".join(sintese))

    stats.append({
        "periodo": fim.date(),
        "silos": len(communities_mod),
        "truck": len(articulation),
        "boundary": len(boundary_spanners),
        "bottlenecks": len(bottlenecks),
        "lone": len(isolados)
    })

driver.close()



# === Gráfico ===
df_stats = pd.DataFrame(stats).set_index("periodo")

plt.figure(figsize=(10,6))
plt.plot(df_stats.index, df_stats["silos"], marker="o", label="Organizational Silos")
plt.plot(df_stats.index, df_stats["truck"], marker="s", label="Truck Factor")
plt.plot(df_stats.index, df_stats["boundary"], marker="d", label="Boundary Spanners")
plt.plot(df_stats.index, df_stats["bottlenecks"], marker="^", label="Bottleneck Leaders")
plt.plot(df_stats.index, df_stats["lone"], marker="x", label="Lone Wolves")
plt.title("Evolução dos Community Smells por Trimestre")
plt.xlabel("Período")
plt.ylabel("Quantidade")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("./reports/community_smells_evolucao.png", dpi=300)


# === Exportar relatório ===
with open("./reports/analyse_community_smells_by_quarter.md", "w", encoding="utf-8") as f:
    f.write("# Relatório Trimestral de Community Smells\n\n")
    for bloco in analises:
        f.write(bloco + "\n\n---\n\n")
   
    f.write("# Relatório Trimestral de Community Smells")
    f.write("![Evolução dos Community Smells](community_smells_evolucao.png)") 
        

print("\n✅ Relatório trimestral concluído e salvo em analyse_community_smells_by_quarter.md")
print("📊 Gráfico salvo como community_smells_evolucao.png")
