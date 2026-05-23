# =====================================================================
# utils/aej.py — Gerador do Arquivo Eletrônico de Jornada (AEJ)
# ---------------------------------------------------------------------
# AEJ é um relatório mensal por funcionário, listando as batidas
# de cada dia e a quantidade de horas trabalhadas. Também é
# definido pela Portaria 671/2021 (anexo II).
# =====================================================================

from io import StringIO
from E_Ponto.utils.clt import calcular_horas_trabalhadas


def gerar_aej(empresa, funcionarios_registros, periodo) -> str:
    """
    Generate AEJ (Arquivo Eletronico de Jornada) for Portaria 671/2021 Annex II.

    funcionarios_registros: list of (user, [registros ordenados por timestamp])
    periodo: string "YYYY-MM"
    """
    buf = StringIO()

    cnpj_limpo = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '')

    # ---- Tipo 1 - Header (uma vez por arquivo) ----------------------
    # Notação {var:<N} = alinha à esquerda preenchendo até N chars.
    buf.write(f"1{cnpj_limpo:<14}{empresa.trade_name:<150}{periodo}\r\n")

    # Itera por funcionário.
    for user, regs in funcionarios_registros:
        if not regs:
            continue

        # ---- Tipo 2 - Cabeçalho do funcionário ----------------------
        pis = user.pis_nis or user.cpf or ''
        buf.write(f"2{pis:<12}{user.name:<70}\r\n")

        # Agrupa batidas por dia: {date: [Registro, ...]}.
        por_dia = {}
        for reg in regs:
            d = reg.timestamp_utc.date()
            # setdefault: se a chave não existe, cria com []; em seguida appenda.
            por_dia.setdefault(d, []).append(reg)

        # Itera por dia em ordem cronológica.
        for dia, recs in sorted(por_dia.items()):
            timestamps = sorted([r.timestamp_utc for r in recs])
            # Primeira batida do dia = entrada; última = saída (simplificação).
            entrada = timestamps[0] if timestamps else None
            saida = timestamps[-1] if len(timestamps) > 1 else None

            horas = calcular_horas_trabalhadas(entrada, saida)
            # Converte timedelta -> horas e minutos (truncado).
            hh, mm = divmod(int(horas.total_seconds() // 60), 60)

            # Concatena até 6 marcações HHMM em uma única coluna.
            marcacoes = ''.join(ts.strftime('%H%M') for ts in timestamps[:6])

            # ---- Tipo 3 - Linha do dia ------------------------------
            # Formato: 3 + DDMMAAAA + marcações (24 chars) + HHH + MM
            buf.write(f"3{dia.strftime('%d%m%Y')}{marcacoes:<24}{hh:03d}{mm:02d}\r\n")

    # ---- Tipo 9 - Trailer simples -----------------------------------
    buf.write("9\r\n")
    return buf.getvalue()
