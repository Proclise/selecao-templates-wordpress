"""Funções de análise: antes x depois, gargalo, ranking e matriz de recomendação."""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import config as C
from banco import ler
from ranking import ranquear, selecionar_top


def carregar():
    proj = ler("SELECT * FROM vw_projetos_desempenho")
    for c in ["data_inicio", "data_entrega"]:
        proj[c] = pd.to_datetime(proj[c])
    ga = ler("SELECT g.*, p.nicho, p.tipo_site, p.periodo FROM fato_ga4_paginas g "
             "JOIN fato_projetos p USING (projeto_id)")
    etapas = ler("SELECT e.*, p.periodo, p.tipo_site FROM fato_etapas e JOIN fato_projetos p USING (projeto_id)")
    templates = ler("SELECT * FROM dim_templates")
    fato = ler("SELECT * FROM fato_projetos")
    return proj, ga, etapas, templates, fato


def antes_depois(proj: pd.DataFrame) -> pd.DataFrame:
    r = ler("SELECT * FROM vw_antes_depois").set_index("periodo").loc[["Antes", "Depois"]]
    var = pd.Series({
        "dias_medios_entrega": r.loc["Depois", "dias_medios_entrega"] / r.loc["Antes", "dias_medios_entrega"] - 1,
        "taxa_conversao_pct": r.loc["Depois", "taxa_conversao_pct"] / r.loc["Antes", "taxa_conversao_pct"] - 1,
        "pct_no_prazo": (r.loc["Depois", "pct_no_prazo"] - r.loc["Antes", "pct_no_prazo"]) / 100,
        "retrabalho_medio": r.loc["Depois", "retrabalho_medio"] / r.loc["Antes", "retrabalho_medio"] - 1,
    }, name="variação")
    return r, var


def testes_estatisticos(proj: pd.DataFrame, n_boot: int = 5000, seed: int = 0) -> dict:
    """Mann-Whitney para prazo e bootstrap por projeto para o lift de conversão."""
    a = proj[proj.periodo == "Antes"]
    d = proj[(proj.periodo == "Depois") & (proj.sessoes > 0)]
    _, p_dias = mannwhitneyu(a["dias_entrega"], d["dias_entrega"], alternative="greater")

    rng = np.random.default_rng(seed)
    a_s, a_c = a["sessoes"].to_numpy(), a["conversoes"].to_numpy()
    d_s, d_c = d["sessoes"].to_numpy(), d["conversoes"].to_numpy()
    lifts = []
    for _ in range(n_boot):
        ia = rng.integers(0, len(a), len(a))
        idd = rng.integers(0, len(d), len(d))
        lifts.append((d_c[idd].sum() / d_s[idd].sum()) / (a_c[ia].sum() / a_s[ia].sum()) - 1)
    lifts = np.array(lifts)
    return {
        "p_valor_prazo": p_dias,
        "lift_conversao": d_c.sum() / d_s.sum() / (a_c.sum() / a_s.sum()) - 1,
        "ic95_lift": tuple(np.percentile(lifts, [2.5, 97.5])),
        "prob_lift_positivo": (lifts > 0).mean(),
    }


def gargalo(etapas: pd.DataFrame) -> pd.DataFrame:
    """Duração média e variabilidade (coef. de variação) de cada etapa, por período."""
    e = etapas[etapas.periodo.isin(["Antes", "Depois"])]
    g = e.groupby(["etapa", "periodo"])["dias"].agg(["mean", "std"]).unstack()
    out = pd.DataFrame({
        "dias_antes": g[("mean", "Antes")], "dias_depois": g[("mean", "Depois")],
        "cv_antes": g[("std", "Antes")] / g[("mean", "Antes")],
    })
    out["reducao_dias"] = out["dias_antes"] - out["dias_depois"]
    out["pct_da_reducao_total"] = out["reducao_dias"] / out["reducao_dias"].sum()
    return out.loc[C.ETAPAS].round(3)


def ranking_antes(fato, ga, templates):
    """Ranking calculado SOMENTE com o período Antes (mesma regra usada na decisão)."""
    a = fato[fato.periodo == "Antes"]
    rank = ranquear(a, ga[ga.projeto_id.isin(a.projeto_id)], templates)
    top = selecionar_top(rank)
    rank["catalogo"] = np.where(rank.template_id.isin(top.template_id), "Sim", "Não")
    return rank, top


def matriz_recomendacao(top: pd.DataFrame) -> pd.DataFrame:
    """Template recomendado para cada nicho x tipo de site (regra do fluxo documentado)."""
    linhas = []
    for nicho in C.NICHOS:
        for tipo, (_, _, _, familia) in C.TIPOS_SITE.items():
            cat = top[top.familia == familia]
            match = cat[cat.nicho_alvo == nicho]
            esc = (match if len(match) else cat).iloc[0]
            linhas.append({"nicho": nicho, "tipo_site": tipo, "template_id": esc.template_id,
                           "nome_template": esc.nome_template, "criterio": "Nicho-alvo" if len(match) else "Maior score da família"})
    return pd.DataFrame(linhas)


# ------------------------------------------------------------- teste piloto de 30 dias --
def piloto_projetos() -> pd.DataFrame:
    return ler("SELECT * FROM vw_piloto_projetos").set_index("grupo_piloto").loc[["Controle", "Teste"]]


def piloto_ab() -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    """Resumo do A/B, teste z de duas proporções (unilateral, B > A) e série diária acumulada."""
    from scipy.stats import norm
    res = ler("SELECT * FROM vw_piloto_ab").set_index("variante")
    a, b = res.loc["A"], res.loc["B"]
    pa, pb = a.conversoes / a.sessoes, b.conversoes / b.sessoes
    pp = (a.conversoes + b.conversoes) / (a.sessoes + b.sessoes)
    ep = np.sqrt(pp * (1 - pp) * (1 / a.sessoes + 1 / b.sessoes))
    z = (pb - pa) / ep
    ep_dif = np.sqrt(pa * (1 - pa) / a.sessoes + pb * (1 - pb) / b.sessoes)
    teste = {"taxa_A": pa, "taxa_B": pb, "lift": pb / pa - 1, "z": z, "p_valor": 1 - norm.cdf(z),
             "ic95_dif_pp": ((pb - pa - 1.96 * ep_dif) * 100, (pb - pa + 1.96 * ep_dif) * 100)}
    d = ler("SELECT data, variante, SUM(sessoes) s, SUM(conversoes) c FROM fato_teste_ab_ga4 GROUP BY data, variante")
    d = d.pivot(index="data", columns="variante", values=["s", "c"])
    diario = pd.DataFrame({
        "taxa_A_dia": d[("c", "A")] / d[("s", "A")], "taxa_B_dia": d[("c", "B")] / d[("s", "B")],
        "taxa_A_acum": d[("c", "A")].cumsum() / d[("s", "A")].cumsum(),
        "taxa_B_acum": d[("c", "B")].cumsum() / d[("s", "B")].cumsum(),
    })
    diario.index = pd.to_datetime(diario.index)
    return res, teste, diario
