import os
import logging
import socket
import sys
from datetime import datetime, timezone
from uuid import uuid4
import urllib.request
import json
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "src", "assets"))
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega as variáveis do arquivo .env manualmente
def load_dotenv():
    # Procura pelo .env no diretório pai ou no atual
    paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        ".env"
    ]
    for path in paths:
        if os.path.exists(path):
            logger.info("Carregando variáveis de ambiente de %s", path)
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
            break

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


KNOWLEDGE_BASE = """
## BASE DE CONHECIMENTO — CASOS E PRECEDENTES DA AZUL

### Caso 001 — Falha de Viracopos
- **Contexto:** A Azul cortou os ônibus intermunicipais de conexão em Viracopos como medida de redução de custos.
- **Problema:** A decisão foi tomada exclusivamente pela BU de operações, sem consulta ao Marketing.
- **Consequências:** Reação negativa em redes sociais, clientes stranded, dano reputacional significativo.
- **Lições Aprendidas:**
  1. Toda iniciativa que impacte a experiência do cliente DEVE passar pelo Marketing ANTES da implementação.
  2. A promessa de conectividade ponta-a-ponta é um dos pilares centrais da marca Azul.
  3. Reduções de custo que afetam a percepção de qualidade exigem avaliação de trade-off de marca.

### Guardrails Inegociáveis da Marca Azul
1. **Conectividade ponta a ponta:** Cortar conexões ou reduzir malha é inaceitável sem estratégia de comunicação equivalente.
2. **Atendimento humanizado:** Qualquer iniciativa que automatize sem alternativa humana deve ser sinalizada como ALTO RISCO.
3. **Brasilidade:** Iniciativas que desconsiderem o contexto regional brasileiro ou prejudiquem a presença da Azul em qualquer região do país devem ser questionadas.
"""

CREATE_ALLOWED_ROLES = {"coordenador", "gerente", "diretor", "executivo", "vp_superintendente"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def analyze_by_keywords(bu_name: str, project_idea: str) -> dict:
    logger.info("Analisando iniciativa | BU: %s | Ideia: %.80s...", bu_name, project_idea)

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

    # termos sensíveis que exigem atenção independente de brasilidade positiva
    sensitive_terms = ["desmatamento", "desflorestamento", "queimada", "mineração", "exploração", "grilagem"]
    has_sensitive = any(w in idea_lower for w in sensitive_terms)

    if has_connectivity_risk and has_service_risk:
        risk = "ALTO"
        recommendation = (
            "BLOQUEAR. A iniciativa agride simultaneamente conectividade e atendimento humanizado. "
            "Remete ao Caso 001 — Falha de Viracopos."
        )
    elif has_connectivity_risk:
        risk = "ALTO"
        recommendation = (
            "EXIGIR AJUSTES. A iniciativa impacta a conectividade ponta-a-ponta e deve passar por "
            "mitigação e comunicação antes da implementação."
        )
    elif has_service_risk:
        risk = "MÉDIO"
        recommendation = (
            "EXIGIR AJUSTES. Redução de atendimento humanizado fere o posicionamento de marca."
        )
    elif has_brazil_context and not has_sensitive:
        # brasilidade é vista como ponto positivo — não reduz automaticamente riscos já identificados
        risk = "BAIXO"
        recommendation = (
            "APROVAR com monitoramento. A iniciativa considera o contexto regional brasileiro e agrega brasilidade positiva."
        )
    elif has_sensitive:
        # casos sensíveis relacionados a impacto socioambiental exigem revisão rigorosa
        risk = "ALTO"
        recommendation = (
            "BLOQUEAR/EXIGIR AJUSTES. A iniciativa menciona temas socioambientais sensíveis (ex.: desmatamento, exploração). "
            "Exigir avaliação de impacto socioambiental, jurídico e consulta ao Marketing antes de qualquer avanço."
        )
    else:
        risk = "BAIXO"
        recommendation = "APROVAR. A iniciativa não aparenta conflitar com os pilares de marca."

    if has_connectivity_risk:
        precedents = "Similar ao Caso 001 — Falha de Viracopos, onde o corte de conectividade gerou crise reputacional."
    else:
        precedents = "Nenhum precedente crítico identificado."

    return {
        "alinhamento_identidade": (
            "Conectividade ponta-a-ponta é o principal pilar de identidade da Azul. A iniciativa precisa ser avaliada sob essa lente."
            if has_connectivity_risk or has_service_risk else
            "Alinhado à identidade de marca. A iniciativa respeita os pilares de conectividade, atendimento humanizado e brasilidade."
        ),
        "fit_publico": (
            "O público Azul valoriza capilaridade e atendimento. A iniciativa pode causar insatisfação se percebida como perda de qualidade."
            if has_connectivity_risk or has_service_risk else
            "Adequado ao perfil do cliente Azul. A iniciativa atende viajantes de negócios e lazer em todo o Brasil."
        ),
        "maturidade_contexto": (
            "A BU parece focada em redução de custos imediata sem considerar o impacto sistêmico de marca."
            if has_connectivity_risk else
            "A BU demonstra compreensão do contexto estratégico."
        ),
        "precedentes_historicos": precedents,
        "risco_reputacional": risk,
        "recomendacao": recommendation,
    }


def analyze_with_llm(bu_name: str, project_idea: str) -> dict:
    return analyze_by_keywords(bu_name, project_idea)


def mentor_project(bu_name: str, project_idea: str) -> dict:
    idea_lower = project_idea.lower()

    risks = []
    bonuses = []

    connectivity_keywords = ["cortar", "corte", "eliminar", "reduzir conex", "remover rota",
                            "cancelar voo", "diminuir malha", "fechar base", "ônibus",
                            "intermunicipal", "conexão", "conectividade"]
    service_keywords = ["chatbot", "automatizar", "sem humano", "reduzir atendimento",
                        "eliminar suporte", "remover canal", "call center", "sac"]
    brazil_keywords = ["brasil", "região", "norte", "nordeste", "amazônia", "regional",
                       "sul", "sudeste", "centro-oeste"]
    innovation_keywords = ["inovação", "digital", "app", "plataforma", "data", "ia",
                           "inteligência artificial", "machine learning", "personalização"]

    has_connectivity = any(w in idea_lower for w in connectivity_keywords)
    has_service = any(w in idea_lower for w in service_keywords)
    has_brazil = any(w in idea_lower for w in brazil_keywords)
    has_innovation = any(w in idea_lower for w in innovation_keywords)

    if has_connectivity:
        risks.append("conectividade")
    if has_service:
        risks.append("atendimento humanizado")

    if has_brazil:
        bonuses.append("brasilidade")
    if has_innovation:
        bonuses.append("inovação")

    if has_connectivity and has_service:
        veredito = "BLOQUEAR"
        risco = "ALTO"
        justificativa = "A iniciativa agride simultaneamente conectividade e atendimento humanizado."
        sugestao = "Repensar a abordagem garantindo que os pilares de marca não sejam comprometidos."
    elif has_connectivity:
        veredito = "EXIGIR AJUSTES"
        risco = "ALTO"
        justificativa = "A iniciativa impacta a conectividade ponta-a-ponta da Azul."
        sugestao = "Criar plano de mitigação e comunicação antes da implementação."
    elif has_service:
        veredito = "EXIGIR AJUSTES"
        risco = "MÉDIO"
        justificativa = "Redução de atendimento humanizado fere o posicionamento de marca."
        sugestao = "Preservar canal humano como alternativa obrigatória."
    else:
        veredito = "APROVAR"
        risco = "BAIXO"
        justificativa = "A iniciativa respeita os pilares de marca da Azul."
        sugestao = "Seguir com monitoramento de rotina."

    precedentes = "Similar ao Caso 001 — Falha de Viracopos." if has_connectivity else "Nenhum precedente crítico identificado."

    return {
        "titulo_projeto": project_idea[:60],
        "unidade_negocio": bu_name,
        "objetivo_executivo": f"Iniciativa da {bu_name} para {project_idea[:100]}",
        "aderencia_marca_azul": "Crítico" if has_connectivity or has_service else "Adequado",
        "publico_alvo_impacto": "Impacto direto na experiência do cliente" if has_connectivity or has_service else "Público-alvo compatível com a marca Azul",
        "recursos_necessarios": "Avaliação adicional necessária para estimativa de recursos.",
        "mentoria": {
            "veredito": veredito,
            "risco": risco,
            "justificativa": justificativa,
            "sugestao": sugestao,
            "precedentes_historicos": precedentes,
        }
    }


def calculate_brand_strength(project: dict) -> dict:
    title_summary = f"{project.get('title', '')} {project.get('summary', '')}".lower()
    score = 100
    criterios = []

    connectivity_penalties = ["cortar", "corte", "eliminar", "reduzir conex", "remover rota",
                             "cancelar voo", "diminuir malha", "fechar base"]
    service_penalties = ["chatbot", "automatizar", "sem humano", "reduzir atendimento",
                         "eliminar suporte", "remover canal"]
    brazil_bonus = ["brasil", "região", "norte", "nordeste", "amazônia", "regional"]
    innovation_bonus = ["inovação", "digital", "app", "plataforma", "ia",
                        "inteligência artificial", "personalização"]

    if any(w in title_summary for w in connectivity_penalties):
        score -= 25
        criterios.append({"criterio": "Conectividade", "impacto": -25, "detalhe": "Impacto na conectividade ponta-a-ponta"})
    else:
        criterios.append({"criterio": "Conectividade", "impacto": 0, "detalhe": "Sem impacto identificado"})

    if any(w in title_summary for w in service_penalties):
        score -= 20
        criterios.append({"criterio": "Atendimento Humanizado", "impacto": -20, "detalhe": "Risco ao atendimento humanizado"})
    else:
        criterios.append({"criterio": "Atendimento Humanizado", "impacto": 0, "detalhe": "Sem risco identificado"})

    if any(w in title_summary for w in brazil_bonus):
        score += 10
        criterios.append({"criterio": "Brasilidade", "impacto": 10, "detalhe": "Foco no contexto regional brasileiro"})
    else:
        criterios.append({"criterio": "Brasilidade", "impacto": 0, "detalhe": "Sem referência regional"})

    if any(w in title_summary for w in innovation_bonus):
        score += 5
        criterios.append({"criterio": "Inovação", "impacto": 5, "detalhe": "Iniciativa com caráter inovador"})
    else:
        criterios.append({"criterio": "Inovação", "impacto": 0, "detalhe": "Sem caráter inovador explícito"})

    score = max(0, min(100, score))

    if score >= 80:
        nivel = "FORTE"
        descricao = "Marca bem posicionada. A iniciativa está alinhada aos pilares da Azul."
    elif score >= 50:
        nivel = "MODERADA"
        descricao = "Marca com ressalvas. A iniciativa requer ajustes para alinhamento total."
    else:
        nivel = "FRACA"
        descricao = "Marca sob risco. A iniciativa conflita significativamente com os pilares da Azul."

    return {
        "pontuacao": score,
        "nivel": nivel,
        "descricao": descricao,
        "criterios": criterios,
    }


def generate_verdict(project, brand_strength, similarity) -> dict:
    score = brand_strength["pontuacao"]
    similar_score = similarity.get("similarityScore", 0)

    if score >= 80 and not similarity.get("hasSimilarProjects"):
        classificacao = "Investimento Prioritário"
        plano_acao = "Aprovar e acelerar. Projeto alinhado à marca e sem concorrência interna."
    elif score >= 50 and similar_score > 50:
        classificacao = "Aprovação Condicional"
        plano_acao = f"Fusão recomendada com projeto similar (similaridade: {similar_score}%). Consolidar antes de aprovar."
    elif score >= 50:
        classificacao = "Aprovação Condicional"
        plano_acao = "Aprovar com monitoramento. Ajustes pontuais podem ser necessários."
    else:
        classificacao = "Banco de Ideias"
        plano_acao = "Revisar e reformular. Projeto requer alinhamento estratégico com a marca."

    return {
        "classificacao": classificacao,
        "plano_acao": plano_acao,
        "score_brand_strength": score,
    }


PROJECTS = [
    {
        "id": "proj-001",
        "title": "Conexão Regional Premium",
        "summary": "Projeto para fortalecer a conexão entre rotas regionais e o ecossistema Azul Viagens, com foco em experiências premium para clientes de fora do eixo sul-sudeste.",
        "org": "Azul Viagens",
        "areas": ["Marketing", "Produtos"],
        "ownerRole": "Gerente",
        "similarityScore": 24,
        "similarityType": "Leves similaridades",
        "marketingAlert": False,
        "alertReason": "Sem alertas críticos. O projeto respeita os pilares de conectividade, atendimento humanizado e brasilidade. Monitoramento de rotina recomendado.",
        "alertSeverity": "BAIXA",
        "comments": [
            {"id": "c1", "author": "Bruna", "role": "Analista", "text": "Gostei do foco nas rotas regionais. Podemos incorporar uma nota de brasilidade no posicionamento."}
        ],
        "createdAt": "2026-07-10T15:00:00Z",
        "references": ["Programa de fidelidade regional", "Campanha de conexão nacional"],
        "votes": [
            {"userId": "u1", "userName": "Carla Nogueira", "role": "Gerente", "vote": "qualificado", "timestamp": "2026-07-11T10:00:00Z"},
            {"userId": "u3", "userName": "Ana Beatriz", "role": "Diretor", "vote": "qualificado", "timestamp": "2026-07-11T14:30:00Z"},
        ]
    },
    {
        "id": "proj-002",
        "title": "Assistente de atendimento humano",
        "summary": "Ambiente de IA para apoio ao SAC, com transição automática para um atendente humano em caso de falhas ou casos complexos.",
        "org": "Azul Conecta",
        "areas": ["TI", "Customer Experience"],
        "ownerRole": "Analista",
        "similarityScore": 68,
        "similarityType": "Objetivos parecidos",
        "marketingAlert": True,
        "alertReason": "ALERTA DE IMAGEM: O projeto menciona chatbot, sac. Impacto potencial: percepção negativa do cliente sobre o atendimento humanizado da Azul. Ação necessária: garantir que o atendimento humano seja preservado como alternativa.",
        "alertSeverity": "MÉDIA",
        "comments": [
            {"id": "c2", "author": "Mateus", "role": "Gerente", "text": "A proposta precisa deixar claro que o canal humano não será removido."}
        ],
        "createdAt": "2026-07-12T10:20:00Z",
        "references": ["Chatbot de atendimento", "Rota de suporte 24h"],
        "votes": [
            {"userId": "u2", "userName": "Rafael Costa", "role": "Analista", "vote": "nao_qualificado", "timestamp": "2026-07-13T08:00:00Z"},
            {"userId": "u6", "userName": "Pedro Alves", "role": "Supervisor", "vote": "nao_qualificado", "timestamp": "2026-07-13T09:15:00Z"},
            {"userId": "u4", "userName": "Carlos Mendes", "role": "Coordenador", "vote": "qualificado", "timestamp": "2026-07-13T11:00:00Z"},
            {"userId": "u7", "userName": "Fernanda Lima", "role": "Executivo", "vote": "qualificado", "timestamp": "2026-07-14T08:30:00Z"},
            {"userId": "u3", "userName": "Ana Beatriz", "role": "Diretor", "vote": "nao_qualificado", "timestamp": "2026-07-14T10:00:00Z"},
            {"userId": "u8", "userName": "Luciana Rocha", "role": "VP / Superintendente", "vote": "nao_qualificado", "timestamp": "2026-07-14T16:00:00Z"},
            {"userId": "u5", "userName": "Juliana Souza", "role": "Especialista", "vote": "qualificado", "timestamp": "2026-07-15T08:00:00Z"},
        ]
    },
]


USERS = [
    {"id": "u1", "name": "Carla Nogueira", "roleLevel": "Gerente", "org": "Azul Viagens", "area": "Marketing", "isMarketing": True},
    {"id": "u2", "name": "Rafael Costa", "roleLevel": "Analista", "org": "Azul TechOps", "area": "TI", "isMarketing": False},
    {"id": "u3", "name": "Ana Beatriz", "roleLevel": "Diretor", "org": "Azul Logística", "area": "Operações", "isMarketing": True},
    {"id": "u4", "name": "Carlos Mendes", "roleLevel": "Coordenador", "org": "Azul Fidelidade", "area": "Produtos", "isMarketing": True},
    {"id": "u5", "name": "Juliana Souza", "roleLevel": "Especialista", "org": "Azul Conecta", "area": "TI", "isMarketing": False},
    {"id": "u6", "name": "Pedro Alves", "roleLevel": "Supervisor", "org": "Azul Viagens", "area": "Customer Experience", "isMarketing": True},
    {"id": "u7", "name": "Fernanda Lima", "roleLevel": "Executivo", "org": "Azul TechOps", "area": "Comercial", "isMarketing": True},
    {"id": "u8", "name": "Luciana Rocha", "roleLevel": "VP / Superintendente", "org": "Azul Logística", "area": "Jurídico", "isMarketing": True},
    {"id": "u9", "name": "Mariana Tavares", "roleLevel": "Analista", "org": "Azul Conecta", "area": "Marketing", "isMarketing": True},
    {"id": "u10", "name": "Roberto Faria", "roleLevel": "Gerente", "org": "Azul Fidelidade", "area": "Finanças", "isMarketing": True},
]


def calculate_project_alerts(project: dict) -> dict:
    title_summary = f"{project['title']} {project['summary']}".lower()
    conflicts_found = []
    image_risks_found = []

    conflict_keywords = {"cortar": "corte de conectividade/rotas", "remover": "remoção de serviço", "eliminar": "eliminação de canal ou rota", "reduzir": "redução de malha ou atendimento", "cancelar": "cancelamento de voo/serviço", "corte": "corte de operação", "diminuir": "diminuição de malha", "fechar": "fechamento de base"}
    image_keywords = {"automação sem humano": "automação sem alternativa humana", "chatbot": "chatbot sem suporte humano", "sac": "alteração no SAC", "baixo custo": "estratégia de baixo custo", "sem humano": "remoção do atendimento humano"}

    conflict = False
    for word, desc in conflict_keywords.items():
        if word in title_summary:
            conflicts_found.append(desc)
            conflict = True

    image_risk = False
    for word, desc in image_keywords.items():
        if word in title_summary:
            image_risks_found.append(desc)
            image_risk = True

    guardrail_risk = conflict or image_risk

    if conflict and image_risk:
        reason_parts = [
            "RISCOS IDENTIFICADOS:",
            f"  • Violação de guardrails: {', '.join(conflicts_found)}.",
            f"  • Risco de imagem: {', '.join(image_risks_found)}.",
            "Impacto potencial: dano reputacional, reação negativa em redes sociais, perda de confiança do cliente.",
            "Ação necessária: revisão obrigatória pelo Marketing antes de qualquer implementação.",
        ]
        severity = "ALTA"
    elif conflict:
        reason_parts = [
            f"ALERTA DE CONFLITO: O projeto apresenta indicativos de {', '.join(conflicts_found)}.",
            "Impacto potencial: violação das guardrails de conectividade ponta-a-ponta da Azul.",
            "Ação necessária: submeter ao comitê de marca para avaliação de trade-off.",
        ]
        severity = "ALTA"
    elif image_risk:
        reason_parts = [
            f"ALERTA DE IMAGEM: O projeto menciona {', '.join(image_risks_found)}.",
            "Impacto potencial: percepção negativa do cliente sobre o atendimento humanizado da Azul.",
            "Ação necessária: garantir que o atendimento humano seja preservado como alternativa.",
        ]
        severity = "MÉDIA"
    else:
        reason_parts = [
            "Nenhum risco crítico identificado automaticamente.",
            "O projeto respeita os pilares de conectividade, atendimento humanizado e brasilidade.",
            "Monitoramento de rotina recomendado.",
        ]
        severity = "BAIXA"

    return {
        "needsMarketing": guardrail_risk,
        "reason": " ".join(reason_parts),
        "severity": severity,
    }


def find_similar_projects(project: dict, all_projects: list[dict]) -> dict:
    from difflib import SequenceMatcher

    current_text = f"{project['title']} {project['summary']}".lower()
    matches = []
    for candidate in all_projects:
        if candidate['id'] == project['id']:
            continue
        candidate_text = f"{candidate['title']} {candidate['summary']}".lower()
        overlap = len(set(current_text.split()) & set(candidate_text.split()))
        similarity_ratio = SequenceMatcher(None, current_text, candidate_text).ratio()
        similarity = round(min(100, max(overlap * 12, similarity_ratio * 100)), 1)
        if overlap >= 2 and similarity >= 50:
            matches.append({
                'id': candidate['id'],
                'title': candidate['title'],
                'similarity': similarity,
                'org': candidate['org'],
            })

    if not matches:
        return {
            'hasSimilarProjects': False,
            'similarityScore': 0,
            'notifications': ['marketing'],
            'matches': [],
        }

    best = max(matches, key=lambda item: item['similarity'])
    return {
        'hasSimilarProjects': True,
        'similarityScore': best['similarity'],
        'notifications': ['marketing'],
        'matches': matches,
    }


def compute_project_qualification(project: dict) -> dict:
    votes = project.get("votes", [])
    qualificado_count = sum(1 for v in votes if v["vote"] == "qualificado")
    nao_qualificado_count = sum(1 for v in votes if v["vote"] == "nao_qualificado")
    total_votes = len(votes)

    director_qualificado = [v for v in votes if v["vote"] == "qualificado" and v.get("role") in ("Diretor", "Executivo", "VP / Superintendente")]
    director_nao_qualificado = [v for v in votes if v["vote"] == "nao_qualificado" and v.get("role") in ("Diretor", "Executivo", "VP / Superintendente")]

    if total_votes == 0:
        status = "pending"
        status_message = "Aguardando feedback de revisão."
    else:
        status = "revisao"
        status_message = "Os votos funcionam como feedback de revisão e não definem aprovação automática."

    return {
        "qualificado": qualificado_count,
        "nao_qualificado": nao_qualificado_count,
        "total": total_votes,
        "status": status,
        "status_message": status_message,
        "director_qualificado": [{"userName": v["userName"], "role": v["role"]} for v in director_qualificado],
        "director_nao_qualificado": [{"userName": v["userName"], "role": v["role"]} for v in director_nao_qualificado],
    }


@app.route("/api/projects/<project_id>/vote", methods=["POST"])
def vote_on_project(project_id: str):
    project = next((p for p in PROJECTS if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Projeto não encontrado"}), 404

    body = request.get_json(silent=True) or {}
    vote_value = body.get("vote")
    if vote_value not in ("qualificado", "nao_qualificado"):
        return jsonify({"error": "Voto deve ser 'qualificado' ou 'nao_qualificado'"}), 400

    user_id = body.get("userId") or f"user-{uuid4().hex[:6]}"
    user_name = body.get("userName", "Usuário")
    user_role = body.get("role", "Analista")

    existing_vote = next((v for v in project.setdefault("votes", []) if v["userId"] == user_id), None)
    if existing_vote:
        existing_vote["vote"] = vote_value
        existing_vote["timestamp"] = utc_now_iso()
        existing_vote["role"] = user_role
        existing_vote["userName"] = user_name
    else:
        project["votes"].append({
            "userId": user_id,
            "userName": user_name,
            "role": user_role,
            "vote": vote_value,
            "timestamp": utc_now_iso(),
        })

    qualification = compute_project_qualification(project)
    return jsonify({"project": project, "qualification": qualification}), 200


@app.route("/api/projects/<project_id>/qualification", methods=["GET"])
def get_qualification(project_id: str):
    project = next((p for p in PROJECTS if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Projeto não encontrado"}), 404
    qualification = compute_project_qualification(project)
    return jsonify({"qualification": qualification, "project": project}), 200


def _call_gemini(system_instruction: str, user_text: str) -> str | None:
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY não configurada")
        return None

    model_name = "models/gemma-4-26b-a4b-it"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}]
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode())
            candidates = res_data.get("candidates", [])
            if not candidates:
                return None

            parts = candidates[0].get("content", {}).get("parts", [{}])
            raw_text = "".join(p.get("text", "") for p in parts if not p.get("thought", False))

            match = re.search(r'<response>(.*?)</response>', raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            elif "<response>" in raw_text.lower():
                split_parts = re.split(r'<response>', raw_text, flags=re.IGNORECASE)
                return split_parts[-1].strip()
            return raw_text.strip() or None
    except Exception as e:
        logger.error("Erro na chamada da API Gemini: %s", str(e))
        return None


def evaluate_project_with_gemini(project: dict) -> dict:
    title = project.get("title", "")
    summary = project.get("summary", "")

    system = (
        "Você é o analista de governança de marca da Azul Linhas Aéreas.\n"
        "Sua função é avaliar projetos propostos sob a lente dos guardrails de marca.\n"
        f"{KNOWLEDGE_BASE}\n\n"
        "Com base na BASE DE CONHECIMENTO acima, avalie o projeto proposto e retorne APENAS um JSON válido dentro da tag <response> com a seguinte estrutura:\n"
        '{\n'
        '  "classificacao": "APROVADO" | "APROVAÇÃO CONDICIONAL" | "BLOQUEADO",\n'
        '  "score": 0-100,\n'
        '  "justificativa": "texto curto explicando a decisão",\n'
        '  "plano_acao": "texto curto com recomendações"\n'
        '}\n\n'
        "Regras:\n"
        "- Score >= 70: APROVADO\n"
        "- Score entre 40 e 69: APROVAÇÃO CONDICIONAL\n"
        "- Score < 40: BLOQUEADO\n"
        "- Se houver risco de conectividade ou atendimento humanizado, o score deve ser reduzido significativamente.\n"
        "- Se o projeto mencionar brasilidade ou inovação positiva, considere um bônus de até 10 pontos.\n"
        "- Seja rigoroso: projetos que repetem erros do Caso 001 (corte de conectividade sem consulta ao Marketing) devem ser BLOQUEADOS."
    )

    user_text = f"Título: {title}\nResumo: {summary}"

    result_text = _call_gemini(system, user_text)
    if result_text:
        try:
            parsed = json.loads(result_text)
            return {
                "classificacao": parsed.get("classificacao", "APROVAÇÃO CONDICIONAL"),
                "score": int(parsed.get("score", 50)),
                "justificativa": parsed.get("justificativa", ""),
                "plano_acao": parsed.get("plano_acao", ""),
            }
        except (_json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Falha ao interpretar resposta do Gemini como JSON: %.200s", result_text)
            return None
    return None


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "agent": "OmniBridge Brand Co-Pilot v1.1"}), 200


@app.route("/api/chat", methods=["POST"])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"error": "Configuração da API Key do Gemini (.env) não encontrada."}), 500

    body = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return jsonify({"error": "A mensagem não pode estar vazia."}), 400

    contents = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "model") and content:
            contents.append({
                "role": role,
                "parts": [{"text": content}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    system_instruction = (
        "Você é o OmniBridge Assist, o assistente inteligente da plataforma OmniBridge da Azul.\n"
        "Seu objetivo é ajudar os colaboradores da Azul a entenderem os guardrails de marca e alinhar/validar suas propostas de projetos.\n"
        "Use a seguinte Base de Conhecimento para fundamentar suas respostas:\n"
        f"{KNOWLEDGE_BASE}\n\n"
        "Instruções:\n"
        "- Responda em português de forma amigável, clara e concisa.\n"
        "- Seja muito direto e evite reflexões longas no seu raciocínio.\n"
        "- Se o usuário propor uma ideia de projeto, avalie-a sob a lente dos guardrails de marca e cite o Caso 001 ou outros guardrails se aplicável.\n"
        "- Você DEVE envolver estritamente a resposta final que será exibida para o usuário dentro da tag <response>...</response>."
    )

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents
    }

    model_name = "models/gemma-4-26b-a4b-it"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode())
            
            candidates = res_data.get("candidates", [])
            if not candidates:
                return jsonify({"error": "Nenhuma resposta gerada pelo modelo."}), 500
            
            parts = candidates[0].get("content", {}).get("parts", [{}])
            raw_text = "".join(p.get("text", "") for p in parts if not p.get("thought", False))
            
            match = re.search(r'<response>(.*?)</response>', raw_text, re.DOTALL | re.IGNORECASE)
            if match:
                bot_message = match.group(1).strip()
            elif "<response>" in raw_text.lower():
                parts = re.split(r'<response>', raw_text, flags=re.IGNORECASE)
                bot_message = parts[-1].strip()
            else:
                bot_message = raw_text.strip()
                
            return jsonify({"response": bot_message}), 200

    except Exception as e:
        logger.error("Erro na chamada da API Gemini: %s", str(e))
        return jsonify({"error": f"Falha na comunicação com o assistente: {str(e)}"}), 500



@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json(silent=True) or {}
    bu_name = body.get("bu_name", "").strip()
    project_idea = body.get("project_idea", "").strip()

    if not bu_name or not project_idea:
        return jsonify({"error": "Campos bu_name e project_idea são obrigatórios"}), 400

    result = analyze_with_llm(bu_name, project_idea)
    result["analisado_em"] = utc_now_iso()
    result["bu_responsavel"] = bu_name
    return jsonify(result), 200


@app.route("/api/brand-check", methods=["POST"])
def brand_check():
    return analyze()


@app.route("/api/mentor", methods=["POST"])
def mentor():
    body = request.get_json(silent=True) or {}
    bu_name = body.get("bu_name", "").strip()
    project_idea = body.get("project_idea", "").strip()

    if not bu_name or not project_idea:
        return jsonify({"error": "Campos bu_name e project_idea são obrigatórios"}), 400

    result = mentor_project(bu_name, project_idea)
    return jsonify(result), 200


@app.route("/api/analyst", methods=["POST"])
def analyst():
    body = request.get_json(silent=True) or {}
    project_id = body.get("project_id", "").strip()

    if not project_id:
        return jsonify({"error": "Campo project_id é obrigatório"}), 400

    project = next((p for p in PROJECTS if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Projeto não encontrado"}), 404

    brand_strength = calculate_brand_strength(project)
    similarity = find_similar_projects(project, PROJECTS)
    verdict = generate_verdict(project, brand_strength, similarity)

    return jsonify({
        "project_id": project_id,
        "project_title": project["title"],
        "brand_strength": brand_strength,
        "similarity": similarity,
        "verdict": verdict,
    }), 200


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    role_level = body.get("roleLevel", "Analista")
    organization = body.get("organization", "Azul Conecta")
    area = body.get("area", "Marketing")
    name = body.get("name", "Usuário demo")

    role_lower = role_level.lower().replace("vp / superintendente", "vp_superintendente")
    is_marketing_area = area.lower() == "marketing"
    high_roles = {"coordenador", "supervisor", "gerente", "diretor", "executivo", "vp_superintendente"}
    user = {
        "id": f"user-{uuid4().hex[:6]}",
        "name": name,
        "roleLevel": role_level,
        "organization": organization,
        "area": area,
        "isMarketing": is_marketing_area or role_lower in high_roles,
        "canCreate": role_lower in CREATE_ALLOWED_ROLES,
    }
    return jsonify({"user": user, "projects": PROJECTS, "users": USERS}), 200


@app.route("/api/projects", methods=["GET", "POST"])
def projects():
    if request.method == "GET":
        sort_by = request.args.get("sort", "date_desc")
        person_filter = request.args.get("person", "").strip()

        result = list(PROJECTS)

        if person_filter:
            result = [p for p in result if p.get("ownerRole", "").lower() == person_filter.lower()]

        if sort_by == "date_asc":
            result.sort(key=lambda p: p.get("createdAt", ""))
        elif sort_by == "importance_desc":
            result.sort(key=lambda p: p.get("similarityScore", 0), reverse=True)
        elif sort_by == "importance_asc":
            result.sort(key=lambda p: p.get("similarityScore", 0))
        else:
            result.sort(key=lambda p: p.get("createdAt", ""), reverse=True)

        return jsonify({"projects": result, "alerts": [p for p in PROJECTS if p.get("marketingAlert")]}), 200

    body = request.get_json(silent=True) or {}
    user_role = (body.get("userRole") or "").strip()
    normalized_role = user_role.lower().replace("vp / superintendente", "vp_superintendente")
    can_create = normalized_role in CREATE_ALLOWED_ROLES if user_role else True
    if not can_create:
        return jsonify({"error": "Seu cargo atual não possui permissão para criar novos projetos; apenas a visualização está disponível."}), 403

    title = (body.get("title") or "").strip()
    summary = (body.get("summary") or "").strip()
    organization = (body.get("organization") or "Azul Conecta").strip()
    areas = body.get("areas") or []

    if not title or not summary:
        return jsonify({"error": "Título e resumo são obrigatórios"}), 400

    new_project = {
        "id": f"proj-{uuid4().hex[:6]}",
        "title": title,
        "summary": summary,
        "org": organization,
        "areas": areas,
        "ownerRole": body.get("ownerRole", "Analista"),
        "similarityScore": 0,
        "similarityType": "Sem similaridades",
        "marketingAlert": False,
        "comments": [],
        "createdAt": utc_now_iso(),
        "references": body.get("references") or ["Projeto semelhante identificado pelo agente", "Revisar com Marketing"],
        "votes": [],
    }
    alert = calculate_project_alerts(new_project)
    similarity = find_similar_projects(new_project, PROJECTS)
    new_project["marketingAlert"] = alert["needsMarketing"] or similarity['hasSimilarProjects']
    new_project["alertReason"] = alert["reason"] if alert["needsMarketing"] else "Projeto semelhante encontrado; revisar com as áreas envolvidas."
    new_project["alertSeverity"] = alert["severity"] if alert["needsMarketing"] else "MÉDIA"
    new_project["similarityScore"] = similarity['similarityScore']
    new_project["similarityType"] = "Projeto quase idêntico" if similarity['similarityScore'] >= 70 else "Objetivos parecidos" if similarity['similarityScore'] >= 40 else "Leves similaridades" if similarity['hasSimilarProjects'] else "Sem similaridades"
    new_project["similarityMatches"] = similarity['matches']
    new_project["similarityNotifications"] = similarity['notifications']
    new_project["relatedProjects"] = [{"id": match['id'], "title": match['title'], "similarity": match['similarity']} for match in similarity['matches']]

    for match in similarity['matches']:
        existing = next((item for item in PROJECTS if item['id'] == match['id']), None)
        if existing is None:
            continue
        existing.setdefault("relatedProjects", []).append({"id": new_project['id'], "title": new_project['title'], "similarity": match['similarity']})
        existing['similarityScore'] = max(existing.get('similarityScore', 0), match['similarity'])
        existing['similarityType'] = "Projeto quase idêntico" if existing['similarityScore'] >= 70 else "Objetivos parecidos" if existing['similarityScore'] >= 40 else "Leves similaridades"
        existing['marketingAlert'] = existing.get('marketingAlert', False) or (match['similarity'] >= 50)
        existing['alertReason'] = "Projeto semelhante encontrado; revisar com as áreas envolvidas."
        existing['alertSeverity'] = "MÉDIA"
        existing.setdefault('similarityMatches', []).append({'id': new_project['id'], 'title': new_project['title'], 'similarity': match['similarity'], 'org': organization})
        existing['similarityNotifications'] = ['marketing']

    ai_eval = evaluate_project_with_gemini(new_project)
    if ai_eval:
        new_project["aiEvaluation"] = ai_eval
        new_project["aiClassificacao"] = ai_eval["classificacao"]
        new_project["aiScore"] = ai_eval["score"]
    else:
        new_project["aiEvaluation"] = None
        new_project["aiClassificacao"] = "Não avaliado"
        new_project["aiScore"] = None

    PROJECTS.insert(0, new_project)

    return jsonify({"project": new_project, "marketingAlert": alert, "similarity": similarity}), 200


@app.route("/api/projects/<project_id>/comments", methods=["POST"])
def add_comment(project_id: str):
    body = request.get_json(silent=True) or {}
    author = (body.get("author") or "Usuário").strip()
    role = (body.get("role") or "Analista").strip()
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "Texto do comentário é obrigatório"}), 400

    project = next((p for p in PROJECTS if p["id"] == project_id), None)
    if not project:
        return jsonify({"error": "Projeto não encontrado"}), 404

    comment = {"id": f"c-{uuid4().hex[:6]}", "author": author, "role": role, "text": text}
    project.setdefault("comments", []).append(comment)
    return jsonify({"comment": comment, "project": project}), 200


@app.route("/api/marketing-alerts", methods=["GET"])
def marketing_alerts():
    alerts = []
    for project in PROJECTS:
        if project.get("marketingAlert"):
            alerts.append(project)
    return jsonify({"alerts": alerts}), 200


@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/src/assets/<path:filename>")
def serve_asset(filename: str):
    return send_from_directory(os.path.join(BASE_DIR, "src", "assets"), filename)


def find_available_port(start_port: int) -> int:
    """Tenta ligar na porta `start_port`.

    Comportamento padrão: se a porta estiver em uso, aborta imediatamente com
    uma exceção para deixar explícito ao chamador que a porta requisitada
    não está disponível. Para permitir fallback automático para a próxima
    porta livre, exporte `PORT_FALLBACK=true` no ambiente.
    """
    fallback = os.environ.get("PORT_FALLBACK", "false").lower() == "true"
    port = start_port
    max_port = start_port + 1000
    while port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                if not fallback:
                    logger.error("Port %s already in use and PORT_FALLBACK not set. Aborting.", start_port)
                    raise RuntimeError(f"Port {start_port} already in use.")
                port += 1
    raise RuntimeError(f"Could not find an available port in range {start_port}-{max_port}.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    try:
        port = find_available_port(port)
    except RuntimeError as exc:
        logger.error(str(exc))
        logger.info("To allow automatic fallback to a free port, set PORT_FALLBACK=true")
        sys.exit(1)
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Iniciando servidor em http://0.0.0.0:%s (debug=%s)", port, debug)
    # Evita que o reloader do Werkzeug reinicie o processo em outra porta automaticamente.
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
