"""Constantes e caminhos compartilhados pelo projeto."""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "data"
RAW = DATA / "raw"
DB = DATA / "agencia_templates.db"
SQL_DIR = RAIZ / "sql"
REPORTS = RAIZ / "reports"
FIG = REPORTS / "figures"

SEED = 13
SEED_PILOTO = 1022  # gerador separado do teste piloto

# Linha do tempo do case
INICIO_HISTORICO = pd.Timestamp("2023-01-01")
INICIO_TRANSICAO = pd.Timestamp("2025-04-01")   # análise (abr–mai) + teste piloto (jun)
PILOTO_INICIO = pd.Timestamp("2025-06-01")        # teste piloto de 30 dias
PILOTO_FIM = pd.Timestamp("2025-06-30")
INICIO_PADRONIZACAO = pd.Timestamp("2025-07-01")  # catálogo top 10 em produção (rollout)
FIM_HISTORICO = pd.Timestamp("2026-10-31")

NICHOS = {
    # nicho: (peso, fator de tráfego, fator de conversão)
    "Saúde e Clínicas": (0.16, 1.00, 1.10),
    "Advocacia": (0.10, 0.70, 1.05),
    "Restaurantes e Delivery": (0.09, 1.30, 1.15),
    "Imobiliárias": (0.10, 1.10, 0.85),
    "Educação e Cursos": (0.11, 1.20, 0.95),
    "Moda e Varejo": (0.12, 1.40, 0.90),
    "Beleza e Estética": (0.10, 1.00, 1.10),
    "Contabilidade": (0.07, 0.60, 1.00),
    "Academias e Fitness": (0.07, 0.90, 1.05),
    "Tecnologia e SaaS": (0.08, 0.80, 0.90),
}

TIPOS_SITE = {
    # tipo: (peso, dias de desenvolvimento base, prazo planejado, família de template)
    "Institucional": (0.30, 14, 38, "Geral"),
    "Landing Page": (0.22, 6, 20, "Geral"),
    "Loja Virtual (WooCommerce)": (0.16, 26, 60, "WooCommerce"),
    "Blog / Portal": (0.10, 12, 35, "Geral"),
    "Portfólio": (0.10, 10, 32, "Geral"),
    "Catálogo de Produtos": (0.12, 18, 45, "WooCommerce"),
}

PAGINAS_POR_TIPO = {
    "Institucional": ["Home", "Serviços", "Sobre", "Contato"],
    "Landing Page": ["Landing Page"],
    "Loja Virtual (WooCommerce)": ["Home", "Categoria", "Produto", "Checkout"],
    "Blog / Portal": ["Home", "Post de Blog", "Contato"],
    "Portfólio": ["Home", "Portfólio", "Contato"],
    "Catálogo de Produtos": ["Home", "Categoria", "Produto", "Contato"],
}

TIPOS_PAGINA = {
    # tipo de página: (peso de sessões, taxa base de conversão)
    "Home": (1.00, 0.0110),
    "Serviços": (0.50, 0.0240),
    "Sobre": (0.25, 0.0080),
    "Contato": (0.22, 0.0650),
    "Landing Page": (1.00, 0.0380),
    "Post de Blog": (0.90, 0.0045),
    "Portfólio": (0.55, 0.0120),
    "Categoria": (0.65, 0.0080),
    "Produto": (0.95, 0.0185),
    "Checkout": (0.07, 0.1600),
}

ETAPAS = ["Briefing", "Escolha de layout", "Design e aprovação", "Desenvolvimento",
          "Conteúdo", "QA e ajustes", "Publicação"]


def periodo(data_inicio: pd.Series) -> pd.Series:
    return pd.Series(
        pd.cut(data_inicio, bins=[pd.Timestamp("1900-01-01"), INICIO_TRANSICAO, INICIO_PADRONIZACAO,
                                  pd.Timestamp("2100-01-01")],
               labels=["Antes", "Transição", "Depois"], right=False),
        index=data_inicio.index,
    ).astype(str)
