"""Análise de risco do texto transcrito via API OpenAI (ChatGPT)."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um analista de segurança especializado em avaliação de conteúdo
de áudio/vídeo transcrito. Avalie indícios relacionados a:
- risco de segurança e integridade física;
- ameaças, coerção ou violência;
- possível situação de crime;
- risco de vida e integridade da mulher (violência doméstica, assédio, perseguição, etc.).

Responda SOMENTE com um JSON válido (sem markdown) no formato:
{
  "nivel_risco": "baixo|medio|alto|critico",
  "pontuacao": 0-100,
  "resumo_executivo": "texto curto",
  "indicadores": ["lista de trechos ou comportamentos observados"],
  "categorias": ["seguranca", "integridade", "ameaca", "crime", "mulher", ...],
  "recomendacoes": ["ações sugeridas"],
  "justificativa": "explicação objetiva da classificação"
}"""


def analyze_transcript_risk(
    *,
    api_key: str,
    model: str,
    source_filename: str,
    transcript_text: str,
) -> dict[str, Any]:
    """Envia o texto ao ChatGPT e retorna o JSON de classificação de risco."""
    client = OpenAI(api_key=api_key)
    user_content = (
        f"Arquivo de origem: {source_filename}\n\n"
        f"Texto transcrito:\n\n{transcript_text}"
    )
    logger.info("Solicitando análise de risco via OpenAI (modelo=%s)", model)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Resposta não é JSON; encapsulando texto bruto.")
        return {
            "nivel_risco": "medio",
            "pontuacao": 50,
            "resumo_executivo": raw[:500],
            "indicadores": [],
            "categorias": ["nao_classificado"],
            "recomendacoes": ["Revisar manualmente a resposta do modelo."],
            "justificativa": raw,
        }
