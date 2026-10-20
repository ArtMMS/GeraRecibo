import re
import unicodedata
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.caminhos import pasta

# Página: largura do A4, altura calculada pelo conteúdo
LARGURA_PAGINA = A4[0]
MARGEM_LATERAL = 2.5 * cm
MARGEM_VERTICAL = 1.5 * cm
FOLGA = 1 * cm  # espaço extra para nada ser empurrado para outra página

# Tamanho máximo da logo no cabeçalho
LOGO_ALTURA_MAX = 1.8 * cm
LOGO_LARGURA_MAX = 4 * cm


# ---------- Onde salvar ----------

def pasta_recibos():
    """Pasta padrão 'recibos/' ao lado do projeto (ou ao lado do .exe)."""
    return pasta("recibos")


def _slug(texto, limite=40):
    """Ex.: 'Colégio Jardim Escola' → 'colegio-jardim-escola'."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].strip("-") or "cliente"


def caminho_disponivel(recibo, pasta_destino=None):
    """Ex.: <pasta>/recibo_0001_2026-07-23_colegio-jardim.pdf (sem sobrescrever)."""
    pasta_destino = Path(pasta_destino) if pasta_destino else pasta_recibos()
    pasta_destino.mkdir(parents=True, exist_ok=True)

    partes = ["recibo"]
    if recibo.numero_recibo:
        partes.append(recibo.numero_formatado)
    partes += [recibo.data.isoformat(), _slug(recibo.nome)]
    nome_base = "_".join(partes)

    caminho = pasta_destino / f"{nome_base}.pdf"
    contador = 2
    while caminho.exists():
        caminho = pasta_destino / f"{nome_base}_{contador}.pdf"
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


def _logo(caminho):
    """Carrega a logo mantendo a proporção. Retorna None se não der para usar."""
    if not caminho or not Path(caminho).is_file():
        return None

    try:
        largura, altura = ImageReader(caminho).getSize()
    except Exception:
        return None

    escala = min(LOGO_LARGURA_MAX / largura, LOGO_ALTURA_MAX / altura)
    imagem = Image(caminho, width=largura * escala, height=altura * escala)
    imagem.hAlign = "LEFT"
    return imagem


def _titulo(recibo, estilos):
    texto = "RECIBO"
    if recibo.numero_recibo:
        texto += f' <font name="Helvetica" size="12">Nº {recibo.numero_formatado}</font>'
    return Paragraph(texto, estilos["titulo"])


def _cabecalho(recibo, largura, estilos):
    titulo = _titulo(recibo, estilos)
    valor = Paragraph(f"Valor: <b>{recibo.valor_formatado}</b>", estilos["valor"])
    logo = _logo(recibo.emitente_logo)

    if logo:
        largura_logo = logo.drawWidth + 0.5 * cm
        resto = largura - largura_logo
        tabela = Table(
            [[logo, titulo, valor]],
            colWidths=[largura_logo, resto / 2, resto / 2],
        )
    else:
        tabela = Table([[titulo, valor]], colWidths=[largura / 2, largura / 2])

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


def _altura_do_conteudo(elementos, largura):
    """Soma a altura de todos os blocos do recibo."""
    return sum(elemento.wrap(largura, 100 * cm)[1] for elemento in elementos)


# ---------- Geração ----------

def gerar_pdf(recibo, caminho=None):
    """Gera o PDF do recibo e retorna o caminho do arquivo salvo."""
    caminho = Path(caminho) if caminho else caminho_disponivel(recibo)

    largura_util = LARGURA_PAGINA - 2 * MARGEM_LATERAL
    estilos = _estilos()

    elementos = [
        _cabecalho(recibo, largura_util, estilos),
        Spacer(1, 0.8 * cm),
        _corpo(recibo, estilos),
        Spacer(1, 0.6 * cm),
        Paragraph(escape(recibo.local_e_data()), estilos["data"]),
        Spacer(1, 1.8 * cm),
        _linha_assinatura(),
        *_rodape_emitente(recibo, estilos),
    ]

    altura_pagina = (
        _altura_do_conteudo(elementos, largura_util)
        + 2 * MARGEM_VERTICAL
        + FOLGA
    )

    titulo_doc = f"Recibo {recibo.numero_formatado} - {recibo.nome}".replace("  ", " ")

    doc = SimpleDocTemplate(
        str(caminho),
        pagesize=(LARGURA_PAGINA, altura_pagina),
        leftMargin=MARGEM_LATERAL,
        rightMargin=MARGEM_LATERAL,
        topMargin=MARGEM_VERTICAL,
        bottomMargin=MARGEM_VERTICAL,
        title=titulo_doc,
        author=recibo.emitente_nome,
    )

    doc.build(elementos)
    return caminho