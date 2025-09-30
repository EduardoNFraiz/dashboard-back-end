## Setup 

Ser o .env antes de rodar

'''
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=
GEMINI_KEY

'''

## Running

# Cria as relacoes de coodernacao e co-trabalho
make build 

# Cria as analises e gerar o markdown e salva em reports 
make analyse 

# Cria explicacoes com I 
make report 
