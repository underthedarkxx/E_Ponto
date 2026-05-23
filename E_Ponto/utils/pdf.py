# =====================================================================
# utils/pdf.py — Geração do PDF de comprovante de ponto
# ---------------------------------------------------------------------
# Usa a biblioteca ReportLab para montar um PDF "Hello World" com
# uma tabela dos campos legais exigidos pela Portaria 671/2021
# (art. 81 — comprovante de marcação).
# =====================================================================

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


def gerar_comprovante(registro) -> bytes:
    """Generate PDF receipt for a time punch record."""
    # BytesIO atua como arquivo em memória — não toca o disco.
    buf = BytesIO()

    # SimpleDocTemplate cuida da paginação e margens.
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    # Estilos prontos (Title, Normal, Heading1, etc.).
    styles = getSampleStyleSheet()
    # `story` é a lista de elementos que vão aparecer no PDF.
    story = []

    # ---- Título ------------------------------------------------------
    story.append(Paragraph("COMPROVANTE DE REGISTRO DE PONTO", styles['Title']))
    story.append(Paragraph("REP-P — Portaria MTP no 671/2021", styles['Normal']))
    story.append(Spacer(1, 0.5 * cm))   # espaço em branco

    # Converte UTC -> horário local do servidor para exibição.
    ts_local = registro.timestamp_utc.astimezone()

    # Campos que podem ter valores ausentes ganham um fallback.
    local_nome = registro.local_trabalho.nome if registro.local_trabalho else 'Nao informado'
    geo_val = (
        f"{registro.latitude}, {registro.longitude}"
        if registro.latitude else 'Nao coletada'
    )

    # ---- Tabela de dados --------------------------------------------
    # Lista de listas (linhas x colunas). Primeira linha é o cabeçalho.
    dados = [
        ['Campo', 'Valor'],
        ['Empregador', registro.empresa.trade_name],
        ['CNPJ', registro.empresa.cnpj],
        ['Funcionario', registro.user.name],
        ['CPF/PIS', registro.user.pis_nis or registro.user.cpf or 'N/A'],
        ['NSR', str(registro.nsr)],
        ['Data/Hora', ts_local.strftime('%d/%m/%Y %H:%M:%S')],
        ['Tipo', registro.tipo.value.upper()],
        ['Local', local_nome],
        ['Geolocalizacao', geo_val],
        ['Suspeito', 'SIM' if registro.suspeito_geo else 'NAO'],
        # Hash exibido truncado para caber e ficar legível.
        ['Hash SHA-256', registro.hash_registro[:32] + '...'],
    ]

    # Larguras das colunas em centímetros.
    t = Table(dados, colWidths=[5 * cm, 12 * cm])
    # TableStyle = tuplas (propriedade, célula_inicial, célula_final, valor).
    # (0,0) é canto sup. esquerdo; (-1,-1) é canto inf. direito.
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),   # header escuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),       # texto do header branco
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),  # zebra
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # linhas internas
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # ---- Rodapé legal -----------------------------------------------
    story.append(Paragraph(
        f"Documento gerado em {ts_local.strftime('%d/%m/%Y %H:%M:%S')}. "
        "Este comprovante tem validade legal conforme art. 84 da Portaria MTP 671/2021.",
        styles['Normal']
    ))

    # build() escreve o PDF efetivo no buffer.
    doc.build(story)
    # getvalue() devolve os bytes — o caller (view) envia ao navegador.
    return buf.getvalue()
