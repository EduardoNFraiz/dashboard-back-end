import matplotlib.pyplot as plt
import networkx as nx
import re

# === Ler o arquivo de relatório ===
with open("analyse_community_smells_global.md", "r", encoding="utf-8") as f:
    texto = f.read()

# === Extrair comunidades ===
comunidades = {}
for linha in texto.splitlines():
    m = re.match(r"- - Comunidade (\d+): (.+)", linha)
    if m:
        idx = int(m.group(1))
        membros = [m.strip() for m in m.group(2).split(",")]
        comunidades[idx] = membros

# === Extrair Truck Factor ===
m_truck = re.search(r"Truck Factor .*: (.+)", texto)
truck_factor = [m.strip() for m in m_truck.group(1).split(",")] if m_truck else []

# === Extrair Bottleneck Leaders ===
m_bottleneck = re.search(r"Bottleneck Lideres: (.+)", texto)
bottlenecks = []
if m_bottleneck:
    partes = m_bottleneck.group(1).split(",")
    for p in partes:
        nome = p.split("(")[0].strip()
        bottlenecks.append(nome)

# === Extrair Lone Wolves ===
m_lone = re.search(r"Lone Wolves: (.+)", texto)
lone_wolves = [m.strip() for m in m_lone.group(1).split(",")] if m_lone else []

# === Criar o grafo ===
G = nx.Graph()

for cid, membros in comunidades.items():
    for i in range(len(membros)-1):
        G.add_edge(membros[i], membros[i+1], comunidade=cid)
    if len(membros) == 1:  # comunidade isolada
        G.add_node(membros[0], comunidade=cid)

# === Cores e tamanhos ===
node_colors = []
node_sizes = []

for n in G.nodes():
    if any(n.startswith(tf) for tf in truck_factor):
        node_colors.append("red")     # Truck Factor
        node_sizes.append(1600)
    elif any(n.startswith(b) for b in bottlenecks):
        node_colors.append("orange")  # Bottleneck
        node_sizes.append(1400)
    elif any(n.startswith(lw) for lw in lone_wolves):
        node_colors.append("gray")    # Lone Wolf
        node_sizes.append(1200)
    else:
        node_colors.append("skyblue") # Normal
        node_sizes.append(600)

# === Layout ===
pos = nx.spring_layout(G, seed=42, k=0.5)

plt.figure(figsize=(16, 12))
nx.draw_networkx_edges(G, pos, alpha=0.3)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9)
nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")

# === Legenda ===
import matplotlib.patches as mpatches
legend_elements = [
    mpatches.Patch(color="orange", label="Bottleneck Leaders"),
    mpatches.Patch(color="red", label="Truck Factor"),
    mpatches.Patch(color="gray", label="Lone Wolf"),
    mpatches.Patch(color="skyblue", label="Outros membros")
]
plt.legend(handles=legend_elements, loc="upper right")

plt.title("📊 Infográfico de Community Smells\n(Organizational Silos, Truck Factor, Bottlenecks e Lone Wolves)", 
          fontsize=14, fontweight="bold")
plt.axis("off")
plt.tight_layout()
plt.savefig("infografico_community_smells.png", dpi=300)
plt.show()
