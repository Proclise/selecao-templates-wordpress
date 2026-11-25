"""
Gera a base simulada da agência (jan/2023 a out/2026).

Tabelas geradas em data/raw/ (esquema estrela):
  dim_templates, dim_nichos, dim_tipos_site, dim_clientes, dim_calendario
  fato_projetos      – 1 linha por projeto de site WordPress
  fato_etapas        – duração de cada etapa do projeto
  fato_ga4_paginas   – exportação mensal do Google Analytics 4 por página

Cenário simulado:
  • ANTES (jan/2023 a mar/2025): o layout era escolhido sem critério, por preferência
    do designer, entre ~36 templates. Isso gerava muitas rodadas de aprovação e atrasos.
  • TRANSIÇÃO (abr a jun/2025): consolidação dos dados, análise e dashboards no Power BI.
  • DEPOIS (jul/2025 em diante): a equipe usa o catálogo dos 10 templates de melhor
    desempenho, escolhidos pelo ranking calculado SOMENTE com os dados do período ANTES.
"""

import numpy as np
import pandas as pd

import config as C
from ranking import ranquear, selecionar_top

TEMAS = [
    # (tema, page builder, fator de conversão, fator de complexidade)
    ("Astra", "Elementor", 1.00, 0.92),
    ("Hello Elementor", "Elementor", 0.99, 0.90),
    ("Kadence", "Gutenberg", 1.07, 0.92),
    ("GeneratePress", "Gutenberg", 1.06, 0.95),
    ("Blocksy", "Gutenberg", 1.05, 0.94),
    ("Divi", "Divi Builder", 0.95, 1.08),
    ("Avada", "WPBakery", 0.90, 1.25),
    ("OceanWP", "Elementor", 0.97, 1.00),
    ("Flatsome", "UX Builder", 1.02, 1.00),
]
ESTILOS = ["Minimal", "Corporate", "Bold", "Clean", "Modern", "Classic", "Fresh", "Prime"]


def _templates(rng) -> pd.DataFrame:
    linhas, nichos = [], list(C.NICHOS)
    i = 1
    for familia, qtd in [("Geral", 24), ("WooCommerce", 12)]:
        for _ in range(qtd):
            tema, builder, f_conv, f_cx = TEMAS[rng.integers(len(TEMAS))]
            if familia == "WooCommerce" and rng.random() < 0.35:
                tema, builder, f_conv, f_cx = TEMAS[8]  # Flatsome é popular em lojas
            if familia == "Geral" and tema == "Flatsome":  # Flatsome é tema de loja
                tema, builder = "Neve", "Gutenberg"
            alvo = rng.choice(nichos)
            linhas.append({
                "template_id": f"WP-{i:02d}",
                "nome_template": f"{tema} {rng.choice(ESTILOS)} {alvo.split()[0]}",
                "tema_base": tema,
                "page_builder": builder,
                "familia": familia,
                "nicho_alvo": alvo,
                "data_cadastro": (C.INICIO_HISTORICO - pd.Timedelta(days=int(rng.integers(30, 700)))).date(),
                "_conv": f_conv * rng.lognormal(0, 0.11),
                "_cx": f_cx * rng.lognormal(0, 0.11),
                "_rework": 1.35 * f_cx * rng.lognormal(0, 0.22),
            })
            i += 1
    return pd.DataFrame(linhas)


def _clientes(rng, n: int) -> pd.DataFrame:
    ufs = rng.choice(["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "PE", "DF", "GO"], size=n,
                     p=[.30, .13, .12, .09, .08, .08, .06, .05, .05, .04])
    nichos = list(C.NICHOS)
    pesos = np.array([v[0] for v in C.NICHOS.values()])
    return pd.DataFrame({
        "cliente_id": [f"CLI-{i:04d}" for i in range(1, n + 1)],
        "nome_cliente": [f"Cliente {i:04d}" for i in range(1, n + 1)],
        "nicho": rng.choice(nichos, size=n, p=pesos / pesos.sum()),
        "uf": ufs,
        "porte": rng.choice(["MEI", "Pequena", "Média"], size=n, p=[.35, .5, .15]),
    })


def _datas_inicio(rng, ini, fim, por_mes):
    meses = pd.date_range(ini, fim, freq="MS")
    datas = []
    for m in meses:
        for _ in range(rng.poisson(por_mes)):
            datas.append(m + pd.Timedelta(days=int(rng.integers(0, 28))))
    return sorted(datas)


def _simular_projetos(rng, datas, clientes, templates, fase, catalogo=None, id_ini=1):
    tipos = list(C.TIPOS_SITE)
    pesos_tipo = np.array([v[0] for v in C.TIPOS_SITE.values()])
    tpl = templates.set_index("template_id")
    proj, etapas = [], []

    for k, data_ini in enumerate(datas):
        pid = f"PRJ-{id_ini + k:04d}"
        cli = clientes.iloc[rng.integers(len(clientes))]
        tipo = rng.choice(tipos, p=pesos_tipo / pesos_tipo.sum())
        _, dev_base, prazo, familia = C.TIPOS_SITE[tipo]
        compat = templates[templates["familia"] == familia]

        if catalogo is None:  # escolha livre, sem critério
            tid = rng.choice(compat["template_id"])
        else:  # catálogo padronizado: prioriza nicho-alvo; senão, os melhores da família
            cat = catalogo[catalogo["familia"] == familia]
            match = cat[cat["nicho_alvo"] == cli["nicho"]]
            opcoes = match if len(match) and rng.random() < 0.8 else cat.head(3)
            tid = rng.choice(opcoes["template_id"])
        t = tpl.loc[tid]
        fit = t["nicho_alvo"] == cli["nicho"]

        depois = fase == "Depois"
        lam = t["_rework"] * (0.75 if fit else 1.10) * (0.48 if depois else 1.0)
        rodadas = int(rng.poisson(lam))
        d = {
            "Briefing": 2 + rng.gamma(2, 0.7),
            "Escolha de layout": (1 + rng.gamma(2, 0.35)) if depois else rng.gamma(2.4, 2.9),
            "Design e aprovação": 3 + rodadas * 3.0 + rng.gamma(1.5, 0.8),
            "Desenvolvimento": dev_base * t["_cx"] * rng.lognormal(0, 0.15) * (0.80 if depois else 1.0),
            "Conteúdo": rng.gamma(3, 1.9),
            "QA e ajustes": 1.5 + 2 * t["_cx"] + rodadas * 0.6 + rng.gamma(1.2, 0.6),
            "Publicação": 1.0,
        }
        d = {e: max(1, round(v)) for e, v in d.items()}
        total = sum(d.values())
        data_ent = data_ini + pd.Timedelta(days=total)
        proj.append({
            "projeto_id": pid, "cliente_id": cli["cliente_id"], "nicho": cli["nicho"],
            "tipo_site": tipo, "template_id": tid, "data_inicio": data_ini, "data_entrega": data_ent,
            "prazo_planejado_dias": prazo, "dias_entrega": total, "rodadas_retrabalho": rodadas,
            "horas_desenvolvimento": round(d["Desenvolvimento"] * rng.uniform(5.5, 7.0), 1),
            "valor_projeto_brl": round(dev_base * 180 * rng.uniform(0.85, 1.3), -1),
            "url_site": f"https://www.cliente{id_ini + k:04d}.com.br",
            "conv_latente": t["_conv"] * (1.10 if fit else 1.0) * rng.lognormal(0, 0.14),
        })
        ordem = 0
        for etapa, dias in d.items():
            ordem += 1
            etapas.append({"projeto_id": pid, "ordem_etapa": ordem, "etapa": etapa, "dias": dias})
    return pd.DataFrame(proj), pd.DataFrame(etapas)


def _simular_ga4(rng, projetos, escala_conv=0.94):
    linhas = []
    for p in projetos.itertuples():
        lanc = pd.Timestamp(p.data_entrega).to_period("M").to_timestamp()
        meses = [m for m in pd.date_range(lanc, periods=6, freq="MS") if m <= C.FIM_HISTORICO]
        traf_nicho, conv_nicho = C.NICHOS[p.nicho][1], C.NICHOS[p.nicho][2]
        porte = rng.lognormal(0, 0.45)
        for i, mes in enumerate(meses):
            rampa = min(1.0, 0.45 + 0.18 * i)
            for pagina in C.PAGINAS_POR_TIPO[p.tipo_site]:
                peso, taxa = C.TIPOS_PAGINA[pagina]
                sess = int(rng.poisson(520 * peso * traf_nicho * porte * rampa * rng.lognormal(0, 0.2)))
                if sess == 0:
                    continue
                taxa_real = min(0.9, taxa * conv_nicho * p.conv_latente * escala_conv)
                conv = int(rng.binomial(sess, taxa_real))
                engaj = int(rng.binomial(sess, min(0.95, 0.55 * p.conv_latente)))
                slug = {"Home": "/", "Landing Page": "/lp/"}.get(pagina, f"/{pagina.lower().replace(' ', '-')}/")
                linhas.append({
                    "projeto_id": p.projeto_id, "mes": mes.date(), "page_path": slug,
                    "tipo_pagina": pagina, "sessoes": sess, "usuarios": int(sess * rng.uniform(0.78, 0.9)),
                    "sessoes_engajadas": engaj,
                    "tempo_medio_engajamento_s": round(rng.gamma(4, 12) * (1.6 if pagina == "Post de Blog" else 1), 1),
                    "conversoes": conv,
                })
    return pd.DataFrame(linhas)


def gerar(seed: int = C.SEED):
    rng = np.random.default_rng(seed)
    templates = _templates(rng)
    clientes = _clientes(rng, 420)

    d_antes = _datas_inicio(rng, C.INICIO_HISTORICO, C.INICIO_TRANSICAO - pd.Timedelta(days=1), 8.0)
    d_trans = _datas_inicio(rng, C.INICIO_TRANSICAO, C.INICIO_PADRONIZACAO - pd.Timedelta(days=1), 8.0)
    d_depois = _datas_inicio(rng, C.INICIO_PADRONIZACAO, pd.Timestamp("2026-09-30"), 9.0)

    p1, e1 = _simular_projetos(rng, d_antes + d_trans, clientes, templates, "Antes")
    g1 = _simular_ga4(rng, p1)

    # ---- a decisão: ranking calculado somente com o histórico ANTES ----
    antes = p1[p1["data_inicio"] < C.INICIO_TRANSICAO]
    rank = ranquear(antes, g1[g1["projeto_id"].isin(antes["projeto_id"])], templates)
    catalogo = selecionar_top(rank)

    p2, e2 = _simular_projetos(rng, d_depois, clientes, templates, "Depois",
                               catalogo=catalogo, id_ini=len(p1) + 1)
    g2 = _simular_ga4(rng, p2)

    projetos = pd.concat([p1, p2], ignore_index=True)
    projetos["periodo"] = C.periodo(projetos["data_inicio"])
    etapas = pd.concat([e1, e2], ignore_index=True)
    ga = pd.concat([g1, g2], ignore_index=True)
    ga.insert(0, "ga_id", range(1, len(ga) + 1))
    etapas.insert(0, "etapa_id", range(1, len(etapas) + 1))

    templates["no_catalogo_padrao"] = np.where(templates["template_id"].isin(catalogo["template_id"]), "Sim", "Não")
    dim_nichos = pd.DataFrame([{"nicho": k, "segmento": "Varejo" if k in ("Moda e Varejo", "Restaurantes e Delivery")
                                else "Serviços"} for k in C.NICHOS])
    dim_tipos = pd.DataFrame([{"tipo_site": k, "familia_template": v[3], "prazo_planejado_dias": v[2],
                               "paginas_padrao": ", ".join(C.PAGINAS_POR_TIPO[k])} for k, v in C.TIPOS_SITE.items()])
    cal = pd.DataFrame({"data": pd.date_range(C.INICIO_HISTORICO, C.FIM_HISTORICO, freq="D")})
    cal["ano"], cal["mes_num"] = cal["data"].dt.year, cal["data"].dt.month
    cal["ano_mes"] = cal["data"].dt.strftime("%Y-%m")
    cal["trimestre"] = "T" + cal["data"].dt.quarter.astype(str) + "/" + cal["ano"].astype(str)
    cal["periodo"] = C.periodo(cal["data"])

    projetos = projetos.drop(columns="conv_latente")
    for col in ["data_inicio", "data_entrega"]:
        projetos[col] = projetos[col].dt.date
    cal["data"] = cal["data"].dt.date

    return {
        "dim_templates": templates.drop(columns=["_conv", "_cx", "_rework"]),
        "dim_nichos": dim_nichos, "dim_tipos_site": dim_tipos, "dim_clientes": clientes,
        "dim_calendario": cal, "fato_projetos": projetos, "fato_etapas": etapas, "fato_ga4_paginas": ga,
    }


if __name__ == "__main__":
    C.RAW.mkdir(parents=True, exist_ok=True)
    for nome, df in gerar().items():
        df.to_csv(C.RAW / f"{nome}.csv", index=False, encoding="utf-8")
        print(f"{nome:<18} {len(df):>6} linhas")
