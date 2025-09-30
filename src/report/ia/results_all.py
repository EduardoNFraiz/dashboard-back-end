

import google.generativeai as genai

from dotenv import load_dotenv
import os
from pathlib import Path

# ===== Carregar variáveis do .env =====
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

# Carregar o .env explicitamente
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_KEY = os.getenv("GEMINI_KEY")


# === Configuração da API Gemini ===
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# === Dicionário de explicações técnicas ===
explicacoes = {
    "bottleneck": "Bottleneck (leaders): Identifies leaders who concentrate many connections. In this case, leaders impose their participation in several tasks. A bottleneck leader can cause overload and block the workflow if not acting properly.",
    "silos": "Organizational Silos: Subgroups that interact more with each other than with the rest. Indicates communication barriers between teams.",
    "lone": "Lone Wolf: People in the team who cannot reach all others. They represent communication gaps that need to be addressed.",
    "factor": "Truck Factor: Individuals whose removal disconnects the network. They are single points of vulnerability.",
    "bound": "Boundary Spanners: Critical and disconnected people within the team who connect their team to other teams. They are vital links for inter-team collaboration.",
}

# === Função para ler markdown ===
def ler_markdown(caminho_md):
    with open(caminho_md, "r", encoding="utf-8") as f:
        return f.read()

# === Função para gerar explicações amigáveis ===
def gerar_relatorio_para_gestor(conteudo_md):
    # junta todas as explicações como texto único
    todas_explicacoes = "\n".join([f"- {v}" for v in explicacoes.values()])

    prompt = f"""
    You are a project management consultant and very knowledgeable about community smells.
    Below are the technical definitions of each smell that may appear:

    ### Technical definitions of community smells:
    {todas_explicacoes}


    Now, here are the analyzed results from GitHub commits, pull requests, and issues regarding community smells for the entire project(in Markdown):

    ### Analyzed results for the entire group (.md):
    {conteudo_md}

    Task:
    - Analyze the project technical report and write everything in corrected text form, as if it were a formal report, 
    - Dot not generate recommendations for improvement, just anaylze the smells. 
    - Use a clear and accessible language for managers and entry-level leader.  
    - Use simple language without technical jargon; use community smell terms but also explain what they mean.  
    - Use english as output. 
    
     Output as the sample bellow:
    
Report from inicial data x to end y, fulano is a key go-to person across tasks and conversations; that’s great for coordination, but it also risks overload.
We see small groups that mostly talk among themselves, and franciscorj is working apart from the rest; Person 1, Person 2 and person 2 don’t reach everyone yet.
On the bright side, the team doesn’t hinge on any single person—if someone steps away, work can still move forward.
  
    
    """

    resposta = model.generate_content(prompt)
    return resposta.text.strip()

# === Processar arquivo MD ===
def analisar_md(caminho_md):
    conteudo = ler_markdown(caminho_md)
    return gerar_relatorio_para_gestor(conteudo)

# === Exemplo de uso ===
if __name__ == "__main__":
    caminho = "../reports/analyse_community_smells_global.md"  # seu arquivo MD
    resultado = analisar_md(caminho)

    # Salva saída em outro .md
    with open("relatorio_gestor.md", "w", encoding="utf-8") as f:
        f.write(resultado)

    print("✅ Relatório pronto em relatorio_gestor.md")
    
