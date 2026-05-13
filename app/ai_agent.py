"""
AI Agent - Converte perguntas em linguagem natural para SQL e retorna respostas.
Usa Azure OpenAI com dicionário de KPIs no system prompt.
"""
import os
import json
import httpx
from database import execute_query

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt4o-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

SYSTEM_PROMPT = """Você é um analista de dados especialista em e-commerce brasileiro.
O usuário fará perguntas de negócio sobre vendas e você deve gerar queries SQL PostgreSQL.

=== TABELAS DISPONÍVEIS ===

1) vendas_resumo (visão por carrinho):
   - id_carrinho (integer, PK)
   - data_carrinho (date) — data do pedido
   - status_carrinho (varchar) — valores: 'convertido', 'aguardando', 'cancelado'
   - valor_total_produtos (decimal) — soma dos produtos do carrinho
   - valor_frete (decimal)
   - valor_desconto (decimal)
   - id_cliente (integer)
   - nome_cliente (varchar)
   - cidade_cliente (varchar)
   - uf_cliente (varchar, 2 chars) — sigla do estado (SP, RJ, MG, etc.)

2) vendas_detalhada (visão por produto/SKU):
   - id (integer, PK)
   - id_carrinho (integer, FK → vendas_resumo)
   - data_carrinho (date)
   - status_carrinho (varchar)
   - id_sku (integer)
   - nome_sku (varchar) — nome do produto
   - valor_sku (decimal) — preço do produto
   - id_cliente (integer)
   - nome_cliente (varchar)
   - cidade_cliente (varchar)
   - uf_cliente (varchar, 2 chars)

=== DICIONÁRIO DE KPIs ===

• FATURAMENTO = SUM(valor_total_produtos + valor_frete - valor_desconto) WHERE status_carrinho = 'convertido'
  Obs: Faturamento SEMPRE filtra apenas carrinhos convertidos.

• TAXA DE CONVERSÃO = COUNT(DISTINCT id_carrinho WHERE status_carrinho = 'convertido') / COUNT(DISTINCT id_carrinho) * 100
  Resultado em percentual.

• QUANTIDADE DE CARRINHOS = COUNT(DISTINCT id_carrinho)
  Pode ser filtrado por status ou total.

• TICKET MÉDIO = FATURAMENTO / COUNT(DISTINCT id_carrinho WHERE status_carrinho = 'convertido')
  Apenas carrinhos convertidos no divisor.

• RANKING DE PRODUTOS = Use vendas_detalhada, agrupe por nome_sku, conte ou some valor_sku.
  "Mais vendidos" = maior quantidade de ocorrências (COUNT).
  "Maior receita" = maior soma de valor_sku.

=== REGRAS ===
1. Retorne APENAS a query SQL. Sem explicações, sem markdown, sem blocos de código.
2. Use PostgreSQL syntax.
3. Limite resultados a 50 linhas (LIMIT 50).
4. Para datas relativas (semana passada, mês passado, etc.), considere a data atual como CURRENT_DATE.
5. Quando o usuário mencionar um estado, use a sigla (uf_cliente). Ex: "São Paulo" → 'SP'.
6. Quando filtrar por mês, use EXTRACT(MONTH FROM data_carrinho) e EXTRACT(YEAR FROM data_carrinho).
7. Sempre use DISTINCT em id_carrinho quando contar carrinhos para evitar duplicatas.
8. Para perguntas sobre produtos, use a tabela vendas_detalhada.
9. Para perguntas sobre faturamento, ticket médio, taxa de conversão, use a tabela vendas_resumo.
10. Apenas queries SELECT são permitidas."""

SUMMARY_PROMPT = """Você é um analista de dados que explica resultados de forma clara em português brasileiro.
O usuário fez uma pergunta de negócio e o banco de dados retornou dados.
Resuma os resultados de forma clara, amigável e direta.
Use formatação com números formatados em pt-BR (ex: R$ 1.234,56 / 45,2%).
Se for uma tabela/ranking, formate de forma legível.
Seja conciso mas completo."""


async def generate_sql(pergunta: str) -> str:
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    payload = {
        "temperature": 0,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pergunta},
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    sql = data["choices"][0]["message"]["content"].strip()
    sql = sql.removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
    return sql


def validate_sql(sql: str) -> None:
    upper = sql.upper().strip()
    if not upper.startswith("SELECT"):
        raise ValueError("Apenas consultas SELECT são permitidas.")
    blocked = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
    for kw in blocked:
        if f" {kw} " in f" {upper} " or upper.startswith(kw):
            raise ValueError(f"Operação {kw} não permitida.")


async def summarize_results(pergunta: str, dados: list[dict], sql: str) -> str:
    dados_str = json.dumps(dados[:30], ensure_ascii=False, default=str)
    url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    payload = {
        "temperature": 0.3,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": SUMMARY_PROMPT},
            {
                "role": "user",
                "content": f"Pergunta do usuário: {pergunta}\n\nSQL executado: {sql}\n\nResultados:\n{dados_str}",
            },
        ],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json=payload,
            headers={"api-key": AZURE_OPENAI_KEY, "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


async def ask(pergunta: str) -> dict:
    sql = await generate_sql(pergunta)
    validate_sql(sql)
    dados = execute_query(sql)
    resumo = await summarize_results(pergunta, dados, sql)
    return {
        "resposta": resumo,
        "sql_gerado": sql,
        "dados": dados[:50],
        "total_linhas": len(dados),
    }
