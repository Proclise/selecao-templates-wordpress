-- =============================================================================
-- Views analíticas: camada consumida pelo Power BI e pelo notebook
-- =============================================================================

-- Projeto + GA4 consolidado (1 linha por projeto)
DROP VIEW IF EXISTS vw_projetos_desempenho;
CREATE VIEW vw_projetos_desempenho AS
SELECT p.projeto_id, p.periodo, p.nicho, p.tipo_site, p.template_id,
       t.nome_template, t.tema_base, t.page_builder, t.no_catalogo_padrao,
       p.data_inicio, p.data_entrega, p.dias_entrega, p.prazo_planejado_dias,
       CASE WHEN p.dias_entrega <= p.prazo_planejado_dias THEN 1 ELSE 0 END AS no_prazo,
       p.rodadas_retrabalho,
       COALESCE(SUM(g.sessoes), 0)     AS sessoes,
       COALESCE(SUM(g.conversoes), 0)  AS conversoes,
       ROUND(1.0 * SUM(g.conversoes) / NULLIF(SUM(g.sessoes), 0), 5) AS taxa_conversao
FROM fato_projetos p
JOIN dim_templates t ON t.template_id = p.template_id
LEFT JOIN fato_ga4_paginas g ON g.projeto_id = p.projeto_id
GROUP BY p.projeto_id;

-- Antes x Depois da padronização
DROP VIEW IF EXISTS vw_antes_depois;
CREATE VIEW vw_antes_depois AS
SELECT periodo,
       COUNT(*)                                        AS projetos,
       ROUND(AVG(dias_entrega), 1)                     AS dias_medios_entrega,
       ROUND(100.0 * AVG(no_prazo), 1)                 AS pct_no_prazo,
       ROUND(AVG(rodadas_retrabalho), 2)               AS retrabalho_medio,
       SUM(sessoes)                                    AS sessoes,
       SUM(conversoes)                                 AS conversoes,
       ROUND(100.0 * SUM(conversoes) / SUM(sessoes), 2) AS taxa_conversao_pct
FROM vw_projetos_desempenho
GROUP BY periodo;

-- Duração média por etapa e período (diagnóstico do gargalo)
DROP VIEW IF EXISTS vw_etapas_periodo;
CREATE VIEW vw_etapas_periodo AS
SELECT p.periodo, e.ordem_etapa, e.etapa,
       ROUND(AVG(e.dias), 1) AS dias_medios,
       ROUND(100.0 * SUM(e.dias) / SUM(SUM(e.dias)) OVER (PARTITION BY p.periodo), 1) AS pct_do_ciclo
FROM fato_etapas e
JOIN fato_projetos p ON p.projeto_id = e.projeto_id
GROUP BY p.periodo, e.ordem_etapa, e.etapa;

-- Conversão por nicho x tipo de página (benchmark usado no ranking)
DROP VIEW IF EXISTS vw_benchmark_conversao;
CREATE VIEW vw_benchmark_conversao AS
SELECT p.nicho, g.tipo_pagina,
       SUM(g.sessoes) AS sessoes, SUM(g.conversoes) AS conversoes,
       ROUND(1.0 * SUM(g.conversoes) / SUM(g.sessoes), 5) AS taxa_benchmark
FROM fato_ga4_paginas g
JOIN fato_projetos p ON p.projeto_id = g.projeto_id
WHERE p.periodo = 'Antes'
GROUP BY p.nicho, g.tipo_pagina;

-- Teste piloto de 30 dias: projetos (Teste x Controle)
DROP VIEW IF EXISTS vw_piloto_projetos;
CREATE VIEW vw_piloto_projetos AS
SELECT p.grupo_piloto,
       COUNT(DISTINCT p.projeto_id)               AS projetos,
       ROUND(AVG(p.dias_entrega), 1)              AS dias_medios_entrega,
       ROUND(AVG(p.rodadas_retrabalho), 2)        AS retrabalho_medio,
       ROUND(AVG(CASE WHEN e.etapa = 'Escolha de layout' THEN e.dias END), 1) AS dias_escolha_layout,
       ROUND(AVG(CASE WHEN e.etapa = 'Design e aprovação' THEN e.dias END), 1) AS dias_design_aprovacao
FROM fato_projetos p
JOIN fato_etapas e ON e.projeto_id = p.projeto_id
WHERE p.grupo_piloto IS NOT NULL
GROUP BY p.grupo_piloto;

-- Teste piloto de 30 dias: A/B de conversão (GA4)
DROP VIEW IF EXISTS vw_piloto_ab;
CREATE VIEW vw_piloto_ab AS
SELECT variante, descricao_variante,
       COUNT(DISTINCT projeto_id) AS sites,
       COUNT(DISTINCT data)       AS dias,
       SUM(sessoes)               AS sessoes,
       SUM(conversoes)            AS conversoes,
       ROUND(100.0 * SUM(conversoes) / SUM(sessoes), 3) AS taxa_conversao_pct,
       ROUND(100.0 * SUM(sessoes_engajadas) / SUM(sessoes), 1) AS taxa_engajamento_pct
FROM fato_teste_ab_ga4
GROUP BY variante, descricao_variante;
