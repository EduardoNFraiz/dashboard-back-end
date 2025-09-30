from neo4j import GraphDatabase
import sys

sys.stdout.reconfigure(encoding="utf-8")

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

# === Dicionário de papéis ===
roles = {
    "leader": {
        "MateusLannes","vinicius-je","marcelasfl","joaomrpimentel","oliverids",
        "gabrieldpbrunetti","JenniferAmaral", "ManoelRL",
        "sofialctv","diogoanb-dev","malumantovanelli"
    },
    "consultant": {
        "RobsonGarcia","franciscorj","LuizRojas","felipefo","MayaraPimenta" ,"rafaelrezo","victoriocarvalho","jvcosmo", "igorcarlospulini", "LEDS", "barcx"
    },
    "chief": {
        "paulossjunior" 
    }
}

# === Função para atualizar papéis no Neo4j ===
def definir_papeis(driver, roles_dict):
    with driver.session() as session:
        for role, pessoas in roles_dict.items():
            for pessoa in pessoas:
                session.run("""
                    MATCH (p:person {name:$nome})
                    SET p.role = $role
                """, nome=pessoa, role=role)
                print(f"✅ {pessoa} definido como {role}")

# === Main ===
if __name__ == "__main__":
    definir_papeis(driver, roles)
    driver.close()
    print("\n✅ Atualização de papéis concluída!")
