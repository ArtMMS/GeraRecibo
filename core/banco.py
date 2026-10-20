import re
import sqlite3
from contextlib import closing
from dataclasses import fields
from datetime import date, datetime

from core.caminhos import pasta
from core.recibo import Recibo

# Campos do Recibo guardados no banco (o número vira a chave da tabela)
CAMPOS = [campo.name for campo in fields(Recibo) if campo.name != "numero_recibo"]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS recibos (
    numero_recibo            INTEGER PRIMARY KEY,
    criado_em                TEXT    NOT NULL,
    caminho_pdf              TEXT    NOT NULL DEFAULT '',

    emitente_tipo_documento  TEXT    NOT NULL,
    emitente_nome            TEXT    NOT NULL,
    emitente_documento       TEXT    NOT NULL,
    emitente_telefones       TEXT    NOT NULL DEFAULT '',
    emitente_logo            TEXT    NOT NULL DEFAULT '',

    tipo_documento           TEXT    NOT NULL,
    nome                     TEXT    NOT NULL,
    documento                TEXT    NOT NULL,

    produto                  TEXT    NOT NULL,
    quantidade               INTEGER NOT NULL,
    valor                    REAL    NOT NULL,
    data                     TEXT    NOT NULL,

    rua                      TEXT    NOT NULL,
    numero                   TEXT    NOT NULL,
    bairro                   TEXT    NOT NULL,
    cidade                   TEXT    NOT NULL,
    estado                   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recibos_nome ON recibos (nome COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_recibos_data ON recibos (data);
"""


# ---------- Conexão ----------

def caminho_banco():
    return pasta("dados") / "recibos.db"


def conectar():
    conexao = sqlite3.connect(caminho_banco())
    conexao.row_factory = sqlite3.Row
    conexao.executescript(ESQUEMA)
    return conexao


# ---------- Conversões ----------

def _valores(recibo):
    """Valores do recibo na ordem de CAMPOS (data vira texto ISO)."""
    return [
        recibo.data.isoformat() if campo == "data" else getattr(recibo, campo)
        for campo in CAMPOS
    ]


def _recibo_da_linha(linha):
    dados = {campo: linha[campo] for campo in CAMPOS}
    dados["data"] = date.fromisoformat(dados["data"])
    return Recibo(**dados, numero_recibo=linha["numero_recibo"])


def _proximo(conexao):
    linha = conexao.execute(
        "SELECT COALESCE(MAX(numero_recibo), 0) + 1 FROM recibos"
    ).fetchone()
    return linha[0]


# ---------- Escrita ----------

def proximo_numero():
    """Número que o próximo recibo salvo vai receber."""
    with closing(conectar()) as conexao:
        return _proximo(conexao)


def salvar(recibo, caminho_pdf):
    """Grava um recibo novo. Retorna o número dele."""
    with closing(conectar()) as conexao, conexao:
        if recibo.numero_recibo is None:
            recibo.numero_recibo = _proximo(conexao)

        colunas = ["numero_recibo", "criado_em", "caminho_pdf", *CAMPOS]
        marcadores = ", ".join("?" for _ in colunas)

        conexao.execute(
            f"INSERT INTO recibos ({', '.join(colunas)}) VALUES ({marcadores})",
            [
                recibo.numero_recibo,
                datetime.now().isoformat(timespec="seconds"),
                str(caminho_pdf),
                *_valores(recibo),
            ],
        )

    return recibo.numero_recibo


def atualizar_caminho(numero_recibo, caminho_pdf):
    """Atualiza onde está o PDF (usado ao reemitir)."""
    with closing(conectar()) as conexao, conexao:
        conexao.execute(
            "UPDATE recibos SET caminho_pdf = ? WHERE numero_recibo = ?",
            [str(caminho_pdf), numero_recibo],
        )


# ---------- Leitura ----------

def obter(numero_recibo):
    """Retorna (Recibo, caminho_pdf) ou None se não existir."""
    with closing(conectar()) as conexao:
        linha = conexao.execute(
            "SELECT * FROM recibos WHERE numero_recibo = ?", [numero_recibo]
        ).fetchone()

    return (_recibo_da_linha(linha), linha["caminho_pdf"]) if linha else None


def buscar(texto="", data_inicio=None, data_fim=None, limite=500):
    """Busca por nome ou CPF/CNPJ do cliente e/ou período (data do pedido).

    Retorna lista de (Recibo, caminho_pdf), do mais novo para o mais antigo.
    """
    condicoes, parametros = [], []

    if texto:
        so_documento = re.sub(r"[.\-/\s]", "", texto)
        condicoes.append(
            "(nome LIKE ? "
            "OR REPLACE(REPLACE(REPLACE(documento, '.', ''), '-', ''), '/', '') LIKE ?)"
        )
        parametros += [f"%{texto}%", f"%{so_documento}%"]

    if data_inicio:
        condicoes.append("data >= ?")
        parametros.append(data_inicio.isoformat())

    if data_fim:
        condicoes.append("data <= ?")
        parametros.append(data_fim.isoformat())

    onde = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""

    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            f"SELECT * FROM recibos {onde} ORDER BY numero_recibo DESC LIMIT ?",
            [*parametros, limite],
        ).fetchall()

    return [(_recibo_da_linha(linha), linha["caminho_pdf"]) for linha in linhas]


def clientes():
    """Nomes de clientes já usados (para o autocompletar)."""
    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            "SELECT nome FROM recibos "
            "GROUP BY nome COLLATE NOCASE "
            "ORDER BY nome COLLATE NOCASE"
        ).fetchall()

    return [linha["nome"] for linha in linhas]


def ultimo_do_cliente(nome):
    """Recibo mais recente de um cliente (para preencher documento e endereço)."""
    with closing(conectar()) as conexao:
        linha = conexao.execute(
            "SELECT * FROM recibos WHERE nome = ? COLLATE NOCASE "
            "ORDER BY numero_recibo DESC LIMIT 1",
            [nome],
        ).fetchone()

    return _recibo_da_linha(linha) if linha else None