-- ============================================
-- CHATBOT VENDAS - Schema e Dados
-- ============================================

-- Tabela Resumo de Vendas (por carrinho)
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

-- Tabela Detalhada de Vendas (por produto/SKU)
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

-- Índices para performance
CREATE INDEX idx_resumo_data ON vendas_resumo(data_carrinho);
CREATE INDEX idx_resumo_status ON vendas_resumo(status_carrinho);
CREATE INDEX idx_resumo_uf ON vendas_resumo(uf_cliente);
CREATE INDEX idx_resumo_cliente ON vendas_resumo(id_cliente);
CREATE INDEX idx_detalhada_carrinho ON vendas_detalhada(id_carrinho);
CREATE INDEX idx_detalhada_data ON vendas_detalhada(data_carrinho);
CREATE INDEX idx_detalhada_sku ON vendas_detalhada(id_sku);
CREATE INDEX idx_detalhada_status ON vendas_detalhada(status_carrinho);
