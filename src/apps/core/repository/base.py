import os  # noqa: I001
from abc import ABC, abstractmethod
from neo4j import GraphDatabase
from django.conf import settings
from dotenv import load_dotenv  # noqa: I001

class Neo4jRepository(ABC):

    def __init__(self):
        load_dotenv()
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", ""),
            auth=(os.getenv("NEO4J_USERNAME", ""), os.getenv("NEO4J_PASSWORD", ""))
        )

    def execute(self, query, skip=0, limit=50, params=None): # Adicionar params=None
        if params is None:
            params = {}
        
        # Adicionar skip e limit ao dicionário de parâmetros (se sua query usa $skip/$limit)
        # Se você está fazendo a paginação no Python (executando apenas a query e fatiando), 
        # ignore os parâmetros de paginação no Cypher e continue:

        with self.driver.session() as session:
            # O Neo4j driver junta os parâmetros de query e os parâmetros nomeados
            result = session.run(query, **params) 
            
            # Filtra a lista se você estiver fazendo paginação na aplicação (não é o ideal para grandes dados)
            raw_data = [record.data() for record in result]
            
            # Se você está paginando no Python (como a maioria dos exemplos)
            if skip > 0:
                raw_data = raw_data[skip:]
            if limit > 0:
                raw_data = raw_data[:limit]
                
            return raw_data
        
    def close(self):
        self.driver.close()

   