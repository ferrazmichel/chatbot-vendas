import os
import json
from datetime import date, datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import get_table_data
from ai_agent import ask
from init_db import init_database

app = FastAPI(title="Chatbot Vendas", version="1.0.0")


@app.on_event("startup")
def startup_event():
    init_database()


class ChatRequest(BaseModel):
    pergunta: str


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def serialize(data):
    return json.loads(json.dumps(data, cls=JSONEncoder))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.pergunta or not req.pergunta.strip():
        raise HTTPException(400, "Pergunta não pode ser vazia.")
    try:
        result = await ask(req.pergunta.strip())
        return serialize(result)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar pergunta: {str(e)}")


@app.get("/api/tables/{table_name}")
async def get_table(
    table_name: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        result = get_table_data(table_name, limit, offset)
        return serialize(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/kpis")
async def get_kpis():
    return {
        "kpis": [
            {
                "nome": "Faturamento",
                "formula": "SUM(valor_total_produtos + valor_frete - valor_desconto) WHERE status = 'convertido'",
                "descricao": "Receita total dos pedidos convertidos",
            },
            {
                "nome": "Taxa de Conversão",
                "formula": "carrinhos convertidos / total carrinhos × 100",
                "descricao": "Percentual de carrinhos que viraram compra",
            },
            {
                "nome": "Quantidade de Carrinhos",
                "formula": "COUNT(DISTINCT id_carrinho)",
                "descricao": "Total de carrinhos criados",
            },
            {
                "nome": "Ticket Médio",
                "formula": "Faturamento / carrinhos convertidos",
                "descricao": "Valor médio por compra efetivada",
            },
        ],
        "exemplos_perguntas": [
            "Qual foi o faturamento de janeiro de 2026?",
            "Qual a taxa de conversão da última semana?",
            "Ranking dos 10 produtos mais vendidos em fevereiro",
            "Qual o ticket médio por estado?",
            "Quais cidades de SP tiveram mais vendas?",
            "Quantos carrinhos foram cancelados em março?",
        ],
    }


# Serve frontend estático
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
