"""
Seed Data Generator - Dados fictícios realistas de e-commerce brasileiro.
Gera ~350 pedidos com 1-5 produtos cada, de Jan a Mai 2026.
"""
import random
from datetime import date, timedelta

CLIENTES = [
    (1, "Ana Paula Silva", "São Paulo", "SP"),
    (2, "Bruno Costa Santos", "Rio de Janeiro", "RJ"),
    (3, "Carla Mendes", "Belo Horizonte", "MG"),
    (4, "Diego Oliveira", "Curitiba", "PR"),
    (5, "Elena Rodrigues", "Porto Alegre", "RS"),
    (6, "Felipe Araújo", "Salvador", "BA"),
    (7, "Gabriela Lima", "Recife", "PE"),
    (8, "Henrique Souza", "Brasília", "DF"),
    (9, "Isabela Ferreira", "Fortaleza", "CE"),
    (10, "João Pedro Alves", "Manaus", "AM"),
    (11, "Karina Nascimento", "Goiânia", "GO"),
    (12, "Lucas Barbosa", "Campinas", "SP"),
    (13, "Mariana Teixeira", "Florianópolis", "SC"),
    (14, "Nathan Carvalho", "Vitória", "ES"),
    (15, "Olivia Martins", "Belém", "PA"),
    (16, "Paulo Ricardo", "Ribeirão Preto", "SP"),
    (17, "Rafaela Dias", "Niterói", "RJ"),
    (18, "Samuel Gomes", "São Luís", "MA"),
    (19, "Tatiana Rocha", "Joinville", "SC"),
    (20, "Vinícius Pereira", "Londrina", "PR"),
    (21, "Wagner Santos", "Natal", "RN"),
    (22, "Yasmin Costa", "Campo Grande", "MS"),
    (23, "Zara Monteiro", "Cuiabá", "MT"),
    (24, "André Lopes", "João Pessoa", "PB"),
    (25, "Beatriz Cunha", "Aracaju", "SE"),
    (26, "Caio Ramos", "Sorocaba", "SP"),
    (27, "Daniela Freitas", "Uberlândia", "MG"),
    (28, "Eduardo Pinto", "Santos", "SP"),
    (29, "Fernanda Moura", "Maringá", "PR"),
    (30, "Gustavo Neves", "Maceió", "AL"),
]

PRODUTOS = [
    (101, "Smartphone Galaxy S24", 3499.90),
    (102, "Notebook Dell Inspiron 15", 4299.00),
    (103, "Fone Bluetooth JBL Tune", 249.90),
    (104, "Smart TV LG 55 4K", 2899.00),
    (105, "Teclado Mecânico Redragon", 189.90),
    (106, "Mouse Gamer Logitech G502", 299.90),
    (107, "Monitor Samsung 27 Curvo", 1599.00),
    (108, "Câmera GoPro Hero 12", 2199.00),
    (109, "Caixa de Som Portátil JBL", 449.90),
    (110, "Tablet iPad Air M2", 5499.00),
    (111, "Smartwatch Apple Watch SE", 2299.00),
    (112, "Cadeira Gamer ThunderX3", 1299.00),
    (113, "HD Externo Seagate 2TB", 399.90),
    (114, "Webcam Logitech C920", 349.90),
    (115, "Carregador Portátil 20000mAh", 129.90),
    (116, "Echo Dot Alexa 5ª Gen", 349.00),
    (117, "Roteador Wi-Fi 6 TP-Link", 279.90),
    (118, "Pen Drive Kingston 128GB", 59.90),
    (119, "Headset HyperX Cloud II", 499.90),
    (120, "SSD NVMe Samsung 1TB", 549.00),
    (121, "Impressora HP DeskJet", 699.00),
    (122, "Ring Light LED 26cm", 89.90),
    (123, "Suporte Notebook Ergonômico", 149.90),
    (124, "Controle PS5 DualSense", 399.00),
    (125, "Kit Teclado + Mouse Sem Fio", 159.90),
]


def generate_seed_sql() -> str:
    random.seed(42)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 5, 13)
    days_range = (end_date - start_date).days

    resumo_rows = []
    detalhe_rows = []

    for carrinho_id in range(1, 351):
        dia = start_date + timedelta(days=random.randint(0, days_range))
        cliente = random.choice(CLIENTES)
        r = random.random()
        if r < 0.58:
            status = "convertido"
        elif r < 0.82:
            status = "aguardando"
        else:
            status = "cancelado"

        num_itens = random.choices([1, 2, 3, 4, 5], weights=[25, 35, 25, 10, 5])[0]
        itens = random.sample(PRODUTOS, num_itens)
        valor_total = sum(p[2] for p in itens)
        frete = round(random.uniform(0, 45) + valor_total * random.uniform(0.01, 0.04), 2)
        desconto = round(valor_total * random.uniform(0, 0.15), 2) if random.random() > 0.4 else 0

        nome_escaped = cliente[1].replace("'", "''")
        cidade_escaped = cliente[2].replace("'", "''")

        resumo_rows.append(
            f"({carrinho_id}, '{dia}', '{status}', {num_itens}, {valor_total:.2f}, "
            f"{frete:.2f}, {desconto:.2f}, {cliente[0]}, '{nome_escaped}', "
            f"'{cidade_escaped}', '{cliente[3]}')"
        )

        for prod in itens:
            nome_sku_escaped = prod[1].replace("'", "''")
            detalhe_rows.append(
                f"({carrinho_id}, '{dia}', '{status}', {prod[0]}, "
                f"'{nome_sku_escaped}', {prod[2]:.2f}, {cliente[0]}, "
                f"'{nome_escaped}', '{cidade_escaped}', '{cliente[3]}')"
            )

    sql = "-- Dados gerados automaticamente\n\n"
    sql += "INSERT INTO vendas_resumo (id_carrinho, data_carrinho, status_carrinho, quantidade_produtos, valor_total_produtos, valor_frete, valor_desconto, id_cliente, nome_cliente, cidade_cliente, uf_cliente) VALUES\n"
    sql += ",\n".join(resumo_rows) + ";\n\n"

    sql += "SELECT setval('vendas_resumo_id_carrinho_seq', 351);\n\n"

    sql += "INSERT INTO vendas_detalhada (id_carrinho, data_carrinho, status_carrinho, id_sku, nome_sku, valor_sku, id_cliente, nome_cliente, cidade_cliente, uf_cliente) VALUES\n"
    sql += ",\n".join(detalhe_rows) + ";\n"

    return sql


if __name__ == "__main__":
    print(generate_seed_sql())
