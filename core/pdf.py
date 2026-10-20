import re
import sys
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


# ---------- Onde salvar ----------

def pasta_recibos():
    """Pasta 'recibos/' ao lado do projeto (ou ao lado do .exe)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent

    pasta = base / "recibos"
    pasta.mkdir(exist_ok=True)
    return pasta


def _slug(texto, limite=40):
    """Ex.: 'Colégio Jardim Escola' → 'colegio-jardim-escola'."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].strip("-") or "cliente"


def caminho_disponivel(recibo):
    """Ex.: recibos/recibo_2026-07-23_colegio-jardim.pdf (sem sobrescrever)."""
    pasta = pasta_recibos()
    nome_base = f"recibo_{recibo.data.isoformat()}_{_slug(recibo.nome)}"

    caminho = pasta / f"{nome_base}.pdf"
    contador = 2
    while caminho.exists():
        caminho = pasta / f"{nome_base}_{contador}.pdf"
        contador += 1

    return caminho


# ---------- Layout ----------

def _estilos():
    return {
        "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=22, leading=26),
        "valor": ParagraphStyle(
            "valor", fontName="Helvetica", fontSize=14, leading=18, alignment=TA_RIGHT
        ),
        "corpo": ParagraphStyle(
            "corpo", fontName="Helvetica", fontSize=12, leading=22, alignment=TA_LEFT
        ),
        "data": ParagraphStyle(
            "data", fontName="Helvetica", fontSize=12, leading=16, alignment=TA_RIGHT
        ),
        "emitente_nome": ParagraphStyle(
            "emitente_nome", fontName="Helvetica-Bold", fontSize=11, leading=15, alignment=TA_CENTER
        ),
        "emitente": ParagraphStyle(
            "emitente", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_CENTER
        ),
    }


def _cabecalho(recibo, largura, estilos):
    tabela = Table(
        [[
            Paragraph("RECIBO", estilos["titulo"]),
            Paragraph(f"Valor: <b>{recibo.valor_formatado}</b>", estilos["valor"]),
        ]],
        colWidths=[largura / 2, largura / 2],
    )
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tabela


def _corpo(recibo, estilos):
    """Cada linha do texto vira uma linha no PDF."""
    linhas = [escape(linha) for linha in recibo.linhas_do_texto()]
    return Paragraph("<br/>".join(linhas), estilos["corpo"])


def _linha_assinatura():
    linha = Table([[""]], colWidths=[9 * cm], hAlign="CENTER")
    linha.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
    ]))
    return linha


def _rodape_emitente(recibo, estilos):
    elementos = [
        Paragraph(escape(recibo.emitente_nome), estilos["emitente_nome"]),
        Paragraph(
            f"{recibo.emitente_tipo_documento}: {escape(recibo.emitente_documento)}",
            estilos["emitente"],
        ),
    ]

    if recibo.emitente_telefones:
        elementos.append(
            Paragraph(f"Tel: {escape(recibo.emitente_telefones)}", estilos["emitente"])
        )

    return elementos


# ---------- Geração ----------

def gerar_pdf(recibo, caminho=None):
    """Gera o PDF do recibo e retorna o caminho do arquivo salvo."""
    caminho = Path(caminho) if caminho else caminho_disponivel(recibo)

    doc = SimpleDocTemplate(
        str(caminho),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        title=f"Recibo - {recibo.nome}",
        author=recibo.emitente_nome,
    )
    estilos = _estilos()

    elementos = [
        _cabecalho(recibo, doc.width, estilos),
        Spacer(1, 1.2 * cm),
        _corpo(recibo, estilos),
        Spacer(1, 1 * cm),
        Paragraph(escape(recibo.local_e_data()), estilos["data"]),
        Spacer(1, 2.5 * cm),
        _linha_assinatura(),
        *_rodape_emitente(recibo, estilos),
    ]

    doc.build(elementos)
    return caminho