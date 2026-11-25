"""
Dashboard em Excel do TESTE PILOTO DE 30 DIAS (01 a 30/jun/2025).

Esta foi a planilha apresentada à gestão para demonstrar o resultado do teste antes
de aprovar a padronização (rollout em jul/2025). Todos os indicadores são FÓRMULAS sobre
as abas de dados, então a planilha recalcula se os dados forem atualizados.

Saída: excel/dashboard_teste_piloto_30_dias.xlsx

Uso:
    python src/dashboard_excel.py
"""

import sqlite3

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.comments import Comment
from openpyxl.drawing.line import LineProperties
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import config as C

SAIDA = C.RAIZ / "excel" / "dashboard_teste_piloto_30_dias.xlsx"

AZUL, CINZA, NAVY = "2A78D6", "B4B3AD", "14213D"
F = "Arial"
f_txt = Font(name=F, size=10, color="2B2B29")
f_sub = Font(name=F, size=9, color="6B6B66")
f_bold = Font(name=F, size=10, bold=True, color="2B2B29")
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
f_input = Font(name=F, size=10, color="0000FF")
f_link = Font(name=F, size=10, color="008000")
fill_head = PatternFill("solid", fgColor=NAVY)
fill_card = PatternFill("solid", fgColor="FFFFFF")
fill_bg = PatternFill("solid", fgColor="F4F5F7")
fill_input = PatternFill("solid", fgColor="FFFF00")
borda = Border(*(Side(style="thin", color="E1E3E8"),) * 4)
PCT2, PCT1, NUM1 = "0.00%", "0.0%", "0.0"


def _dados():
    con = sqlite3.connect(C.DB)
    ab = pd.read_sql_query("SELECT * FROM fato_teste_ab_ga4 ORDER BY data, projeto_id, variante", con)
    proj = pd.read_sql_query(
        "SELECT projeto_id, grupo_piloto, nicho, tipo_site, template_id, data_inicio, prazo_planejado_dias, "
        "rodadas_retrabalho FROM fato_projetos WHERE grupo_piloto IS NOT NULL ORDER BY data_inicio", con)
    et = pd.read_sql_query("SELECT projeto_id, etapa, dias FROM fato_etapas", con)
    sites = pd.read_sql_query(
        "SELECT a.projeto_id, p.nicho, p.tipo_site, "
        "MAX(CASE WHEN variante='A' THEN a.template_id END) tpl_a, "
        "MAX(CASE WHEN variante='B' THEN a.template_id END) tpl_b "
        "FROM fato_teste_ab_ga4 a JOIN fato_projetos p USING (projeto_id) GROUP BY a.projeto_id", con)
    con.close()
    piv = et.pivot(index="projeto_id", columns="etapa", values="dias")[C.ETAPAS]
    proj = proj.join(piv, on="projeto_id")
    for col in ["data_inicio"]:
        proj[col] = pd.to_datetime(proj[col])
    ab["data"] = pd.to_datetime(ab["data"])
    return ab, proj, sites


def _cab(ws, linha, titulos, larguras=None):
    for j, t in enumerate(titulos, 1):
        c = ws.cell(linha, j, t)
        c.font, c.fill = f_head, fill_head
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if larguras:
        for j, w in enumerate(larguras, 1):
            ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = ws.cell(linha + 1, 1)


def _estilo_tabela(ws, l1, l2, c1, c2):
    for r in ws.iter_rows(min_row=l1, max_row=l2, min_col=c1, max_col=c2):
        for c in r:
            if c.font != f_input:
                c.font = f_txt if not c.font.bold else c.font
            c.border = borda


def _chart_base(ch, titulo, y_titulo=None):
    ch.title = titulo
    ch.roundedCorners = False
    ch.legend.position = "b"
    ch.legend.overlay = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    if y_titulo:
        ch.y_axis.title = y_titulo
    ch.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E6E5E0"))
    return ch


def construir():
    ab, proj, sites = _dados()
    wb = Workbook()

    # ============================================================ Dados_AB
    wsd = wb.active
    wsd.title = "Dados_AB"
    cols = ["teste_id", "data", "projeto_id", "variante", "descricao_variante", "template_id",
            "sessoes", "sessoes_engajadas", "conversoes"]
    _cab(wsd, 1, cols, [9, 12, 12, 9, 22, 12, 10, 16, 11])
    for i, r in enumerate(ab[cols].itertuples(index=False), 2):
        for j, v in enumerate(r, 1):
            c = wsd.cell(i, j, v.to_pydatetime() if isinstance(v, pd.Timestamp) else v)
            c.font = f_txt
            if j == 2:
                c.number_format = "dd/mm/yyyy"
    n_ab = len(ab) + 1
    wsd.auto_filter.ref = f"A1:I{n_ab}"
    rng = lambda col: f"Dados_AB!${col}$2:${col}${n_ab}"  # noqa: E731

    # ============================================================ Projetos_Piloto
    wsp = wb.create_sheet("Projetos_Piloto")
    cab = ["projeto_id", "grupo", "nicho", "tipo_site", "template_id", "data_inicio"] + C.ETAPAS + \
          ["Total (dias)", "Prazo planejado", "No prazo (1/0)", "Rodadas de retrabalho"]
    _cab(wsp, 1, cab, [11, 10, 22, 24, 11, 11, 9, 10, 11, 12, 9, 10, 10, 11, 11, 10, 12])
    for i, (_, r) in enumerate(proj.iterrows(), 2):
        vals = [r.projeto_id, r.grupo_piloto, r.nicho, r.tipo_site, r.template_id, r.data_inicio.to_pydatetime()]
        vals += [int(r[e]) for e in C.ETAPAS]
        for j, v in enumerate(vals, 1):
            wsp.cell(i, j, v).font = f_txt
        wsp.cell(i, 6).number_format = "dd/mm/yyyy"
        wsp.cell(i, 14, f"=SUM(G{i}:M{i})")
        wsp.cell(i, 15, int(r.prazo_planejado_dias))
        wsp.cell(i, 16, f"=IF(N{i}<=O{i},1,0)")
        wsp.cell(i, 17, int(r.rodadas_retrabalho))
    n_p = len(proj) + 1
    _estilo_tabela(wsp, 2, n_p, 1, 17)
    wsp.cell(n_p + 2, 1, "Fonte: fato_projetos + fato_etapas (banco da agência). Grupo alternado por data de início: "
                         "1º Controle, 2º Teste, 3º Controle…").font = f_sub
    pr = lambda col: f"Projetos_Piloto!${col}$2:${col}${n_p}"  # noqa: E731

    # ============================================================ Diario_AB
    wsdi = wb.create_sheet("Diario_AB")
    _cab(wsdi, 1, ["Data", "Sessões A", "Conversões A", "Sessões B", "Conversões B", "Conv. dia A",
                   "Conv. dia B", "Conv. acumulada A", "Conv. acumulada B"], [12, 11, 12, 11, 12, 11, 11, 15, 15])
    dias = sorted(ab["data"].unique())
    for i, d in enumerate(dias, 2):
        wsdi.cell(i, 1, pd.Timestamp(d).to_pydatetime()).number_format = "dd/mm"
        wsdi.cell(i, 2, f'=SUMIFS({rng("G")},{rng("B")},$A{i},{rng("D")},"A")')
        wsdi.cell(i, 3, f'=SUMIFS({rng("I")},{rng("B")},$A{i},{rng("D")},"A")')
        wsdi.cell(i, 4, f'=SUMIFS({rng("G")},{rng("B")},$A{i},{rng("D")},"B")')
        wsdi.cell(i, 5, f'=SUMIFS({rng("I")},{rng("B")},$A{i},{rng("D")},"B")')
        wsdi.cell(i, 6, f"=IFERROR(C{i}/B{i},0)").number_format = PCT2
        wsdi.cell(i, 7, f"=IFERROR(E{i}/D{i},0)").number_format = PCT2
        wsdi.cell(i, 8, f"=SUM(C$2:C{i})/SUM(B$2:B{i})").number_format = PCT2
        wsdi.cell(i, 9, f"=SUM(E$2:E{i})/SUM(D$2:D{i})").number_format = PCT2
    n_d = len(dias) + 1
    _estilo_tabela(wsdi, 2, n_d, 1, 9)

    # ============================================================ Por_site
    wss = wb.create_sheet("Por_site")
    _cab(wss, 1, ["Site (projeto)", "Nicho", "Tipo de site", "Template A (atual)", "Template B (catálogo)",
                  "Sessões A", "Conversões A", "Sessões B", "Conversões B", "Conversão A", "Conversão B", "Lift B vs A"],
         [13, 22, 14, 15, 17, 10, 12, 10, 12, 11, 11, 11])
    for i, r in enumerate(sites.itertuples(index=False), 2):
        for j, v in enumerate([r.projeto_id, r.nicho, r.tipo_site, r.tpl_a, r.tpl_b], 1):
            wss.cell(i, j, v)
        wss.cell(i, 6, f'=SUMIFS({rng("G")},{rng("C")},$A{i},{rng("D")},"A")')
        wss.cell(i, 7, f'=SUMIFS({rng("I")},{rng("C")},$A{i},{rng("D")},"A")')
        wss.cell(i, 8, f'=SUMIFS({rng("G")},{rng("C")},$A{i},{rng("D")},"B")')
        wss.cell(i, 9, f'=SUMIFS({rng("I")},{rng("C")},$A{i},{rng("D")},"B")')
        wss.cell(i, 10, f"=G{i}/F{i}").number_format = PCT2
        wss.cell(i, 11, f"=I{i}/H{i}").number_format = PCT2
        wss.cell(i, 12, f"=K{i}/J{i}-1").number_format = '+0.0%;-0.0%;0.0%'
    n_s = len(sites) + 1
    _estilo_tabela(wss, 2, n_s, 1, 12)

    # ============================================================ Resumo (cálculos)
    wr = wb.create_sheet("Resumo")
    wr.column_dimensions["A"].width = 38
    for col in "BCD":
        wr.column_dimensions[col].width = 20
    wr["A1"] = "Resumo do teste piloto (01/06/2025 a 30/06/2025)"
    wr["A1"].font = Font(name=F, size=13, bold=True, color="2B2B29")

    # --- A/B
    for j, t in enumerate(["Teste A/B de conversão (GA4)", "A: layout atual", "B: template do catálogo"], 1):
        c = wr.cell(3, j, t)
        c.font, c.fill = f_head, fill_head
    linhas = [
        ("Sessões", f'=SUMIFS({rng("G")},{rng("D")},"A")', f'=SUMIFS({rng("G")},{rng("D")},"B")', "#,##0"),
        ("Conversões (key events)", f'=SUMIFS({rng("I")},{rng("D")},"A")', f'=SUMIFS({rng("I")},{rng("D")},"B")', "#,##0"),
        ("Taxa de conversão", "=B5/B4", "=C5/C4", PCT2),
        ("Sessões engajadas", f'=SUMIFS({rng("H")},{rng("D")},"A")', f'=SUMIFS({rng("H")},{rng("D")},"B")', "#,##0"),
        ("Taxa de engajamento", "=B7/B4", "=C7/C4", PCT1),
    ]
    for i, (rot, fa, fb, fmt) in enumerate(linhas, 4):
        wr.cell(i, 1, rot)
        for col, fml in [(2, fa), (3, fb)]:
            wr.cell(i, col, fml).number_format = fmt
    stats = [
        (10, "Lift relativo (B vs A)", "=C6/B6-1", "+0.0%;-0.0%"),
        (11, "Diferença absoluta (p.p.)", "=(C6-B6)*100", "+0.00;-0.00"),
        (12, "Taxa combinada (pooled)", "=(B5+C5)/(B4+C4)", "0.000%"),
        (13, "Erro padrão da diferença", "=SQRT(B12*(1-B12)*(1/B4+1/C4))", "0.0000%"),
        (14, "Estatística z", "=(C6-B6)/B13", "0.00"),
        (15, "p-valor (unilateral, B > A)", "=1-NORMSDIST(B14)", "0.000"),
        (16, "Nível de significância (α)", 0.05, "0.00"),
        (17, "Resultado", '=IF(B15<B16,"Significativo: B converte mais","Inconclusivo")', "@"),
        (18, "IC 95% da diferença: inferior (p.p.)", "=(C6-B6-1.96*SQRT(B6*(1-B6)/B4+C6*(1-C6)/C4))*100", "+0.00;-0.00"),
        (19, "IC 95% da diferença: superior (p.p.)", "=(C6-B6+1.96*SQRT(B6*(1-B6)/B4+C6*(1-C6)/C4))*100", "+0.00;-0.00"),
    ]
    for r, rot, fml, fmt in stats:
        wr.cell(r, 1, rot)
        c = wr.cell(r, 2, fml)
        c.number_format = fmt
    wr["B16"].font, wr["B16"].fill = f_input, fill_input
    wr["B16"].comment = Comment("Premissa editável: nível de significância do teste (padrão de mercado: 5%).", "Analista")

    # --- projetos
    for j, t in enumerate(["Projetos (Teste × Controle)", "Controle: escolha livre", "Teste: catálogo top 10", "Variação"], 1):
        c = wr.cell(22, j, t)
        c.font, c.fill = f_head, fill_head
    col_etapa = {e: get_column_letter(7 + k) for k, e in enumerate(C.ETAPAS)}
    proj_l = [
        ("Projetos no teste", "COUNTIF", None, "0"),
        ("Dias médios de entrega", "N", None, NUM1),
        ("Escolha de layout (dias)", col_etapa["Escolha de layout"], None, NUM1),
        ("Design e aprovação (dias)", col_etapa["Design e aprovação"], None, NUM1),
        ("Desenvolvimento (dias)", col_etapa["Desenvolvimento"], None, NUM1),
        ("Rodadas de retrabalho (média)", "Q", None, "0.00"),
        ("% entregues no prazo", "P", None, "0%"),
    ]
    for k, (rot, col, _, fmt) in enumerate(proj_l):
        i = 23 + k
        wr.cell(i, 1, rot)
        for cc, g in [(2, "Controle"), (3, "Teste")]:
            fml = (f'=COUNTIF({pr("B")},"{g}")' if col == "COUNTIF"
                   else f'=AVERAGEIF({pr("B")},"{g}",{pr(col)})')
            wr.cell(i, cc, fml).number_format = fmt
        if col == "P":
            wr.cell(i, 4, f"=(C{i}-B{i})*100").number_format = '+0" p.p.";-0" p.p."'
        elif col != "COUNTIF":
            wr.cell(i, 4, f"=C{i}/B{i}-1").number_format = "+0%;-0%"
    for r in wr.iter_rows(min_row=4, max_row=29, max_col=4):
        for c in r:
            if c.row not in (22,) and c.coordinate != "B16":
                c.font = f_bold if c.column == 1 else f_txt
                c.border = borda
    wr["A31"] = ("Notas: teste z de duas proporções (unilateral). Projetos: amostra pequena (13), resultado indicativo; "
                 "o prazo foi confirmado depois no rollout (jul/2025 em diante).")
    wr["A31"].font = f_sub

    # ============================================================ Dashboard
    ws = wb.create_sheet("Dashboard", 0)
    ws.sheet_view.showGridLines = False
    for col in range(1, 22):
        ws.column_dimensions[get_column_letter(col)].width = 8.5
    ws.column_dimensions["A"].width = 2
    for r in ws.iter_rows(min_row=1, max_row=60, max_col=21):
        for c in r:
            c.fill = fill_bg
    for r in ws.iter_rows(min_row=1, max_row=3, max_col=21):
        for c in r:
            c.fill = fill_head
    ws["B2"] = "Teste Piloto de 30 Dias: Catálogo Padrão de Templates WordPress"
    ws["B2"].font = Font(name=F, size=16, bold=True, color="FFFFFF")
    ws["B3"] = "01/06/2025 a 30/06/2025  ·  Teste A/B no GA4 (12 sites) + 13 projetos (Teste × Controle)  ·  dados simulados"
    ws["B3"].font = Font(name=F, size=9, color="C9CEDA")
    ws.row_dimensions[2].height = 26

    cards = [
        ("B", "E", "Conversão com o template do catálogo", "=Resumo!C6", PCT2, "Layout atual:", "=Resumo!B6", PCT2),
        ("G", "J", "Ganho de conversão (lift)", "=Resumo!B10", "+0.0%;-0.0%", "p-valor:", "=Resumo!B15", "0.000"),
        ("L", "O", "Prazo médio: grupo Teste", "=Resumo!C24", '0.0" dias"', "Controle:", "=Resumo!B24", '0.0" dias"'),
        ("Q", "T", "Redução do prazo", "=-Resumo!D24", "0%", "Retrabalho:", "=Resumo!D28", "+0%;-0%"),
    ]
    for c1, c2, titulo, val, fmt, sub_rot, sub_val, sub_fmt in cards:
        for r in ws.iter_rows(min_row=5, max_row=9, min_col=ws[c1 + "5"].column, max_col=ws[c2 + "5"].column):
            for c in r:
                c.fill = fill_card
        ws.merge_cells(f"{c1}5:{c2}5")
        ws[f"{c1}5"] = titulo
        ws[f"{c1}5"].font = Font(name=F, size=9, color="6B6B66")
        ws.merge_cells(f"{c1}6:{c2}7")
        ws[f"{c1}6"] = val
        ws[f"{c1}6"].font = Font(name=F, size=22, bold=True, color="2B2B29")
        ws[f"{c1}6"].number_format = fmt
        ws[f"{c1}6"].alignment = Alignment(horizontal="left", vertical="center")
        mid = get_column_letter(ws[c1 + "5"].column + 1)
        ws.merge_cells(f"{c1}8:{mid}8")
        ws[f"{c1}8"] = sub_rot
        ws[f"{c1}8"].font = f_sub
        c3 = get_column_letter(ws[c1 + "5"].column + 2)
        ws.merge_cells(f"{c3}8:{c2}8")
        ws[f"{c3}8"] = sub_val
        ws[f"{c3}8"].number_format = sub_fmt
        ws[f"{c3}8"].font = Font(name=F, size=10, bold=True, color=AZUL)
        ws[f"{c3}8"].alignment = Alignment(horizontal="right")

    ws.merge_cells("B11:T11")
    ws["B11"] = '="Conclusão: "&Resumo!B17&" (α = 5%). Prazo do grupo Teste menor que o do Controle. Recomendação: aprovar a padronização para todos os projetos a partir de jul/2025."'
    ws["B11"].font = Font(name=F, size=10, bold=True, color="FFFFFF")
    ws["B11"].fill = PatternFill("solid", fgColor=AZUL)
    ws["B11"].alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[11].height = 24

    # gráfico 1: conversão acumulada
    g1 = _chart_base(LineChart(), "Taxa de conversão acumulada: A × B", "Conversão")
    g1.add_data(Reference(wsdi, min_col=8, max_col=9, min_row=1, max_row=n_d), titles_from_data=True)
    g1.set_categories(Reference(wsdi, min_col=1, min_row=2, max_row=n_d))
    g1.y_axis.number_format = "0.0%"
    g1.y_axis.scaling.min = 0.015
    g1.y_axis.scaling.max = 0.026
    g1.x_axis.number_format = "dd/mm"
    for s, cor in zip(g1.series, [CINZA, AZUL]):
        s.graphicalProperties.line.solidFill = cor
        s.graphicalProperties.line.width = 28000
        s.smooth = False
    g1.width, g1.height = 15.8, 8
    ws.add_chart(g1, "B13")

    # gráfico 2: dias por etapa
    g2 = _chart_base(BarChart(), "Dias médios nas etapas mais afetadas", "Dias")
    g2.type = "col"
    g2.add_data(Reference(wr, min_col=2, max_col=3, min_row=25, max_row=27), titles_from_data=False)
    g2.set_categories(Reference(wr, min_col=1, min_row=25, max_row=27))
    g2.series[0].tx = SeriesLabel(v="Controle (escolha livre)")
    g2.series[1].tx = SeriesLabel(v="Teste (catálogo top 10)")
    for s, cor in zip(g2.series, [CINZA, AZUL]):
        s.graphicalProperties.solidFill = cor
        s.graphicalProperties.line.noFill = True
    g2.gapWidth = 60
    g2.width, g2.height = 15.8, 8
    ws.add_chart(g2, "L13")

    # gráfico 3: conversão por site
    g3 = _chart_base(BarChart(), "Conversão por site: A (layout atual) × B (template do catálogo)", "Conversão")
    g3.type = "col"
    g3.add_data(Reference(wss, min_col=10, max_col=11, min_row=1, max_row=n_s), titles_from_data=True)
    g3.set_categories(Reference(wss, min_col=1, min_row=2, max_row=n_s))
    g3.y_axis.number_format = "0.0%"
    for s, cor in zip(g3.series, [CINZA, AZUL]):
        s.graphicalProperties.solidFill = cor
        s.graphicalProperties.line.noFill = True
    g3.gapWidth = 50
    g3.width, g3.height = 32.5, 8
    ws.add_chart(g3, "B30")

    ws["B47"] = ("Como ler: A = layout atual do site; B = mesma página reconstruída com o template indicado pela matriz "
                 "nicho × tipo de site. Tráfego dividido 50/50 por plugin de teste A/B; conversões = key events do GA4.")
    ws["B47"].font = f_sub
    ws["B48"] = "Cálculos na aba Resumo · dados brutos nas abas Dados_AB e Projetos_Piloto · metodologia na aba Metodologia."
    ws["B48"].font = f_sub

    # ============================================================ Metodologia
    wm = wb.create_sheet("Metodologia")
    wm.column_dimensions["A"].width = 28
    wm.column_dimensions["B"].width = 110
    textos = [
        ("Objetivo", "Validar, antes do rollout, se o catálogo dos 10 templates de maior desempenho reduz o prazo de "
                     "entrega e não piora (ou melhora) a conversão das páginas."),
        ("Período", "30 dias: 01/06/2025 a 30/06/2025."),
        ("Frente 1: projetos", "Projetos iniciados na janela foram alternados por data de início entre Controle "
                               "(escolha livre de layout) e Teste (catálogo top 10 + fluxo documentado). Métricas: dias por "
                               "etapa, dias totais até a entrega e rodadas de retrabalho."),
        ("Frente 2: teste A/B", "12 sites já publicados (institucional, landing page e portfólio). As páginas principais "
                                "foram reconstruídas com o template do catálogo indicado para o nicho (variante B), e o "
                                "tráfego foi dividido 50/50 com o layout atual (variante A). Conversão = key events do GA4 "
                                "(lead, clique no WhatsApp)."),
        ("Teste estatístico", "Teste z de duas proporções, unilateral (H1: conversão B > A), α = 5%. Intervalo de "
                              "confiança de 95% para a diferença absoluta."),
        ("Critério de decisão", "Aprovar o rollout se (1) a conversão de B for estatisticamente maior que a de A ou, no "
                                "mínimo, não inferior e (2) o grupo Teste tiver prazo menor que o Controle."),
        ("Limitações", "Amostra de projetos pequena (13): o efeito no prazo é indicativo e foi confirmado depois do "
                       "rollout (44,8 → 31,5 dias). A janela de 30 dias não captura sazonalidade."),
        ("Resultado", "Critérios atendidos. Padronização aprovada e implantada a partir de 01/07/2025, com "
                      "acompanhamento contínuo no Power BI."),
    ]
    wm["A1"] = "Metodologia do teste piloto"
    wm["A1"].font = Font(name=F, size=13, bold=True)
    for i, (k, v) in enumerate(textos, 3):
        wm.cell(i, 1, k).font = f_bold
        c = wm.cell(i, 2, v)
        c.font = f_txt
        c.alignment = Alignment(wrap_text=True, vertical="top")
        wm.row_dimensions[i].height = 44
    wm.cell(13, 1, "Legenda de cores").font = f_bold
    wm.cell(14, 1, "Texto azul / fundo amarelo").font = f_input
    wm.cell(14, 1).fill = fill_input
    wm.cell(14, 2, "Premissa editável (Resumo!B16, nível de significância). Os demais valores são fórmulas.").font = f_txt

    ws.sheet_properties.tabColor = AZUL
    wb.active = 0
    ws.print_area = "A1:U49"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    wb.calculation.fullCalcOnLoad = True  # Excel recalcula todas as fórmulas ao abrir
    SAIDA.parent.mkdir(exist_ok=True)
    wb.save(SAIDA)
    return SAIDA


if __name__ == "__main__":
    print(construir())
