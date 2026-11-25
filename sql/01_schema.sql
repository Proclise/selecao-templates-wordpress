-- =============================================================================
-- Banco centralizado da agência: modelo estrela (SQLite)
-- Compatível com PostgreSQL / SQL Server com pequenos ajustes de tipo
-- =============================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fato_ga4_paginas;
DROP TABLE IF EXISTS fato_etapas;
DROP TABLE IF EXISTS fato_projetos;
DROP TABLE IF EXISTS dim_clientes;
DROP TABLE IF EXISTS dim_templates;
DROP TABLE IF EXISTS dim_nichos;
DROP TABLE IF EXISTS dim_tipos_site;
DROP TABLE IF EXISTS dim_calendario;

-- ---------------------------------------------------------------- dimensões --
CREATE TABLE dim_nichos (
    nicho              TEXT PRIMARY KEY,
    segmento           TEXT NOT NULL
);

CREATE TABLE dim_tipos_site (
    tipo_site             TEXT PRIMARY KEY,
    familia_template      TEXT NOT NULL CHECK (familia_template IN ('Geral', 'WooCommerce')),
    prazo_planejado_dias  INTEGER NOT NULL,
    paginas_padrao        TEXT
);

CREATE TABLE dim_templates (
    template_id         TEXT PRIMARY KEY,
    nome_template       TEXT NOT NULL,
    tema_base           TEXT NOT NULL,          -- Astra, Kadence, Divi, Flatsome...
    page_builder        TEXT NOT NULL,          -- Elementor, Gutenberg, WPBakery...
    familia             TEXT NOT NULL,
    nicho_alvo          TEXT REFERENCES dim_nichos(nicho),
    data_cadastro       DATE,
    no_catalogo_padrao  TEXT CHECK (no_catalogo_padrao IN ('Sim', 'Não'))
);

CREATE TABLE dim_clientes (
    cliente_id     TEXT PRIMARY KEY,
    nome_cliente   TEXT NOT NULL,
    nicho          TEXT NOT NULL REFERENCES dim_nichos(nicho),
    uf             TEXT,
    porte          TEXT
);

CREATE TABLE dim_calendario (
    data        DATE PRIMARY KEY,
    ano         INTEGER,
    mes_num     INTEGER,
    ano_mes     TEXT,
    trimestre   TEXT,
    periodo     TEXT
);

-- ------------------------------------------------------------------- fatos --
CREATE TABLE fato_projetos (
    projeto_id             TEXT PRIMARY KEY,
    cliente_id             TEXT NOT NULL REFERENCES dim_clientes(cliente_id),
    nicho                  TEXT NOT NULL REFERENCES dim_nichos(nicho),
    tipo_site              TEXT NOT NULL REFERENCES dim_tipos_site(tipo_site),
    template_id            TEXT NOT NULL REFERENCES dim_templates(template_id),
    data_inicio            DATE NOT NULL,
    data_entrega           DATE NOT NULL,
    prazo_planejado_dias   INTEGER NOT NULL,
    dias_entrega           INTEGER NOT NULL CHECK (dias_entrega > 0),
    rodadas_retrabalho     INTEGER NOT NULL DEFAULT 0,
    horas_desenvolvimento  REAL,
    valor_projeto_brl      REAL,
    url_site               TEXT,
    periodo                TEXT NOT NULL CHECK (periodo IN ('Antes', 'Transição', 'Depois'))
);

CREATE TABLE fato_etapas (
    etapa_id      INTEGER PRIMARY KEY,
    projeto_id    TEXT NOT NULL REFERENCES fato_projetos(projeto_id),
    ordem_etapa   INTEGER NOT NULL,
    etapa         TEXT NOT NULL,
    dias          INTEGER NOT NULL
);

-- Exportação mensal do Google Analytics 4 (Data API / BigQuery), agregada por página
CREATE TABLE fato_ga4_paginas (
    ga_id                      INTEGER PRIMARY KEY,
    projeto_id                 TEXT NOT NULL REFERENCES fato_projetos(projeto_id),
    mes                        DATE NOT NULL,
    page_path                  TEXT NOT NULL,
    tipo_pagina                TEXT NOT NULL,
    sessoes                    INTEGER NOT NULL,
    usuarios                   INTEGER,
    sessoes_engajadas          INTEGER,
    tempo_medio_engajamento_s  REAL,
    conversoes                 INTEGER NOT NULL      -- key events (lead, WhatsApp, compra)
);

CREATE INDEX ix_proj_template ON fato_projetos(template_id);
CREATE INDEX ix_proj_periodo  ON fato_projetos(periodo);
CREATE INDEX ix_etapas_proj   ON fato_etapas(projeto_id);
CREATE INDEX ix_ga_proj       ON fato_ga4_paginas(projeto_id);
