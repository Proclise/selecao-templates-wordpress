"""Gráficos do projeto. Cada função aceita um `ax` para reuso nas prévias do dashboard."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

import config as C

AZUL = "#2a78d6"
LARANJA = "#eb6834"
CINZA = "#b4b3ad"
TEXTO = "#2b2b29"
TEXTO_2 = "#6b6b66"
GRADE = "#e6e5e0"
SEQ = LinearSegmentedColormap.from_list("seq", ["#eef4fc", "#9cc2ef", "#2a78d6", "#123f75"])


def estilo():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 10.5,
        "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_2, "axes.titlecolor": TEXTO,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 26, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.8,
        "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False,
    })


def _sub(ax, txt):
    ax.text(0, 1.015, txt, transform=ax.transAxes, color=TEXTO_2, fontsize=9.5, va="bottom")


def _novo(ax, figsize):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax, True
    return ax.figure, ax, False


def salvar(fig, nome):
    C.FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIG / nome, facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------------------------
def gargalo_etapas(garg: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8.5, 4.6))
    y = np.arange(len(garg))[::-1]
    h = 0.36
    ax.barh(y + h / 2, garg["dias_antes"], h, color=CINZA, label="Antes (sem critério)")
    ax.barh(y - h / 2, garg["dias_depois"], h, color=AZUL, label="Depois (catálogo top 10)")
    for yi, (a, d) in zip(y, zip(garg["dias_antes"], garg["dias_depois"])):
        ax.text(a + 0.2, yi + h / 2, f"{a:.1f}", va="center", fontsize=8.5, color=TEXTO_2)
        ax.text(d + 0.2, yi - h / 2, f"{d:.1f}", va="center", fontsize=8.5, color=TEXTO)
    ax.set_yticks(y, garg.index)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Dias médios na etapa")
    ax.legend(loc="lower right", fontsize=9)
    if titulo:
        ax.set_title("Onde o prazo era perdido: duração média por etapa")
        _sub(ax, "Escolha de layout, aprovação e desenvolvimento concentram a redução")
    return fig


def evolucao_prazo(proj: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (9, 4.2))
    m = proj.set_index("data_entrega").resample("MS")["dias_entrega"].mean()
    mm = m.rolling(3, min_periods=2).mean()
    ax.axvspan(C.INICIO_TRANSICAO, C.INICIO_PADRONIZACAO, color="#f2f1ed", lw=0)
    ax.plot(m.index, m.values, color=CINZA, lw=1.2, marker="o", ms=3, label="Média mensal")
    ax.plot(mm.index, mm.values, color=AZUL, lw=2.2, label="Média móvel 3 meses")
    for per, cor in [("Antes", TEXTO_2), ("Depois", TEXTO)]:
        sub = proj[proj.periodo == per]
        val = sub["dias_entrega"].mean()
        ini, fim = sub["data_entrega"].min(), sub["data_entrega"].max()
        ax.hlines(val, ini, fim, color=LARANJA, lw=1.5, ls="--")
        ax.text(fim, val - 2.2, f"{per}: {val:.1f} dias", ha="right", va="top", color=cor, fontsize=9.5,
                fontweight="bold", bbox=dict(fc="white", ec="none", pad=1.5))
    ax.text(C.INICIO_TRANSICAO + pd.Timedelta(days=45), 22,
            "Análise +\npiloto 30d", ha="center", fontsize=8.5, color=TEXTO_2)
    ax.set_ylim(20, max(62, m.max() + 4))
    ax.set_ylabel("Dias até a entrega")
    ax.legend(loc="upper right", fontsize=9, ncols=2, bbox_to_anchor=(1, 1.0))
    if titulo:
        ax.set_title("Tempo médio de entrega dos projetos")
        _sub(ax, "Mês da entrega; faixa cinza = análise (abr–mai/25) + teste piloto de 30 dias (jun/25)")
    return fig


def conversao_por_pagina(ga: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8.5, 4.6))
    g = ga[ga.periodo.isin(["Antes", "Depois"])].groupby(["tipo_pagina", "periodo"])[["conversoes", "sessoes"]].sum()
    t = (g["conversoes"] / g["sessoes"] * 100).unstack()
    t = t.drop(index="Checkout").sort_values("Antes")
    y = np.arange(len(t))
    ax.hlines(y, t["Antes"], t["Depois"], color=GRADE, lw=3)
    ax.scatter(t["Antes"], y, s=60, color=CINZA, zorder=3, label="Antes", edgecolor="white", lw=1.5)
    ax.scatter(t["Depois"], y, s=60, color=AZUL, zorder=3, label="Depois", edgecolor="white", lw=1.5)
    for yi, (a, d) in enumerate(zip(t["Antes"], t["Depois"])):
        ax.text(max(a, d) + 0.12, yi, f"{a:.2f}% → {d:.2f}%", va="center", fontsize=8.5, color=TEXTO)
    ax.set_yticks(y, t.index)
    ax.set_xlim(0, t.values.max() * 1.35)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Taxa de conversão (%)")
    ax.legend(loc="lower right", fontsize=9)
    if titulo:
        ax.set_title("Conversão por tipo de página (GA4)")
        _sub(ax, "Key events ÷ sessões; checkout omitido por ter escala própria (~17%)")
    return fig


def ranking_top10(top: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8.8, 4.8))
    t = top.iloc[::-1]
    cores = [AZUL if f == "Geral" else LARANJA for f in t["familia"]]
    rot = [f"{r.template_id}  {r.nome_template}" for r in t.itertuples()]
    ax.barh(rot, t["score"], color=cores, height=0.62)
    for yi, r in enumerate(t.itertuples()):
        ax.text(r.score + 1, yi, f"{r.score:.0f}  ·  conversão {r.lift_conversao:.2f}x  ·  prazo {r.tempo_relativo:.2f}x",
                va="center", fontsize=8.5, color=TEXTO)
    ax.set_xlim(0, 178)
    ax.set_xticks(range(0, 101, 25))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Score de desempenho (0–100)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="Sites gerais"), Patch(color=LARANJA, label="WooCommerce")],
              loc="lower right", fontsize=9)
    if titulo:
        ax.set_title("Catálogo padrão: os 10 templates de maior desempenho")
        _sub(ax, "Score = conversão 40% + prazo 30% + retrabalho 15% + no prazo 15%  ·  1,00x = média (jan/23–mar/25)")
    return fig


def quadrante_templates(rank: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8, 5))
    out = rank[rank.catalogo == "Não"]
    cat = rank[rank.catalogo == "Sim"]
    ax.scatter(out["tempo_relativo"], out["lift_conversao"], s=out["projetos"] * 9, color=CINZA,
               alpha=0.8, edgecolor="white", lw=1, label="Demais templates")
    ax.scatter(cat["tempo_relativo"], cat["lift_conversao"], s=cat["projetos"] * 9, color=AZUL,
               edgecolor="white", lw=1, label="Catálogo top 10")
    for r in cat.itertuples():
        ax.annotate(r.template_id, (r.tempo_relativo, r.lift_conversao), xytext=(6, 4),
                    textcoords="offset points", fontsize=8, color=TEXTO)
    ax.axvline(1, color=TEXTO_2, lw=0.8, ls=":")
    ax.axhline(1, color=TEXTO_2, lw=0.8, ls=":")
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.text(xl[0] + 0.01, yl[1] - 0.01, "Rápido e converte mais", va="top", fontsize=9, color=AZUL, fontweight="bold")
    ax.text(xl[1] - 0.01, yl[0] + 0.01, "Lento e converte menos", ha="right", fontsize=9, color=TEXTO_2)
    ax.set_xlabel("Tempo de entrega relativo (1 = média do tipo de site)")
    ax.set_ylabel("Lift de conversão (1 = benchmark do nicho)")
    ax.legend(loc="center right", fontsize=9, markerscale=0.6)
    if titulo:
        ax.set_title("Templates: prazo × conversão")
        _sub(ax, "Tamanho do ponto = nº de projetos no período Antes")
    return fig


def matriz_nicho_tipo(proj: pd.DataFrame, rec: pd.DataFrame, ax=None, titulo=True):
    """Cor = taxa de conversão histórica do nicho x tipo; texto = template recomendado."""
    fig, ax, novo = _novo(ax, (10.5, 5.6))
    g = proj.groupby(["nicho", "tipo_site"])[["conversoes", "sessoes"]].sum()
    taxa = (g["conversoes"] / g["sessoes"] * 100).unstack()
    cont = proj.pivot_table(index="nicho", columns="tipo_site", values="projeto_id", aggfunc="count")
    cols = list(C.TIPOS_SITE)
    taxa = taxa.where(cont >= 2).reindex(columns=cols)
    r = rec.pivot(index="nicho", columns="tipo_site", values="template_id").reindex(index=taxa.index, columns=cols)
    im = ax.imshow(taxa, cmap=SEQ, aspect="auto")
    ax.set_xticks(range(len(cols)), [c.replace(" (WooCommerce)", "\n(WooCommerce)").replace(" de ", "\nde ")
                                     for c in cols], fontsize=8.5)
    ax.set_yticks(range(len(taxa)), taxa.index, fontsize=9)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    vmin, vmax = np.nanmin(taxa.values), np.nanmax(taxa.values)
    lim = vmin + 0.55 * (vmax - vmin)
    for i in range(taxa.shape[0]):
        for j in range(taxa.shape[1]):
            v = taxa.iat[i, j]
            cor = TEXTO if np.isnan(v) or v <= lim else "white"
            ax.text(j, i - 0.13, r.iat[i, j], ha="center", va="center", fontsize=8.5, fontweight="bold", color=cor)
            ax.text(j, i + 0.2, "sem base" if np.isnan(v) else f"{v:.2f}%", ha="center", va="center",
                    fontsize=7.5, color=cor)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Taxa de conversão histórica (%)")
    if titulo:
        ax.set_title("Matriz de recomendação: template padrão por nicho × tipo de site")
        _sub(ax, "Negrito = template do catálogo indicado; cor = conversão média da combinação (GA4, todo o histórico)")
    return fig


def distribuicao_prazo(proj: pd.DataFrame, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8, 4))
    bins = np.arange(10, 95, 5)
    larg = 2.1
    for k, (per, cor) in enumerate([("Antes", CINZA), ("Depois", AZUL)]):
        d = proj.loc[proj.periodo == per, "dias_entrega"]
        cont, _ = np.histogram(d, bins=bins)
        ax.bar(bins[:-1] + 2.5 + (k - 0.5) * larg, cont, width=larg - 0.2, color=cor, label=f"{per} (n={len(d)})")
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("Dias até a entrega")
    ax.set_ylabel("Projetos")
    ax.legend(fontsize=9)
    if titulo:
        ax.set_title("Distribuição do prazo de entrega")
        _sub(ax, "Prazos ficaram menores e mais previsíveis")
    return fig


def piloto_ab_acumulado(diario: pd.DataFrame, teste: dict, ax=None, titulo=True):
    fig, ax, novo = _novo(ax, (8.5, 4.2))
    ax.plot(diario.index, diario["taxa_A_acum"] * 100, color=CINZA, lw=2.2, label="A: layout atual")
    ax.plot(diario.index, diario["taxa_B_acum"] * 100, color=AZUL, lw=2.2, label="B: template do catálogo")
    for col, cor, nome in [("taxa_A_acum", TEXTO_2, "A"), ("taxa_B_acum", TEXTO, "B")]:
        v = diario[col].iloc[-1] * 100
        ax.text(diario.index[-1] + pd.Timedelta(days=0.6), v, f"{nome}: {v:.2f}%", va="center", fontsize=9.5,
                color=cor, fontweight="bold")
    ax.set_xlim(diario.index[0], diario.index[-1] + pd.Timedelta(days=4.5))
    ax.set_ylim(1.5, 2.8)
    ax.set_xticks(diario.index[::4])
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%d/%m"))
    ax.set_ylabel("Conversão acumulada (%)")
    ax.legend(loc="upper right", fontsize=9, ncols=2)
    if titulo:
        ax.set_title("Teste piloto de 30 dias: A/B de conversão no GA4")
        _sub(ax, f"12 sites, 01–30/jun/2025 · lift {teste['lift']:+.1%} · p-valor {teste['p_valor']:.3f} (teste z unilateral)")
    return fig
