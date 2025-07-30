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

    def close(self):
        self.driver.close()

   