"""
Extração dos dados do Google Analytics 4 via Data API (uso em produção).

Este script NÃO é executado no pipeline de demonstração, que usa dados simulados.
Ele mostra como a tabela `fato_ga4_paginas` é alimentada com dados reais.

Pré-requisitos:
    pip install google-analytics-data
    export GOOGLE_APPLICATION_CREDENTIALS="caminho/para/service-account.json"
    (a conta de serviço precisa de acesso de Leitor em cada propriedade GA4)

Uso:
    python src/extrair_ga4.py --mapa data/propriedades_ga4.csv --inicio 2025-01-01 --fim 2025-12-31

O arquivo de mapa liga cada projeto à sua propriedade GA4:
    projeto_id,property_id
    PRJ-0001,123456789
"""

import argparse
import re

import pandas as pd

TIPO_PAGINA = [
    (r"^/$", "Home"), (r"^/lp/", "Landing Page"), (r"/contato", "Contato"), (r"/servicos?", "Serviços"),
    (r"/sobre", "Sobre"), (r"/blog/.+", "Post de Blog"), (r"/produto/", "Produto"),
    (r"/(categoria|loja|shop)", "Categoria"), (r"/(checkout|finalizar)", "Checkout"), (r"/portfolio", "Portfólio"),
]


def classificar(path: str) -> str:
    for padrao, tipo in TIPO_PAGINA:
        if re.search(padrao, path):
            return tipo
    return "Outras"


def extrair(property_id: str, inicio: str, fim: str) -> pd.DataFrame:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    cliente = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="yearMonth"), Dimension(name="pagePath")],
        metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="engagedSessions"),
                 Metric(name="userEngagementDuration"), Metric(name="keyEvents")],
        date_ranges=[DateRange(start_date=inicio, end_date=fim)],
        limit=100000,
    )
    resp = cliente.run_report(req)
    linhas = [[d.value for d in r.dimension_values] + [m.value for m in r.metric_values] for r in resp.rows]
    df = pd.DataFrame(linhas, columns=["ano_mes", "page_path", "sessoes", "usuarios", "sessoes_engajadas",
                                       "duracao_engajamento_s", "conversoes"])
    num = ["sessoes", "usuarios", "sessoes_engajadas", "duracao_engajamento_s", "conversoes"]
    df[num] = df[num].apply(pd.to_numeric)
    df["mes"] = pd.to_datetime(df["ano_mes"], format="%Y%m").dt.date
    df["tipo_pagina"] = df["page_path"].map(classificar)
    df["tempo_medio_engajamento_s"] = (df["duracao_engajamento_s"] / df["usuarios"].clip(lower=1)).round(1)
    return df.drop(columns=["ano_mes", "duracao_engajamento_s"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapa", required=True)
    ap.add_argument("--inicio", required=True)
    ap.add_argument("--fim", required=True)
    ap.add_argument("--saida", default="data/raw/fato_ga4_paginas_real.csv")
    a = ap.parse_args()

    mapa = pd.read_csv(a.mapa, dtype=str)
    partes = []
    for r in mapa.itertuples():
        df = extrair(r.property_id, a.inicio, a.fim)
        df.insert(0, "projeto_id", r.projeto_id)
        partes.append(df)
        print(f"{r.projeto_id}: {len(df)} linhas")
    pd.concat(partes).to_csv(a.saida, index=False)


if __name__ == "__main__":
    main()
