"""Geracao do PDF de comprovante de ponto (ReportLab).

Monta uma tabela com os campos exigidos pela Portaria 671/2021 (art. 81).
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


def gerar_comprovante(registro) -> bytes:
    """Gera o PDF de comprovante de uma batida de ponto."""
    buf = BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    styles = getSampleStyleSheet()
    story = []

    # Titulo
    story.append(Paragraph("COMPROVANTE DE REGISTRO DE PONTO", styles['Title']))
    story.append(Paragraph("REP-P — Portaria MTP no 671/2021", styles['Normal']))
    story.append(Spacer(1, 0.5 * cm))

    # Converte UTC -> horario local (ver utils/tz.py)
    from E_Ponto.utils.tz import to_local
    ts_local = to_local(registro.timestamp_utc)

    local_nome = registro.local_trabalho.nome if registro.local_trabalho else 'Nao informado'
    geo_val = (
        f"{registro.latitude}, {registro.longitude}"
        if registro.latitude else 'Nao coletada'
    )

    # Tabela de dados (primeira linha = cabecalho)
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
        ['Hash SHA-256', registro.hash_registro[:32] + '...'],
    ]

    t = Table(dados, colWidths=[5 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Rodape legal
    story.append(Paragraph(
        f"Documento gerado em {ts_local.strftime('%d/%m/%Y %H:%M:%S')}. "
        "Este comprovante tem validade legal conforme art. 84 da Portaria MTP 671/2021.",
        styles['Normal']
    ))

    doc.build(story)
    return buf.getvalue()
