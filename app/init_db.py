"""
Inicializa o banco de dados: cria tabelas e popula com dados seed se necessário.
Usado para deploy no Render onde o PostgreSQL é um serviço separado.
"""
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vendas:vendas123@postgres:5432/chatbot_vendas")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS vendas_resumo (
    id_carrinho SERIAL PRIMARY KEY,
    data_carrinho DATE NOT NULL,
    status_carrinho VARCHAR(20) NOT NULL CHECK (status_carrinho IN ('convertido', 'aguardando', 'cancelado')),
    valor_total_produtos DECIMAL(12,2) NOT NULL,
    valor_frete DECIMAL(10,2) NOT NULL DEFAULT 0,
    valor_desconto DECIMAL(10,2) NOT NULL DEFAULT 0,
    id_cliente INTEGER NOT NULL,
    nome_cliente VARCHAR(100) NOT NULL,
    cidade_cliente VARCHAR(80) NOT NULL,
    uf_cliente VARCHAR(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS vendas_detalhada (
    id SERIAL PRIMARY KEY,
    id_carrinho INTEGER NOT NULL REFERENCES vendas_resumo(id_carrinho),
    data_carrinho DATE NOT NULL,
    status_carrinho VARCHAR(20) NOT NULL CHECK (status_carrinho IN ('convertido', 'aguardando', 'cancelado')),
    id_sku INTEGER NOT NULL,
    nome_sku VARCHAR(150) NOT NULL,
    valor_sku DECIMAL(10,2) NOT NULL,
    id_cliente INTEGER NOT NULL,
    nome_cliente VARCHAR(100) NOT NULL,
    cidade_cliente VARCHAR(80) NOT NULL,
    uf_cliente VARCHAR(2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_resumo_data ON vendas_resumo(data_carrinho);
CREATE INDEX IF NOT EXISTS idx_resumo_status ON vendas_resumo(status_carrinho);
CREATE INDEX IF NOT EXISTS idx_resumo_uf ON vendas_resumo(uf_cliente);
CREATE INDEX IF NOT EXISTS idx_resumo_cliente ON vendas_resumo(id_cliente);
CREATE INDEX IF NOT EXISTS idx_detalhada_carrinho ON vendas_detalhada(id_carrinho);
CREATE INDEX IF NOT EXISTS idx_detalhada_data ON vendas_detalhada(data_carrinho);
CREATE INDEX IF NOT EXISTS idx_detalhada_sku ON vendas_detalhada(id_sku);
CREATE INDEX IF NOT EXISTS idx_detalhada_status ON vendas_detalhada(status_carrinho);
"""


def init_database():
    """Cria tabelas e popula com dados seed se o banco estiver vazio."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            # Cria as tabelas
            cur.execute(SCHEMA_SQL)
            conn.commit()

            # Verifica se já tem dados
            cur.execute("SELECT COUNT(*) FROM vendas_resumo")
            count = cur.fetchone()[0]

            if count == 0:
                print("Banco vazio — populando com dados seed...")
                from seed_data import generate_seed_sql
                seed_sql = generate_seed_sql()
                cur.execute(seed_sql)
                conn.commit()
                print("Dados seed inseridos com sucesso!")
            else:
                print(f"Banco já possui {count} registros. Pulando seed.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
