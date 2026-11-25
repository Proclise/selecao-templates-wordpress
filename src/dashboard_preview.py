"""
Prévias (PNG) das 3 páginas do dashboard Power BI, no mesmo layout descrito em
powerbi/README.md. Servem para o README do GitHub e para o post do LinkedIn,
já que o arquivo .pbix é montado no Power BI Desktop.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import config as C
import graficos as G

NAVY = "#14213d"
FUNDO = "#f4f5f7"
PAGINAS = ["Visão geral", "Ranking de templates", "Nicho × tipo de site"]
SAIDA = C.RAIZ / "powerbi" / "previews"


def _pagina(idx: int):
    fig = plt.figure(figsize=(16, 9), facecolor=FUNDO)
    top = fig.add_axes([0, 0.92, 1, 0.08])
    top.set_facecolor(NAVY)
    top.set_xticks([]); top.set_yticks([])
    for s in top.spines.values():
        s.set_visible(False)
    top.grid(False)
    top.text(0.015, 0.5, "Seleção de Templates WordPress  |  Desempenho de Projetos", color="white",
             fontsize=15, fontweight="bold", va="center", transform=top.transAxes)
    x = 0.50
    for i, nome in enumerate(PAGINAS):
        ativo = i == idx
        top.text(x, 0.5, nome, color="white" if ativo else "#9aa3b5", fontsize=11, va="center",
                 fontweight="bold" if ativo else "normal", transform=top.transAxes)
        if ativo:
            top.plot([x, x + len(nome) * 0.0058], [0.12, 0.12], color=G.LARANJA, lw=3, transform=top.transAxes)
        x += len(nome) * 0.0062 + 0.035
    # segmentações (slicers)
    for i, (rot, val) in enumerate([("Período", "Todos"), ("Nicho", "Todos"), ("Tipo de site", "Todos"),
                                    ("Template", "Todos")]):
        x0 = 0.015 + i * 0.12
        fig.patches.append(FancyBboxPatch((x0, 0.862), 0.11, 0.042, boxstyle="round,pad=0.003,rounding_size=0.006",
                                          transform=fig.transFigure, fc="white", ec="#d9dbe0", lw=1, zorder=-5))
        fig.text(x0 + 0.007, 0.889, rot, fontsize=7.5, color=G.TEXTO_2, transform=fig.transFigure)
        fig.text(x0 + 0.007, 0.870, f"{val}  ▾", fontsize=9, color=G.TEXTO, transform=fig.transFigure)
    fig.text(0.985, 0.875, "Fonte: banco SQL da agência + Google Analytics 4  ·  dados simulados",
             ha="right", fontsize=8, color=G.TEXTO_2)
    return fig


def _cartao(fig, ret, titulo, antes, depois, variacao, bom=True):
    x, y, w, h = ret
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.002,rounding_size=0.008",
                                      transform=fig.transFigure, fc="white", ec="#e1e3e8", lw=1, zorder=-5))
    fig.text(x + 0.012, y + h - 0.03, titulo, fontsize=10, color=G.TEXTO_2)
    fig.text(x + 0.012, y + 0.035, depois, fontsize=26, fontweight="bold", color=G.TEXTO)
    fig.text(x + w - 0.012, y + 0.075, variacao, ha="right", fontsize=12, fontweight="bold",
             color=G.AZUL if bom else G.LARANJA)
    fig.text(x + w - 0.012, y + 0.035, f"antes: {antes}", ha="right", fontsize=9, color=G.TEXTO_2)


def _painel(fig, ret, esq=0.04):
    x, y, w, h = ret
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.002,rounding_size=0.008",
                                      transform=fig.transFigure, fc="white", ec="#e1e3e8", lw=1, zorder=-5))
    return fig.add_axes([x + esq, y + 0.065, w - esq - 0.02, h - 0.15])


def gerar(proj, ga, garg, rank, top, rec, resumo, var):
    SAIDA.mkdir(parents=True, exist_ok=True)
    G.estilo()
    plt.rcParams["axes.titlepad"] = 20
    a, d = resumo.loc["Antes"], resumo.loc["Depois"]

    # ---------------- Página 1
    fig = _pagina(0)
    cards = [
        ("Tempo médio de entrega", f"{a.dias_medios_entrega:.1f} dias", f"{d.dias_medios_entrega:.1f} dias",
         f"▼ {-var['dias_medios_entrega']:.0%}"),
        ("Taxa de conversão (GA4)", f"{a.taxa_conversao_pct:.2f}%", f"{d.taxa_conversao_pct:.2f}%",
         f"▲ {var['taxa_conversao_pct']:.0%}"),
        ("Entregas no prazo", f"{a.pct_no_prazo:.0f}%", f"{d.pct_no_prazo:.0f}%",
         f"▲ {var['pct_no_prazo'] * 100:.0f} p.p."),
        ("Rodadas de retrabalho / projeto", f"{a.retrabalho_medio:.2f}", f"{d.retrabalho_medio:.2f}",
         f"▼ {-var['retrabalho_medio']:.0%}"),
    ]
    for i, c in enumerate(cards):
        _cartao(fig, (0.015 + i * 0.245, 0.70, 0.235, 0.14), *c)
    ax = _painel(fig, (0.015, 0.03, 0.55, 0.65), esq=0.045)
    G.evolucao_prazo(proj, ax=ax, titulo=False)
    ax.set_title("Tempo médio de entrega (dias)")
    ax2 = _painel(fig, (0.58, 0.03, 0.405, 0.65), esq=0.115)
    G.gargalo_etapas(garg, ax=ax2, titulo=False)
    ax2.set_title("Dias por etapa: antes × depois")
    ax2.legend(loc="lower right", fontsize=8)
    fig.savefig(SAIDA / "pagina1_visao_geral.png", dpi=110, facecolor=FUNDO)
    plt.close(fig)

    # ---------------- Página 2
    fig = _pagina(1)
    cards = [
        ("Templates avaliados", "", f"{len(rank)}", "≥ 5 projetos · 36 no acervo"),
        ("Templates no catálogo padrão", "", f"{len(top)}", f"{(top.familia == 'WooCommerce').sum()} WooCommerce"),
        ("Lift médio de conversão (top 10)", "", f"{top.lift_conversao.mean():.2f}x",
         f"demais: {rank[rank.catalogo == 'Não'].lift_conversao.mean():.2f}x"),
        ("Prazo relativo médio (top 10)", "", f"{top.tempo_relativo.mean():.2f}",
         f"demais: {rank[rank.catalogo == 'Não'].tempo_relativo.mean():.2f}"),
    ]
    for i, (t, _, v, extra) in enumerate(cards):
        x = 0.015 + i * 0.245
        fig.patches.append(FancyBboxPatch((x, 0.70), 0.235, 0.14, boxstyle="round,pad=0.002,rounding_size=0.008",
                                          transform=fig.transFigure, fc="white", ec="#e1e3e8", lw=1, zorder=-5))
        fig.text(x + 0.012, 0.81, t, fontsize=10, color=G.TEXTO_2)
        fig.text(x + 0.012, 0.735, v, fontsize=26, fontweight="bold", color=G.TEXTO)
        fig.text(x + 0.223, 0.74, extra, ha="right", fontsize=9.5, color=G.TEXTO_2)
    ax = _painel(fig, (0.015, 0.03, 0.56, 0.65), esq=0.235)
    G.ranking_top10(top, ax=ax, titulo=False)
    ax.get_legend().remove()
    ax.set_title("Top 10: score de desempenho   (azul = sites gerais · laranja = WooCommerce)", fontsize=12)
    ax2 = _painel(fig, (0.585, 0.03, 0.40, 0.65), esq=0.05)
    G.quadrante_templates(rank, ax=ax2, titulo=False)
    ax2.set_title("Prazo relativo × lift de conversão")
    fig.savefig(SAIDA / "pagina2_ranking_templates.png", dpi=110, facecolor=FUNDO)
    plt.close(fig)

    # ---------------- Página 3
    fig = _pagina(2)
    ax = _painel(fig, (0.015, 0.03, 0.60, 0.81), esq=0.11)
    G.matriz_nicho_tipo(proj, rec, ax=ax, titulo=False)
    ax.set_title("Template recomendado por nicho × tipo de site")
    ax2 = _painel(fig, (0.63, 0.03, 0.355, 0.81), esq=0.08)
    G.conversao_por_pagina(ga, ax=ax2, titulo=False)
    ax2.set_title("Conversão por tipo de página")
    fig.savefig(SAIDA / "pagina3_nicho_tipo.png", dpi=110, facecolor=FUNDO)
    plt.close(fig)
