
import os
import json
import logging
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AGENT PLAYBOOK — SISTEMA DE REGRAS E BASE DE CONHECIMENTO (RAG)
# ---------------------------------------------------------------------------
KNOWLEDGE_BASE = """
## BASE DE CONHECIMENTO — CASOS E PRECEDENTES DA AZUL

### Caso 001 — Falha de Viracopos
- **Contexto:** A Azul cortou os ônibus intermunicipais de conexão em Viracopos
  como medida de redução de custos.
- **Problema:** A decisão foi tomada exclusivamente pela BU de operações,
  sem consulta ao Marketing. O corte quebrou a promessa de conectividade
  ponta-a-ponta que a Azul sempre comunicou em suas campanhas.
- **Consequências:** Reação negativa em redes sociais, clientes stranded,
  cobertura da imprensa, dano reputacional significativo. Foram necessários
  mais de 6 meses e R$ 4 milhões em recuperação de marca.
- **Lições Aprendidas:**
  1. Toda iniciativa que impacte a experiência do cliente DEVE passar pelo
     Marketing ANTES da implementação.
  2. A promessa de conectividade ponta-a-ponta é um dos pilares centrais
     da marca Azul e não pode ser violada.
  3. Reduções de custo que afetam a percepção de qualidade ou
     atendimento exigem avaliação de trade-off de marca.

### Guardrails Inegociáveis da Marca Azul
1. **Conectividade ponta a ponta:** O cliente Azul precisa chegar de
   qualquer lugar do Brasil a qualquer outro lugar. Cortar conexões,
   reduzir malha ou eliminar rotas que quebrem essa promessa é
   inaceitável sem uma estratégia de comunicação equivalente.
2. **Atendimento humanizado:** A Azul é reconhecida pelo melhor
   atendimento do Brasil. Qualquer iniciativa que automatize sem
   alternativa humana, reduza canais de suporte ou elimine o toque
   humano no serviço deve ser sinalizada como ALTO RISCO.
3. **Brasilidade:** A Azul é a companhia aérea que mais conecta o
   Brasil. A marca está intrinsecamente ligada ao orgulho nacional.
   Iniciativas que desconsiderem o contexto regional brasileiro ou
   que prejudiquem a presença da Azul em qualquer região do país
   devem ser questionadas.
"""

SYSTEM_PROMPT = f"""
Você é o Agente de Governança de Marca da Azul Linhas Aéreas (Azul Brand Co-Pilot).
Sua função é analisar iniciativas de negócio propostas pelas Unidades de Negócio (BUs)
e avaliar seu impacto na marca, riscos reputacionais e alinhamento estratégico.

{KNOWLEDGE_BASE}

## REGRAS DE ANÁLISE

Para cada iniciativa recebida, você DEVE avaliar os seguintes eixos e retornar
exclusivamente um JSON válido (sem markdown, sem texto adicional):

{{
  "alinhamento_identidade": "Descreva se a iniciativa está alinhada com os
    pilares de marca da Azul (conectividade, atendimento humanizado,
    brasilidade). Indique pontos de conflito se houver.",
  "fit_publico": "Descreva se a iniciativa atende ao perfil de cliente Azul
    (viajantes de negócios e lazer em todo o Brasil). Aponte
    desalinhamentos com a base de clientes.",
  "maturidade_contexto": "Descreva se a BU demonstrou compreensão do
    contexto de marca ou se a iniciativa parece isolada e sem visão
    estratégica. Indique se há riscos de curto prazoismo.",
  "precedentes_historicos": "Relacione com casos anteriores da base de
    conhecimento (como o Caso 001 - Falha de Viracopos) se houver
    similaridade. Indique se a iniciativa repete erros conhecidos.",
  "risco_reputacional": "Classifique como ALTO, MÉDIO ou BAIXO.
    JUSTIFIQUE a classificação com base nos guardrails e casos
    anteriores.",
  "recomendacao": "Resumo executivo com recomendação clara:
    APROVAR, EXIGIR AJUSTES, ou BLOQUEAR. Explique o racional."
}}

### IMPORTANTE ###
- Não adicione nenhum texto fora do JSON.
- O JSON deve ser válido e parseável.
- Seja rigoroso na aplicação dos guardrails.
- Se a iniciativa tocar em conectividade ou atendimento humanizado,
  o risco reputacional deve ser no mínimo MÉDIO.
"""


# ---------------------------------------------------------------------------
# MOCK AGENT (substitua por chamada real à LLM)
# ---------------------------------------------------------------------------
def analyze_with_llm(bu_name: str, project_idea: str) -> dict:
    """
    Placeholder — em produção, substitua pela chamada ao modelo de IA
    (OpenAI, Anthropic, Llama, etc.) usando SYSTEM_PROMPT como system message.
    """
    logger.info("Analisando iniciativa | BU: %s | Ideia: %.80s...", bu_name, project_idea)

    # --- Mock inteligente baseado nas regras de negócio ---
    idea_lower = project_idea.lower()
    has_connectivity_risk = any(w in idea_lower for w in [
        "cortar", "corte", "eliminar", "reduzir conex", "remover rota",
        "cancelar voo", "diminuir malha", "fechar base", "ônibus", "transporte",
        "intermunicipal", "conexão", "conectividade"
    ])
    has_service_risk = any(w in idea_lower for w in [
        "chatbot", "automatizar", "sem humano", "reduzir atendimento",
        "eliminar suporte", "remover canal", "call center", "sac",
    ])
    has_brazil_context = any(w in idea_lower for w in [
        "brasil", "região", "norte", "nordeste", "amazônia", "regional"
    ])

    if has_connectivity_risk and has_service_risk:
        risk = "ALTO"
        recommendation = (
            "BLOQUEAR. A iniciativa agride simultaneamente dois guardrails "
            "inegociáveis da marca (conectividade ponta-a-ponta e atendimento "
            "humanizado). Remete ao Caso 001 — Falha de Viracopos. Exigimos "
            "revisão completa com participação obrigatória do Marketing."
        )
    elif has_connectivity_risk:
        risk = "ALTO"
        recommendation = (
            "EXIGIR AJUSTES. A iniciativa impacta a conectividade ponta-a-ponta, "
            "pilar central da marca Azul. Similar ao Caso 001. A BU deve apresentar "
            "plano de comunicação e mitigação antes de qualquer implementação."
        )
    elif has_service_risk:
        risk = "MÉDIO"
        recommendation = (
            "EXIGIR AJUSTES. Redução de atendimento humanizado fere o "
            "posicionamento de marca. A BU precisa demonstrar que haverá "
            "alternativa humana equivalente e plano de comunicação."
        )
    elif has_brazil_context:
        risk = "BAIXO"
        recommendation = (
            "APROVAR com monitoramento. A iniciativa considera o contexto "
            "regional brasileiro, alinhada ao pilar de brasilidade. "
            "Recomendamos acompanhamento trimestral de impacto."
        )
    else:
        risk = "BAIXO"
        recommendation = (
            "APROVAR. A iniciativa não aparenta conflitar com os pilares "
            "de marca ou guardrails. Recomendamos avaliação contínua."
        )

    # Precedentes históricos
    if has_connectivity_risk:
        precedents = (
            "Similar ao Caso 001 — Falha de Viracopos, onde o corte de "
            "conectividade gerou crise reputacional severa."
        )
    else:
        precedents = (
            "Nenhum precedente crítico identificado. A iniciativa não repete "
            "padrões de risco conhecidos na base de conhecimento."
        )

    recommendation_text = recommendation.replace("BLOQUEAR. ", "").replace("EXIGIR AJUSTES. ", "").replace("APROVAR com monitoramento. ", "").replace("APROVAR. ", "")

    return {
        "alinhamento": (
            "Conectividade ponta-a-ponta é o principal pilar de identidade "
            "da Azul. A iniciativa precisa ser avaliada sob essa lente."
            if has_connectivity_risk or has_service_risk else
            "Alinhado à identidade de marca. A iniciativa respeita os pilares "
            "de conectividade, atendimento humanizado e brasilidade."
        ),
        "risco": risk,
        "recomendacao": recommendation,
        "alinhamento_identidade": (
            "Conectividade ponta-a-ponta é o principal pilar de identidade "
            "da Azul. A iniciativa precisa ser avaliada sob essa lente."
            if has_connectivity_risk or has_service_risk else
            "Alinhado à identidade de marca. A iniciativa respeita os pilares "
            "de conectividade, atendimento humanizado e brasilidade."
        ),
        "fit_publico": (
            "O público Azul valoriza a capilaridade e o atendimento. "
            "A iniciativa pode gerar insatisfação se percebida como perda "
            "de qualidade."
            if has_connectivity_risk or has_service_risk else
            "Adequado ao perfil do cliente Azul. A iniciativa atende "
            "viajantes de negócios e lazer em todo o Brasil."
        ),
        "maturidade_contexto": (
            "A BU parece focada em redução de custos imediata sem considerar "
            "o impacto sistêmico de marca. Risco de curto prazoismo."
            if has_connectivity_risk else
            "A BU demonstra compreensão do contexto estratégico. "
            "A iniciativa considera os Pilares de Marca."
        ),
        "precedentes_historicos": precedents,
        "risco_reputacional": risk,
    }


# ---------------------------------------------------------------------------
# ROTA DA API
# ---------------------------------------------------------------------------
@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Endpoint principal de análise.
    Recebe: { "bu_name": "...", "project_idea": "..." }
    Retorna JSON com a análise estruturada do agente.
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "JSON inválido ou ausente"}), 400

    bu_name = body.get("bu_name", "").strip()
    project_idea = body.get("project_idea", "").strip()

    if not bu_name:
        return jsonify({"error": "Campo 'bu_name' é obrigatório"}), 400
    if not project_idea:
        return jsonify({"error": "Campo 'project_idea' é obrigatório"}), 400

    logger.info("Requisição recebida — BU: %s", bu_name)

    result = analyze_with_llm(bu_name, project_idea)

    # Adiciona metadados
    result["analisado_em"] = datetime.utcnow().isoformat() + "Z"
    result["bu_responsavel"] = bu_name

    return jsonify(result), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "agent": "Azul Brand Co-Pilot v1.0"}), 200


# ---------------------------------------------------------------------------
# SERVE FRONT-END (SPA)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    logger.info("Azul Brand Co-Pilot Agent iniciado na porta %d", port)
    app.run(host="0.0.0.0", port=port, debug=True)
