// =============================================================================
// Power Query (M): conexão com o banco SQLite via ODBC, ou com os CSVs
// Página Inicial > Transformar dados > Nova fonte > Consulta nula > Editor avançado
// =============================================================================

// ---- Parâmetro: pasta do projeto (crie como parâmetro do tipo Texto) ----
// PastaProjeto = "C:\projetos\selecao-templates-wordpress\"

// ---- Opção A: ODBC (driver SQLite ODBC: http://www.ch-werner.de/sqliteodbc/) ----
let
    Fonte = Odbc.DataSource(
        "Driver={SQLite3 ODBC Driver};Database=" & PastaProjeto & "data\agencia_templates.db",
        [HierarchicalNavigation = true]
    ),
    vw_projetos = Fonte{[Name = "vw_projetos_desempenho", Kind = "View"]}[Data]
in
    vw_projetos

// ---- Opção B: CSV (uma consulta por tabela). Exemplo: fato_projetos ----
let
    Fonte = Csv.Document(
        File.Contents(PastaProjeto & "data\raw\fato_projetos.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos, {
        {"data_inicio", type date}, {"data_entrega", type date},
        {"prazo_planejado_dias", Int64.Type}, {"dias_entrega", Int64.Type},
        {"rodadas_retrabalho", Int64.Type}, {"horas_desenvolvimento", type number},
        {"valor_projeto_brl", Currency.Type}
    }, "en-US"),
    NoPrazo = Table.AddColumn(Tipos, "no_prazo",
        each if [dias_entrega] <= [prazo_planejado_dias] then 1 else 0, Int64.Type),
    OrdemPeriodo = Table.AddColumn(NoPrazo, "ordem_periodo",
        each if [periodo] = "Antes" then 1 else if [periodo] = "Transição" then 2 else 3, Int64.Type)
in
    OrdemPeriodo

// ---- fato_ga4_paginas ----
let
    Fonte = Csv.Document(File.Contents(PastaProjeto & "data\raw\fato_ga4_paginas.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos, {
        {"mes", type date}, {"sessoes", Int64.Type}, {"usuarios", Int64.Type},
        {"sessoes_engajadas", Int64.Type}, {"tempo_medio_engajamento_s", type number},
        {"conversoes", Int64.Type}
    }, "en-US")
in
    Tipos

// ---- ranking_templates (resultado do modelo Python) ----
let
    Fonte = Csv.Document(File.Contents(PastaProjeto & "reports\ranking_templates.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
    Tipos = Table.TransformColumnTypes(Cabecalhos, {
        {"score", type number}, {"lift_conversao", type number}, {"tempo_relativo", type number},
        {"retrabalho_medio", type number}, {"pct_no_prazo", Percentage.Type},
        {"projetos", Int64.Type}, {"posicao", Int64.Type}
    }, "en-US")
in
    Tipos
