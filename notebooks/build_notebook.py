"""Monta o notebook (notebooks/analise_selecao_templates.ipynb). Executar depois com nbconvert."""
from pathlib import Path

import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb = nbf.v4.new_notebook()
nb.cells = [
    md("""# 🧩 Seleção de Templates WordPress: análise do gargalo de prazo

**Problema:** os sites da agência atrasavam, e a escolha do layout não seguia nenhum critério. Cada designer escolhia o template
que preferia entre 36 opções, o que gerava várias rodadas de aprovação e retrabalho no desenvolvimento.

**Objetivo:** usar o histórico de projetos (banco SQL) e o Google Analytics 4 para:
1. confirmar onde está o gargalo do prazo;
2. medir o desempenho de cada template por **nicho**, **tipo de site** e **tipo de página**;
3. ranquear os templates e escolher os **10 de maior desempenho**;
4. validar a proposta em um **teste piloto de 30 dias**, apresentado à gestão em um dashboard Excel;
5. medir o resultado depois da padronização (rollout).

| Período | Datas | O que aconteceu |
|---|---|---|
| Antes | jan/2023 a mar/2025 | escolha livre do layout |
| Transição | abr a mai/2025 | consolidação dos dados, diagnóstico e ranking |
| ↳ Teste piloto | 01 a 30/jun/2025 | A/B em 12 sites + 13 projetos Teste × Controle → dashboard Excel |
| Depois | jul/2025 a out/2026 | catálogo top 10 + fluxo documentado |

> ⚠️ Os dados são **simulados**, mas seguem a estrutura real de um banco de projetos e da exportação do GA4."""),
    code("""import sys, sqlite3
from pathlib import Path
import pandas as pd, numpy as np
from IPython.display import Image, display

RAIZ = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(RAIZ / "src"))
import config as C, banco, analise as A, graficos as G
from ranking import PESOS

pd.set_option("display.width", 160); pd.set_option("display.max_columns", 20)
G.estilo()
proj, ga, etapas, templates, fato = A.carregar()
print(f"{len(proj)} projetos | {len(ga):,} linhas de GA4 | {len(templates)} templates | {proj.nicho.nunique()} nichos | {proj.tipo_site.nunique()} tipos de site")"""),
    md("## 1. Banco de dados centralizado\nModelo estrela com 5 dimensões e 3 fatos. As views em `sql/02_views.sql` integram projetos e GA4."),
    code("""banco.ler("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")"""),
    code("""banco.ler("SELECT * FROM vw_projetos_desempenho LIMIT 5")"""),
    md("## 2. Diagnóstico: onde está o gargalo?"),
    code("""garg = A.gargalo(etapas)
garg"""),
    code("""G.gargalo_etapas(garg);"""),
    md("""**Leitura (período Antes):**
- *Escolha de layout* e *Design e aprovação* somavam **15,3 dias**, cerca de 34% do ciclo, sem gerar nada de código.
- A escolha de layout tinha a **maior variabilidade** de todas as etapas (coeficiente de variação na tabela), o que tornava o prazo imprevisível.
- O desenvolvimento também variava conforme o template: temas pesados (Avada/WPBakery, Divi) levavam mais tempo e geravam mais retrabalho."""),
    code("""cs = banco.consultas()
pd.read_sql_query(cs["Q3. Variabilidade do prazo por template no período ANTES (o sintoma)"], sqlite3.connect(C.DB))"""),
    md("## 3. Integração com o GA4: conversão por nicho e tipo de página\nComo cada nicho e cada tipo de página tem uma taxa natural diferente, a comparação justa entre templates usa um **benchmark** (`vw_benchmark_conversao`)."),
    code("""banco.ler("SELECT * FROM vw_benchmark_conversao ORDER BY nicho, taxa_benchmark DESC").head(12)"""),
    md("## 4. Ranking dos templates (somente dados do período Antes)\nCalcular o ranking só com o período anterior evita *vazamento de dados*: a decisão foi tomada com a informação que existia na época."),
    code("""pd.Series(PESOS, name="peso").to_frame()"""),
    code("""rank, top = A.ranking_antes(fato, ga, templates)
cols = ["posicao", "template_id", "nome_template", "page_builder", "familia", "projetos",
        "lift_conversao", "tempo_relativo", "retrabalho_medio", "pct_no_prazo", "score"]
rank[cols].round(2).head(15)"""),
    code("""G.ranking_top10(top);"""),
    code("""G.quadrante_templates(rank);"""),
    md("""**Regra de negócio:** o catálogo precisa ter pelo menos 3 templates de cada família (sites gerais e WooCommerce).
Por isso o WP-27 entrou mesmo com conversão abaixo da média: ele é o WooCommerce mais rápido e com menos retrabalho."""),
    md("## 5. Classificação por nicho × tipo de site\nO resultado prático para a equipe é uma matriz que indica qual template usar em cada projeto."),
    code("""rec = A.matriz_recomendacao(top)
rec.pivot(index="nicho", columns="tipo_site", values="template_id")"""),
    code("""G.matriz_nicho_tipo(proj, rec);"""),
    md("""## 6. Teste piloto de 30 dias (01 a 30/jun/2025)
Antes de mudar o processo de toda a equipe, a proposta foi testada por 30 dias em duas frentes:
- **Teste A/B de conversão:** 12 sites publicados, com as páginas principais em duas versões (A = layout atual, B = template do catálogo) e tráfego 50/50, medido no GA4.
- **Projetos Teste × Controle:** projetos iniciados no mês, alternados entre escolha livre (Controle) e catálogo + fluxo (Teste).

O resultado foi apresentado no dashboard `excel/dashboard_teste_piloto_30_dias.xlsx`."""),
    code("""ab_res, ab_teste, ab_diario = A.piloto_ab()
display(ab_res)
print(f"Conversão A = {ab_teste['taxa_A']:.2%} | B = {ab_teste['taxa_B']:.2%} | lift = {ab_teste['lift']:+.1%}")
print(f"z = {ab_teste['z']:.2f} | p-valor = {ab_teste['p_valor']:.3f} | IC 95% da diferença = "
      f"[{ab_teste['ic95_dif_pp'][0]:+.2f}, {ab_teste['ic95_dif_pp'][1]:+.2f}] p.p.")"""),
    code("""G.piloto_ab_acumulado(ab_diario, ab_teste);"""),
    code("""A.piloto_projetos()"""),
    code("""display(Image(filename=str(RAIZ / "excel/preview_dashboard_excel.png"), width=900))"""),
    md("""**Leitura:** o A/B mostrou conversão **11% maior** com o template do catálogo, com significância estatística (p ≈ 0,01).
No grupo Teste, a escolha de layout caiu de 9,4 para 1,8 dia e o prazo total caiu 32%. Com apenas 13 projetos, esse efeito no prazo foi tratado
como **indicativo**. **Decisão da gestão:** aprovar o rollout em 01/07/2025 e acompanhar no Power BI."""),
    md("## 7. Resultado do rollout: antes × depois"),
    code("""resumo, var = A.antes_depois(proj)
display(resumo)
var.map("{:+.1%}".format).to_frame()"""),
    code("""G.evolucao_prazo(proj);"""),
    code("""G.distribuicao_prazo(proj);"""),
    code("""G.conversao_por_pagina(ga);"""),
    md("### Teste estatístico\nPrazo: Mann-Whitney (unilateral). Conversão: *bootstrap* por projeto, já que as sessões de um mesmo site não são independentes."),
    code("""t = A.testes_estatisticos(proj)
print(f"Prazo  -> p-valor = {t['p_valor_prazo']:.1e}")
print(f"Conversão -> lift = {t['lift_conversao']:+.1%} | IC 95% = [{t['ic95_lift'][0]:+.1%}, {t['ic95_lift'][1]:+.1%}] | P(lift > 0) = {t['prob_lift_positivo']:.0%}")"""),
    md("""**Leitura honesta:**
- A redução do prazo é **robusta**: p-valor perto de zero, e a distribuição inteira se deslocou para prazos menores.
- O ganho de conversão (+10%, de 2,0% para 2,2%) é **provável, mas ainda incerto**: o intervalo de confiança encosta no zero.
  O A/B controlado do piloto (p ≈ 0,01) reforça que o efeito é real. A recomendação é continuar acompanhando no Power BI."""),
    md("""## 8. Conclusões

| Indicador | Antes | Depois | Variação |
|---|---|---|---|
| Tempo médio de entrega | 44,8 dias | 31,5 dias | **−30%** |
| Taxa de conversão (GA4) | 2,01% | 2,22% | **+10%** |
| Entregas no prazo | 26% | 69% | +44 p.p. |
| Rodadas de retrabalho | 1,50 | 0,61 | −59% |

1. O gargalo estava na **escolha do layout e no ciclo de aprovação**, não no desenvolvimento em si.
2. Templates leves (Gutenberg/Elementor) com nicho-alvo definido entregam mais rápido e convertem mais.
3. O teste piloto de 30 dias (A/B + Teste × Controle) validou a proposta antes do rollout, e o resultado foi apresentado em dashboard Excel.
4. Um catálogo de 10 templates com matriz nicho × tipo eliminou a escolha subjetiva e reduziu o retrabalho.
5. Próximos passos: revisão trimestral do ranking, novos A/B entre templates do catálogo e inclusão de Core Web Vitals no score."""),
]
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
saida = Path(__file__).resolve().parent / "analise_selecao_templates.ipynb"
nbf.write(nb, saida)
print(saida)
