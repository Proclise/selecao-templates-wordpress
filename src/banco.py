"""
Cria o banco centralizado (SQLite), carrega os CSVs e cria as views.
Também executa as consultas analíticas e salva os resultados em reports/sql/.

Uso:
    python src/banco.py
"""

import re
import sqlite3

import pandas as pd

import config as C

ORDEM_CARGA = ["dim_nichos", "dim_tipos_site", "dim_templates", "dim_clientes", "dim_calendario",
               "fato_projetos", "fato_etapas", "fato_ga4_paginas"]


def criar_banco() -> None:
    C.DB.unlink(missing_ok=True)
    with sqlite3.connect(C.DB) as con:
        con.executescript((C.SQL_DIR / "01_schema.sql").read_text(encoding="utf-8"))
        for tabela in ORDEM_CARGA:
            df = pd.read_csv(C.RAW / f"{tabela}.csv")
            df.to_sql(tabela, con, if_exists="append", index=False)
        con.executescript((C.SQL_DIR / "02_views.sql").read_text(encoding="utf-8"))
        problemas = con.execute("PRAGMA foreign_key_check").fetchall()
        assert not problemas, f"Violação de chave estrangeira: {problemas[:5]}"


def consultas() -> dict[str, str]:
    texto = (C.SQL_DIR / "03_consultas_analiticas.sql").read_text(encoding="utf-8")
    partes = re.split(r"^-- (Q\d+\..*)$", texto, flags=re.M)[1:]
    return {partes[i].strip(): partes[i + 1].strip() for i in range(0, len(partes), 2)}


def executar_consultas(mostrar: bool = False) -> dict[str, pd.DataFrame]:
    saida = C.REPORTS / "sql"
    saida.mkdir(parents=True, exist_ok=True)
    res = {}
    with sqlite3.connect(C.DB) as con:
        for titulo, q in consultas().items():
            df = pd.read_sql_query(q, con)
            res[titulo] = df
            df.to_csv(saida / f"{titulo.split('.')[0].lower()}.csv", index=False)
            if mostrar:
                print(f"\n{titulo}\n{df.head(12).to_string(index=False)}")
    return res


def ler(sql: str) -> pd.DataFrame:
    with sqlite3.connect(C.DB) as con:
        return pd.read_sql_query(sql, con)


if __name__ == "__main__":
    criar_banco()
    print(f"Banco criado: {C.DB.relative_to(C.RAIZ)}")
    executar_consultas(mostrar=True)
