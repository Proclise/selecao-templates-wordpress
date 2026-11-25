"""
Executa o projeto de ponta a ponta:
gera dados -> banco SQLite (schema + views) -> consultas SQL -> análise -> gráficos -> prévias do dashboard.

Uso:
    python src/pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analise as A  # noqa: E402
import banco  # noqa: E402
import config as C  # noqa: E402
import gerar_dados  # noqa: E402
import graficos as G  # noqa: E402


def main():
    print("1/5 Gerando base simulada")
    C.RAW.mkdir(parents=True, exist_ok=True)
    for nome, df in gerar_dados.gerar().items():
        df.to_csv(C.RAW / f"{nome}.csv", index=False, encoding="utf-8")

    print("2/5 Criando banco centralizado e views")
    banco.criar_banco()
    banco.executar_consultas()

    print("3/5 Analisando")
    proj, ga, etapas, templates, fato = A.carregar()
    resumo, var = A.antes_depois(proj)
    testes = A.testes_estatisticos(proj)
    garg = A.gargalo(etapas)
    rank, top = A.ranking_antes(fato, ga, templates)
    rec = A.matriz_recomendacao(top)

    C.REPORTS.mkdir(exist_ok=True)
    resumo.to_csv(C.REPORTS / "resumo_antes_depois.csv")
    garg.to_csv(C.REPORTS / "gargalo_etapas.csv")
    rank.round(4).to_csv(C.REPORTS / "ranking_templates.csv", index=False)
    top.round(4).to_csv(C.REPORTS / "catalogo_top10.csv", index=False)
    rec.to_csv(C.REPORTS / "matriz_recomendacao_nicho_tipo.csv", index=False)

    print("4/5 Gerando gráficos")
    G.estilo()
    G.salvar(G.evolucao_prazo(proj), "01_evolucao_prazo.png")
    G.salvar(G.gargalo_etapas(garg), "02_gargalo_etapas.png")
    G.salvar(G.distribuicao_prazo(proj), "03_distribuicao_prazo.png")
    G.salvar(G.conversao_por_pagina(ga), "04_conversao_por_pagina.png")
    G.salvar(G.quadrante_templates(rank), "05_quadrante_templates.png")
    G.salvar(G.ranking_top10(top), "06_ranking_top10.png")
    G.salvar(G.matriz_nicho_tipo(proj, rec), "07_matriz_nicho_tipo.png")

    print("5/5 Gerando prévias do dashboard Power BI")
    import dashboard_preview
    dashboard_preview.gerar(proj, ga, garg, rank, top, rec, resumo, var)

    print("\nResultado:")
    print(resumo[["projetos", "dias_medios_entrega", "pct_no_prazo", "retrabalho_medio", "taxa_conversao_pct"]])
    print(f"Redução do prazo: {-var['dias_medios_entrega']:.1%} | Lift de conversão: {var['taxa_conversao_pct']:.1%}")
    print(f"p-valor prazo (Mann-Whitney): {testes['p_valor_prazo']:.2e} | "
          f"IC95% lift conversão: {testes['ic95_lift'][0]:.1%} a {testes['ic95_lift'][1]:.1%}")


if __name__ == "__main__":
    main()
