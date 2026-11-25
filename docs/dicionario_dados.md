# 📖 Dicionário de Dados

Banco: `data/agencia_templates.db` (SQLite) · CSVs: `data/raw/` · Schema: `sql/01_schema.sql`

## Dimensões

### `dim_templates` (36 linhas)
| Coluna | Tipo | Descrição |
|---|---|---|
| `template_id` | PK texto | Código interno (`WP-01` …) |
| `nome_template` | texto | Nome interno no acervo |
| `tema_base` | texto | Tema WordPress: Astra, Kadence, GeneratePress, Blocksy, Neve, Hello Elementor, OceanWP, Divi, Avada, Flatsome |
| `page_builder` | texto | Gutenberg, Elementor, Divi Builder, WPBakery, UX Builder |
| `familia` | texto | `Geral` (sites sem loja) ou `WooCommerce` (loja/catálogo) |
| `nicho_alvo` | FK texto | Nicho para o qual o template foi desenhado |
| `data_cadastro` | data | Entrada no acervo |
| `no_catalogo_padrao` | Sim/Não | Faz parte do top 10 padronizado |

### `dim_nichos` (10) · `dim_tipos_site` (6) · `dim_clientes` (420) · `dim_calendario` (1.400)
| Tabela | Colunas principais |
|---|---|
| `dim_nichos` | `nicho`, `segmento` |
| `dim_tipos_site` | `tipo_site`, `familia_template`, `prazo_planejado_dias`, `paginas_padrao` |
| `dim_clientes` | `cliente_id`, `nome_cliente`, `nicho`, `uf`, `porte` |
| `dim_calendario` | `data`, `ano`, `mes_num`, `ano_mes`, `trimestre`, `periodo` |

**Nichos:** Saúde e Clínicas, Advocacia, Restaurantes e Delivery, Imobiliárias, Educação e Cursos, Moda e Varejo, Beleza e Estética, Contabilidade, Academias e Fitness, Tecnologia e SaaS.
**Tipos de site:** Institucional, Landing Page, Loja Virtual (WooCommerce), Blog / Portal, Portfólio, Catálogo de Produtos.

## Fatos

### `fato_projetos` (362 linhas, 1 por projeto)
| Coluna | Tipo | Descrição |
|---|---|---|
| `projeto_id` | PK | `PRJ-0001` … |
| `cliente_id`, `nicho`, `tipo_site`, `template_id` | FK | Chaves para as dimensões |
| `data_inicio`, `data_entrega` | data | Início do briefing e publicação do site |
| `prazo_planejado_dias` | int | Prazo-padrão do tipo de site |
| `dias_entrega` | int | Dias corridos do início à entrega (soma das etapas) |
| `rodadas_retrabalho` | int | Rodadas extras de aprovação de layout |
| `horas_desenvolvimento` | real | Horas registradas na etapa de desenvolvimento |
| `valor_projeto_brl` | real | Valor do contrato |
| `url_site` | texto | Domínio publicado (fictício) |
| `periodo` | texto | `Antes` (< abr/25), `Transição` (abr–jun/25), `Depois` (≥ jul/25), pela data de início |

### `fato_etapas` (2.534 linhas, 7 por projeto)
`etapa_id`, `projeto_id`, `ordem_etapa`, `etapa` (Briefing → Escolha de layout → Design e aprovação → Desenvolvimento → Conteúdo → QA e ajustes → Publicação), `dias`.

### `fato_ga4_paginas` (6.182 linhas, projeto × mês × página)
Até 6 meses após a publicação, no formato da GA4 Data API.
| Coluna | Métrica GA4 equivalente |
|---|---|
| `mes` | `yearMonth` |
| `page_path`, `tipo_pagina` | `pagePath` + classificação por regex (`src/extrair_ga4.py`) |
| `sessoes` | `sessions` |
| `usuarios` | `totalUsers` |
| `sessoes_engajadas` | `engagedSessions` |
| `tempo_medio_engajamento_s` | `userEngagementDuration ÷ totalUsers` |
| `conversoes` | `keyEvents` (lead, clique no WhatsApp, compra) |

## Views
| View | Uso |
|---|---|
| `vw_projetos_desempenho` | Projeto + template + GA4 consolidado (base do Power BI) |
| `vw_antes_depois` | KPIs por período |
| `vw_etapas_periodo` | Duração e % do ciclo por etapa |
| `vw_benchmark_conversao` | Taxa de referência por nicho × tipo de página (período Antes) |

## Saídas do modelo (`reports/`)
| Arquivo | Conteúdo |
|---|---|
| `ranking_templates.csv` | Indicadores e score dos templates com pelo menos 5 projetos |
| `catalogo_top10.csv` | Os 10 templates padronizados |
| `matriz_recomendacao_nicho_tipo.csv` | Template indicado para cada nicho × tipo de site |
| `resumo_antes_depois.csv`, `gargalo_etapas.csv` | Resultados |
| `sql/q1…q8.csv` | Resultado das consultas analíticas |
