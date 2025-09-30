# Setup 

Setar o .env antes de rodar

´´´
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=
GEMINI_KEY=
´´´


# Running

## Cria as relacoes de coodernacao e co-trabalho
make build 

## Cria as analises e gerar o markdown e salva em reports 
make analyse 

## Cria explicacoes com I 
make report 



# Como cada smell é calculado 

## Dicionário de explicações técnicas 

- **Bottleneck**:
-- **Bottleneck (leaders)**: Identifies leaders who concentrate many connections. In this case, leaders impose their participation in several tasks. A bottleneck leader can cause overload and block the workflow if not acting properly.
-- **Boundary Spanners**: Critical and disconnected people within the team who connect their team to other teams. They are vital links for inter-team collaboration.
- **Organizational Silos**: Subgroups that interact more with each other than with the rest. Indicates communication barriers between teams.
- **Lone Wolf**: People in the team who cannot reach all others. They represent communication gaps that need to be addressed.
- **Truck Factor**: Individuals whose removal disconnects the network. They are single points of vulnerability.

## Formula para calulo 

### Visão do time

- **Bottleneck**
-- **Bottleneck (leaders)**: (Degree centrality >=2 ou betweenes >= 2 ) e role="leader" .
-- **Boundary Spanners**: Articulação que conecte a mais de dois times. 
- **Organizational Silos**: Detecção de comunidades greedy_modularity_communities.
- **Lone Wolf**: Grau igual a zeo
- **Truck Factor**: Articulation points (não-dirigido): nós cuja remoção aumenta nº de componentes dentro do time.


### Visão por tempo
-- **Bottleneck (leaders)**: (Degree centrality >=2 ou betweenes >= 2 ) e role="leader" .
-- **Boundary Spanners**: Articulação que conecte a mais de dois times. 
- **Organizational Silos**: Detecção de comunidades greedy_modularity_communities.
- **Lone Wolf**: Grau igual a zeo
- **Truck Factor**: Articulation points (não-dirigido): nós cuja remoção aumenta nº de componentes dentro do time.














