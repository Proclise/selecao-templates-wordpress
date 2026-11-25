# 🧩 Seleção de Templates WordPress com Dados: −30% no prazo de entrega

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?logo=powerbi&logoColor=black)
![GA4](https://img.shields.io/badge/Google%20Analytics%204-E37400?logo=googleanalytics&logoColor=white)
![License](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

> Identifiquei um gargalo no prazo de entrega de sites causado pela **falta de critérios na escolha de layouts**.
> Consolidei o histórico de projetos com SQL, integrei os dados do Google Analytics (nicho, tipo de página e conversão),
> ranqueei os templates e padronizei os **10 de maior desempenho**, com um banco centralizado, dashboards no Power BI e um fluxo documentado para a equipe.

<p align="center"><img src="powerbi/previews/pagina1_visao_geral.png" width="900" alt="Dashboard Power BI: visão geral"></p>

## 🎯 Resultados

| Indicador | Antes | Depois | Variação |
|---|:-:|:-:|:-:|
| **Tempo médio de entrega** | 44,8 dias | 31,5 dias | **−30%** |
| **Taxa de conversão das páginas (GA4)** | 2,0% | 2,2% | **+10%** |
| Entregas dentro do prazo | 26% | 69% | +44 p.p. |
| Rodadas de retrabalho por projeto | 1,50 | 0,61 | −59% |

<sub>Antes: 195 projetos (jan/23–mar/25). Depois: 137 projetos (jul/25–set/26). Redução de prazo com p < 0,001 (Mann-Whitney).
Ganho de conversão com P(lift > 0) = 97%, IC 95% de −0,4% a +22,7% (bootstrap por projeto), portanto ainda em monitoramento.</sub>

---

## 📌 Problema

Uma agência que desenvolve sites em **WordPress** para 10 nichos (saúde, advocacia, restaurantes, imobiliárias, moda…)
e 6 tipos de site (institucional, landing page, loja WooCommerce, blog, portfólio, catálogo) tinha prazos longos e imprevisíveis.
Cada designer escolhia livremente entre 36 templates. Isso gerava:

- dias perdidos só para **escolher o layout** (a etapa mais variável do ciclo);
- **várias rodadas de aprovação** com o cliente;
- desenvolvimento mais lento com temas pesados (WPBakery/Divi).

## 🔍 Diagnóstico do gargalo

<p align="center"><img src="reports/figures/02_gargalo_etapas.png" width="700"></p>

As etapas *Escolha de layout* e *Design e aprovação* somavam **15,3 dias (34% do ciclo)** sem gerar nada de código.
Depois da padronização, essas duas etapas respondem por **58% da redução total** do prazo.

## 🛠️ Solução

```
Banco de projetos (SQL) ─┐
                         ├─► Banco centralizado ─► Views SQL ─► Ranking (Python) ─► Power BI ─► Fluxo da equipe
Google Analytics 4 ──────┘     (modelo estrela)                  top 10 templates    3 páginas    catálogo + matriz
```

**1. Banco centralizado:** modelo estrela com 5 dimensões e 3 fatos (`fato_projetos`, `fato_etapas`, `fato_ga4_paginas`), com chaves estrangeiras e views analíticas.

**2. Integração com o GA4:** sessões, engajamento e key events por página, classificados por **tipo de página** e ligados ao projeto, ao **nicho** e ao **tipo de site**.

**3. Ranking de desempenho:** calculado **apenas com o período Antes**, para evitar vazamento de dados:

| Critério | Peso | Como é medido |
|---|:-:|---|
| Lift de conversão | 40% | conversões reais ÷ esperadas pelo benchmark de nicho × tipo de página |
| Tempo de entrega relativo | 30% | dias ÷ média do tipo de site |
| Rodadas de retrabalho | 15% | média por projeto |
| Entrega no prazo | 15% | % dentro do prazo planejado |

Regras: mínimo de 5 projetos por template e pelo menos 3 templates de cada família (sites gerais e WooCommerce).

<p align="center">
<img src="reports/figures/06_ranking_top10.png" width="49%">
<img src="reports/figures/05_quadrante_templates.png" width="49%">
</p>

**4. Classificação por nicho × tipo de site:** uma matriz indica o template padrão para cada combinação.

<p align="center"><img src="reports/figures/07_matriz_nicho_tipo.png" width="800"></p>

**5. Dashboards no Power BI + fluxo documentado:** veja [`powerbi/`](powerbi/README.md) (modelo, DAX, Power Query, tema e layout) e [`docs/fluxo_selecao_templates.md`](docs/fluxo_selecao_templates.md) (procedimento da equipe em fluxograma).

## 📈 Resultado no tempo

<p align="center"><img src="reports/figures/01_evolucao_prazo.png" width="800"></p>
<p align="center">
<img src="reports/figures/03_distribuicao_prazo.png" width="49%">
<img src="reports/figures/04_conversao_por_pagina.png" width="49%">
</p>

## 🧰 Stack

| Etapa | Ferramentas |
|---|---|
| Banco e consultas | SQL (SQLite; compatível com PostgreSQL/MySQL): CTEs, window functions, views, chaves estrangeiras |
| Dados web | Google Analytics 4 (Data API, script em `src/extrair_ga4.py`) |
| Análise | Python: pandas, NumPy, SciPy (Mann-Whitney, bootstrap) |
| Visualização | Power BI (DAX, Power Query M, tema JSON) e Matplotlib |
| Documentação | Markdown + Mermaid |

## 📁 Estrutura

```
selecao-templates-wordpress/
├── data/
│   ├── raw/                     # 8 tabelas em CSV (dimensões + fatos)
│   └── agencia_templates.db     # banco SQLite centralizado
├── sql/
│   ├── 01_schema.sql            # modelo estrela com PK/FK
│   ├── 02_views.sql             # camada analítica
│   └── 03_consultas_analiticas.sql
├── src/
│   ├── gerar_dados.py           # simulação do histórico
│   ├── banco.py                 # cria o banco, carrega dados e roda consultas
│   ├── ranking.py               # score de desempenho + seleção do top 10
│   ├── analise.py               # gargalo, antes × depois, testes, matriz
│   ├── graficos.py · dashboard_preview.py
│   ├── extrair_ga4.py           # extração real via GA4 Data API
│   └── pipeline.py              # executa tudo
├── notebooks/analise_selecao_templates.ipynb
├── powerbi/                     # DAX, Power Query, tema, layout e prévias
├── reports/                     # rankings, catálogo, matriz, gráficos, resultados SQL
└── docs/                        # fluxo da equipe e dicionário de dados
```

## ▶️ Como executar

```bash
git clone https://github.com/Proclise/selecao-templates-wordpress.git
cd selecao-templates-wordpress
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/pipeline.py                                 # dados → banco → SQL → ranking → gráficos
jupyter notebook notebooks/analise_selecao_templates.ipynb
sqlite3 data/agencia_templates.db < sql/03_consultas_analiticas.sql
```

## 🚀 Próximos passos
- [ ] Testes A/B entre templates do catálogo para confirmar o ganho de conversão
- [ ] Incluir Core Web Vitals (LCP, CLS, INP) no score
- [ ] Revisão trimestral automática do ranking com alerta no Power BI

## ⚠️ Sobre os dados
Os dados deste repositório são **simulados** e reproduzem a estrutura e a dinâmica do case descrito acima,
preservando a confidencialidade de clientes e projetos. Nomes de clientes, templates e domínios são fictícios.

---
**Proclise** · [LinkedIn](https://www.linkedin.com/in/seu-perfil) · [GitHub](https://github.com/Proclise)
