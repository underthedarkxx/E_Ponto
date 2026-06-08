"""Gerador do Arquivo Eletronico de Jornada (AEJ).

Relatorio mensal por funcionario com as batidas de cada dia e as horas
trabalhadas, conforme a Portaria 671/2021 (anexo II).
"""

from io import StringIO
from E_Ponto.utils.clt import calcular_horas_trabalhadas


def gerar_aej(empresa, funcionarios_registros, periodo) -> str:
    """Gera o conteudo do AEJ.

    funcionarios_registros: lista de (user, [registros ordenados por timestamp])
    periodo: string "YYYY-MM"
    """
    buf = StringIO()

    cnpj_limpo = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '')

    # Tipo 1 - Header (uma vez por arquivo)
    buf.write(f"1{cnpj_limpo:<14}{empresa.trade_name:<150}{periodo}\r\n")

    for user, regs in funcionarios_registros:
        if not regs:
            continue

        # Tipo 2 - Cabecalho do funcionario
        pis = user.pis_nis or user.cpf or ''
        buf.write(f"2{pis:<12}{user.name:<70}\r\n")

        # Agrupa batidas por dia
        por_dia = {}
        for reg in regs:
            d = reg.timestamp_utc.date()
            por_dia.setdefault(d, []).append(reg)

        for dia, recs in sorted(por_dia.items()):
            timestamps = sorted([r.timestamp_utc for r in recs])
            # Simplificacao: primeira batida = entrada, ultima = saida
            entrada = timestamps[0] if timestamps else None
            saida = timestamps[-1] if len(timestamps) > 1 else None

            horas = calcular_horas_trabalhadas(entrada, saida)
            hh, mm = divmod(int(horas.total_seconds() // 60), 60)

            marcacoes = ''.join(ts.strftime('%H%M') for ts in timestamps[:6])

            # Tipo 3 - Linha do dia
            buf.write(f"3{dia.strftime('%d%m%Y')}{marcacoes:<24}{hh:03d}{mm:02d}\r\n")

    # Tipo 9 - Trailer
    buf.write("9\r\n")
    return buf.getvalue()
