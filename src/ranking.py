"""
Ranking de desempenho dos templates.

O score combina quatro indicadores, todos ajustados ao contexto do projeto para
comparar templates usados em nichos e tipos de site diferentes:

  • Lift de conversão (40%) – conversões reais ÷ conversões esperadas para o mesmo
    nicho e tipo de página (benchmark calculado no próprio histórico)
  • Tempo de entrega relativo (30%) – dias reais ÷ média do tipo de site (menor = melhor)
  • Rodadas de retrabalho (15%) – média de rodadas de aprovação de layout (menor = melhor)
  • Entrega no prazo (15%) – % de projetos entregues dentro do prazo planejado

Templates com menos de MIN_PROJETOS projetos não entram no ranking, para evitar
ranquear com base em poucos casos.
"""

import pandas as pd

PESOS = {"lift_conversao": 0.40, "tempo_relativo": 0.30, "retrabalho_medio": 0.15, "pct_no_prazo": 0.15}
MAIOR_MELHOR = {"lift_conversao": True, "tempo_relativo": False, "retrabalho_medio": False, "pct_no_prazo": True}
MIN_PROJETOS = 5
TOP_N = 10
MIN_POR_FAMILIA = 3  # regra de negócio: o catálogo precisa cobrir sites com e sem WooCommerce


def indicadores_por_template(projetos: pd.DataFrame, ga: pd.DataFrame) -> pd.DataFrame:
    """projetos: fato_projetos (com template e tipo_site); ga: fato_ga4 (com nicho e tipo_pagina)."""
    p = projetos.copy()
    p["tempo_relativo"] = p["dias_entrega"] / p.groupby("tipo_site")["dias_entrega"].transform("mean")
    p["no_prazo"] = (p["dias_entrega"] <= p["prazo_planejado_dias"]).astype(int)

    g = ga[["projeto_id", "tipo_pagina", "sessoes", "conversoes"]].merge(p[["projeto_id", "template_id", "nicho"]], on="projeto_id", how="inner")
    bench = g.groupby(["nicho", "tipo_pagina"]).agg(s=("sessoes", "sum"), c=("conversoes", "sum"))
    bench["taxa_bench"] = bench["c"] / bench["s"]
    g = g.join(bench["taxa_bench"], on=["nicho", "tipo_pagina"])
    g["conv_esperadas"] = g["sessoes"] * g["taxa_bench"]
    conv = g.groupby("template_id").agg(sessoes=("sessoes", "sum"), conversoes=("conversoes", "sum"),
                                        conv_esperadas=("conv_esperadas", "sum"))
    conv["taxa_conversao"] = conv["conversoes"] / conv["sessoes"]
    conv["lift_conversao"] = conv["conversoes"] / conv["conv_esperadas"]

    ind = p.groupby("template_id").agg(
        projetos=("projeto_id", "count"),
        dias_medios=("dias_entrega", "mean"),
        tempo_relativo=("tempo_relativo", "mean"),
        retrabalho_medio=("rodadas_retrabalho", "mean"),
        pct_no_prazo=("no_prazo", "mean"),
    ).join(conv[["sessoes", "conversoes", "taxa_conversao", "lift_conversao"]])
    return ind


def ranquear(projetos: pd.DataFrame, ga: pd.DataFrame, templates: pd.DataFrame) -> pd.DataFrame:
    ind = indicadores_por_template(projetos, ga)
    ind = ind[(ind["projetos"] >= MIN_PROJETOS) & ind["lift_conversao"].notna()].copy()
    for col, maior in MAIOR_MELHOR.items():
        x = ind[col]
        n = (x - x.min()) / (x.max() - x.min())
        ind[f"n_{col}"] = n if maior else 1 - n
    ind["score"] = sum(ind[f"n_{c}"] * w for c, w in PESOS.items()) * 100
    ind = ind.join(templates.set_index("template_id")[["nome_template", "tema_base", "page_builder",
                                                        "familia", "nicho_alvo"]])
    ind = ind.sort_values("score", ascending=False)
    ind["posicao"] = range(1, len(ind) + 1)
    return ind.reset_index()


def selecionar_top(ranking: pd.DataFrame, n: int = TOP_N, min_familia: int = MIN_POR_FAMILIA) -> pd.DataFrame:
    """Top N por score, garantindo um mínimo de templates de cada família."""
    escolhidos = []
    for fam in ranking["familia"].unique():
        escolhidos += ranking[ranking["familia"] == fam].head(min_familia)["template_id"].tolist()
    for tid in ranking["template_id"]:
        if len(escolhidos) >= n:
            break
        if tid not in escolhidos:
            escolhidos.append(tid)
    top = ranking[ranking["template_id"].isin(escolhidos)].copy()
    top["selo"] = "Catálogo padrão"
    return top.sort_values("score", ascending=False)
