from neo4j import GraphDatabase 
import pandas as pd
import networkx as nx
from networkx.algorithms import community
import sys
import unicodedata

from dotenv import load_dotenv
import os

# ===== Carregar variáveis do .env =====
load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

sys.stdout.reconfigure(encoding="utf-8")

# === Função para remover acentos e caracteres especiais ===
def remover_acentos(txt):
    if not isinstance(txt, str):
        return txt
    return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8")

# === Parâmetro de granularidade temporal ===
TIME_UNIT = "all"

# === Query com coordenação + colaboração + isolados ===
if TIME_UNIT == "all":
    query_network = """
    // Colaboração (não-direcionada)
    MATCH (p1:person)-[r:CO_COMMIT_IN|CO_ASSIGNED]-(p2:person)
    WHERE r.created_at IS NOT NULL 
      AND coalesce(p1.role, "none") <> "consultant"
      AND coalesce(p2.role, "none") <> "consultant"  
    WITH "ALL" AS periodo,
         p1.team_slug AS team1,
         p2.team_slug AS team2,
         p1.name AS source,
         p2.name AS target,
         type(r) AS relation,
         r.created_at AS created_at,
         p1.role AS role1,
         p2.role AS role2
    RETURN periodo, team1, team2, source, target, relation, created_at, role1, role2

    UNION

    // Coordenação (direcionada)
    MATCH (c:person)-[r:COORDINATES]->(a:person)
    WHERE r.created_at IS NOT NULL 
      AND coalesce(c.role, "none") <> "consultant"
      AND coalesce(a.role, "none") <> "consultant"  
    WITH "ALL" AS periodo,
         c.team_slug AS team1,
         a.team_slug AS team2,
         c.name AS source,
         a.name AS target,
         r.via AS relation,
         r.created_at AS created_at,
         c.role AS role1,
         a.role AS role2
    RETURN periodo, team1, team2, source, target, relation, created_at, role1, role2

    UNION

    // Isolados
    MATCH (p:person)
    WHERE NOT (p)-[:CO_COMMIT_IN|CO_ASSIGNED|COORDINATES]-(:person) 
      AND p.organization = "leds-conectafapes" 
      AND coalesce(p.role, "none") <> "consultant"
    WITH "ALL" AS periodo,
         p.team_slug AS team1,
         p.name AS source,
         p.role AS role1
    RETURN periodo, team1, NULL AS team2, source, NULL AS target, 
           "ISOLATED" AS relation, NULL AS created_at, role1, NULL AS role2;
    """
else:
    query_network = f"..."

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return pd.DataFrame([dict(record) for record in result])

# === Buscar rede ===
df_edges = run_query(query_network)

# === Buscar todos os membros por time ===
query_times = """
MATCH (p:person)
WHERE p.organization = "leds-conectafapes" 
  AND coalesce(p.role, "none") <> "consultant"
RETURN DISTINCT p.team_slug AS time, p.name AS pessoa, p.role AS role
ORDER BY time, pessoa
"""
df_times = run_query(query_times)
times_dict = df_times.groupby("time")[["pessoa","role"]].apply(lambda x: list(map(tuple, x.values))).to_dict()

# Converter datas
if "created_at" in df_edges.columns:
    df_edges["created_at"] = pd.to_datetime(df_edges["created_at"], errors="coerce")
    data_min = df_edges["created_at"].min()
    data_max = df_edges["created_at"].max()
else:
    data_min, data_max = None, None

# Montar labels já com (time)
df_edges["source"] = df_edges.apply(lambda x: f"{x['source']} ({x['team1']})" if x["team1"] else x["source"], axis=1)
df_edges["target"] = df_edges.apply(lambda x: f"{x['target']} ({x['team2']})" if x["target"] and x["team2"] else x["target"], axis=1)

print("Prévia das relações extraídas:")
print(df_edges.head())

# === Loop por período + team1 ===
analises = []
for (periodo, team), grupo in df_edges.groupby(["periodo", "team1"]):
    G = nx.DiGraph()
    roles_map = {}

    # Construir grafo do agrupamento atual
    for _, row in grupo.iterrows():
        if row["relation"] == "ISOLATED":
            G.add_node(row["source"], relation="ISOLATED")
        elif row["relation"] in ["CO_COMMIT_IN", "CO_ASSIGNED"]:
            G.add_edge(row["source"], row["target"], relation=row["relation"])
            G.add_edge(row["target"], row["source"], relation=row["relation"])
        else:
            G.add_edge(row["source"], row["target"], relation=row["relation"])

        if row.get("role1"):
            roles_map[row["source"]] = row["role1"]
        if row.get("role2") and row["target"]:
            roles_map[row["target"]] = row["role2"]

    if G.number_of_nodes() == 0:
        continue

    undirected_G = G.to_undirected()
    communities = list(community.greedy_modularity_communities(undirected_G))

    sintese = [f"=== Periodo: {periodo} ({TIME_UNIT}) | Time: {team} ==="]

    # 🔹 Lista de membros do time
    membros_do_time = times_dict.get(team, [])
    if membros_do_time:
        membros_fmt = [f"{p} ({r})" for p, r in sorted(membros_do_time)]
        sintese.append(f"Membros do time {team}: {', '.join(membros_fmt)}")
    else:
        sintese.append(f"Membros do time {team}: nenhum encontrado")

    # 🔹 Conjunto de nós que pertencem ao time (pelo rótulo "Nome (time)")
    membros_time = [n for n in G.nodes() if f"({team})" in n]

    # === Articulation Points (dentro do time) ===
    articulation = []
    if membros_time:
        subG_time = G.subgraph(membros_time).copy()
        undirected_sub = subG_time.to_undirected()
        articulation = list(nx.articulation_points(undirected_sub))

        if articulation:
            sintese.append(
                f"Pessoas críticas (Truck Factor) dentro do time: {', '.join(sorted(articulation))}"
            )
        else:
            sintese.append("Nenhuma pessoa crítica (Truck Factor) encontrada dentro do time.")
    else:
        sintese.append("Nenhum membro do time encontrado no grafo atual.")



    # === Boundary Spanners (globais) ===
    articulation = list(nx.articulation_points(undirected_G))
    boundary_spanners = []
    for n in articulation:
        vizinhos = set(G.neighbors(n)) | set(G.predecessors(n))
        times_vizinhos = {v.split("(")[-1].replace(")", "") for v in vizinhos if "(" in v}
        if len(times_vizinhos) > 2:  # conecta pelo menos 2 times
            boundary_spanners.append(n)

    if boundary_spanners:
        sintese.append(f"Boundary Spanners: {', '.join(boundary_spanners)}")
    else:
        sintese.append("Boundary Spanners: nenhum identificado")

    # === Lone Wolf (nós sem arestas no grafo do agrupamento) ===
    isolados = [n for n, d in G.degree() if d == 0]
    sintese.append(f"Lone Wolf: {', '.join(sorted(isolados)) if isolados else 'nenhum identificado'}")

    # === Organizational Silos (somente dentro do time) ===
    if membros_time:
        subG_time = G.subgraph(membros_time).copy()
        undirected_sub = subG_time.to_undirected()
        communities_sub = list(community.greedy_modularity_communities(undirected_sub))
        sintese.append(f"Organizational Silos no time: {len(communities_sub)} comunidades")
        for i, c in enumerate(communities_sub, 1):
            sintese.append(f"- Comunidade {i}: {', '.join(sorted(c))}")
    else:
        sintese.append("Organizational Silos: nenhum membro encontrado no time")

    analises.append("\n".join(sintese))

driver.close()

# === Exportar para Markdown ===
with open("./reports/analyse_community_smells_by_team.md", "w", encoding="utf-8") as f:
    f.write("# Relatório de Análise de Community Smells por Time\n\n")

    if data_min is not None and data_max is not None:
        f.write(f"**Período analisado:** {data_min.date()} → {data_max.date()}\n\n")

    for bloco in analises:
        linhas = bloco.splitlines()
        if linhas and linhas[0].startswith("==="):
            header = linhas[0].replace("===", "").replace("==", "").strip()
            f.write(f"## {header}\n\n")
            for l in linhas[1:]:
                f.write(f"- {remover_acentos(l)}\n")
            f.write("\n---\n\n")

print("\n✅ Análise concluída e salva em analyse_community_smells_by_team.md")
