-- =============================================================================
-- Consultas analíticas
-- Rodar: sqlite3 data/agencia_templates.db < sql/03_consultas_analiticas.sql
-- =============================================================================

-- Q1. Resultado da padronização: antes x depois
SELECT * FROM vw_antes_depois ORDER BY CASE periodo WHEN 'Antes' THEN 1 WHEN 'Transição' THEN 2 ELSE 3 END;

-- Q2. Onde está o gargalo? Etapas do ciclo antes x depois
SELECT a.etapa,
       a.dias_medios AS dias_antes,
       d.dias_medios AS dias_depois,
       ROUND(d.dias_medios - a.dias_medios, 1) AS variacao_dias,
       a.pct_do_ciclo AS pct_ciclo_antes
FROM vw_etapas_periodo a
JOIN vw_etapas_periodo d ON d.etapa = a.etapa AND d.periodo = 'Depois'
WHERE a.periodo = 'Antes'
ORDER BY a.ordem_etapa;

-- Q3. Variabilidade do prazo por template no período ANTES (o sintoma)
SELECT template_id, nome_template, page_builder,
       COUNT(*) AS projetos,
       ROUND(AVG(dias_entrega), 1) AS dias_medios,
       MIN(dias_entrega) AS min_dias, MAX(dias_entrega) AS max_dias,
       ROUND(AVG(rodadas_retrabalho), 2) AS retrabalho_medio
FROM vw_projetos_desempenho
WHERE periodo = 'Antes'
GROUP BY template_id
HAVING COUNT(*) >= 5
ORDER BY dias_medios DESC
LIMIT 10;

-- Q4. Lift de conversão por template vs. benchmark de nicho e tipo de página (período ANTES)
WITH ga AS (
    SELECT p.template_id, g.sessoes, g.conversoes, b.taxa_benchmark
    FROM fato_ga4_paginas g
    JOIN fato_projetos p ON p.projeto_id = g.projeto_id
    JOIN vw_benchmark_conversao b ON b.nicho = p.nicho AND b.tipo_pagina = g.tipo_pagina
    WHERE p.periodo = 'Antes'
)
SELECT t.template_id, t.nome_template,
       SUM(ga.sessoes) AS sessoes,
       ROUND(100.0 * SUM(ga.conversoes) / SUM(ga.sessoes), 2) AS taxa_conv_pct,
       ROUND(SUM(ga.conversoes) / SUM(ga.sessoes * ga.taxa_benchmark), 3) AS lift_conversao
FROM ga JOIN dim_templates t ON t.template_id = ga.template_id
GROUP BY t.template_id
ORDER BY lift_conversao DESC
LIMIT 10;

-- Q5. Catálogo padrão: os 10 templates selecionados e o uso deles após a padronização
SELECT t.template_id, t.nome_template, t.tema_base, t.page_builder, t.familia, t.nicho_alvo,
       SUM(CASE WHEN v.periodo = 'Depois' THEN 1 ELSE 0 END) AS projetos_depois,
       ROUND(AVG(CASE WHEN v.periodo = 'Depois' THEN v.dias_entrega END), 1) AS dias_medios_depois
FROM dim_templates t
LEFT JOIN vw_projetos_desempenho v ON v.template_id = t.template_id
WHERE t.no_catalogo_padrao = 'Sim'
GROUP BY t.template_id
ORDER BY projetos_depois DESC;

-- Q6. Classificação por nicho x tipo de site: volume, prazo e conversão (antes x depois)
SELECT nicho, tipo_site,
       SUM(CASE WHEN periodo = 'Antes'  THEN 1 ELSE 0 END) AS projetos_antes,
       SUM(CASE WHEN periodo = 'Depois' THEN 1 ELSE 0 END) AS projetos_depois,
       ROUND(AVG(CASE WHEN periodo = 'Antes'  THEN dias_entrega END), 1) AS dias_antes,
       ROUND(AVG(CASE WHEN periodo = 'Depois' THEN dias_entrega END), 1) AS dias_depois,
       ROUND(100.0 * SUM(CASE WHEN periodo = 'Antes'  THEN conversoes END)
                   / NULLIF(SUM(CASE WHEN periodo = 'Antes'  THEN sessoes END), 0), 2) AS conv_antes_pct,
       ROUND(100.0 * SUM(CASE WHEN periodo = 'Depois' THEN conversoes END)
                   / NULLIF(SUM(CASE WHEN periodo = 'Depois' THEN sessoes END), 0), 2) AS conv_depois_pct
FROM vw_projetos_desempenho
GROUP BY nicho, tipo_site
ORDER BY nicho, tipo_site;

-- Q7. Evolução mensal: tempo médio de entrega (média móvel de 3 meses)
WITH mensal AS (
    SELECT strftime('%Y-%m', data_entrega) AS mes, AVG(dias_entrega) AS dias, COUNT(*) AS n
    FROM fato_projetos GROUP BY mes
)
SELECT mes, n, ROUND(dias, 1) AS dias_medios,
       ROUND(AVG(dias) OVER (ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS media_movel_3m
FROM mensal ORDER BY mes;

-- Q8. Conversão por tipo de página antes x depois
SELECT g.tipo_pagina,
       ROUND(100.0 * SUM(CASE WHEN p.periodo='Antes'  THEN g.conversoes END) / SUM(CASE WHEN p.periodo='Antes'  THEN g.sessoes END), 2) AS conv_antes_pct,
       ROUND(100.0 * SUM(CASE WHEN p.periodo='Depois' THEN g.conversoes END) / SUM(CASE WHEN p.periodo='Depois' THEN g.sessoes END), 2) AS conv_depois_pct
FROM fato_ga4_paginas g JOIN fato_projetos p ON p.projeto_id = g.projeto_id
GROUP BY g.tipo_pagina
ORDER BY conv_antes_pct DESC;
