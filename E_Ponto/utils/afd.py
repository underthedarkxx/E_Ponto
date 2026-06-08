"""Gerador do Arquivo Fonte de Dados (AFD).

Arquivo-texto em formato de largura fixa exigido pelo Ministerio do
Trabalho (Portaria 671/2021) como prova das batidas. Cada linha comeca
com um tipo (1=header, 3=batida, 9=trailer). Layout simplificado.
"""

from datetime import datetime, timezone
from io import StringIO

from E_Ponto.utils.tz import to_local


def gerar_afd(empresa, registros, data_inicio, data_fim) -> str:
    """Gera o conteudo do AFD (string ASCII) para o periodo informado."""
    buf = StringIO()

    # Helpers de campo de tamanho fixo
    def pad_right(s, n, char=' '):
        s = str(s or '')
        return s[:n].ljust(n, char)

    def pad_left(s, n, char='0'):
        s = str(s or '')
        return s[:n].rjust(n, char)

    def linha(conteudo):
        # CRLF exigido pelo layout AFD
        buf.write(conteudo + '\r\n')

    agora = datetime.now(timezone.utc)
    cnpj_limpo = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '')

    # Tipo 1 - Header (empresa e periodo)
    linha(
        '1' +
        pad_left(cnpj_limpo, 14) +
        pad_left(empresa.cei_caepf or '', 12) +
        pad_right(empresa.trade_name, 150) +
        agora.strftime('%d%m%Y') +
        agora.strftime('%H%M%S') +
        data_inicio.strftime('%d%m%Y') +
        data_fim.strftime('%d%m%Y')
    )

    # Tipo 3 - Batidas (3 = entrada/inclusao, 4 = saida)
    tipo_map = {
        'entrada': '3',
        'retorno_almoco': '3',
        'saida_almoco': '4',
        'saida': '4',
        'inclusao': '3',
        'alteracao': '3',
    }
    for idx, reg in enumerate(registros, start=1):
        ts = to_local(reg.timestamp_utc)
        tipo_evento = tipo_map.get(reg.tipo.value, '3')
        pis = reg.user.pis_nis or reg.user.cpf or ''
        linha(
            '3' +
            pad_left(idx, 9) +
            ts.strftime('%d%m%Y') +
            ts.strftime('%H%M') +
            tipo_evento +
            pad_left(pis, 12) +
            pad_right(reg.hash_registro[:20], 20)
        )

    # Tipo 9 - Trailer (total de registros + padding)
    linha(
        '9' +
        pad_left(len(registros), 9) +
        pad_right('', 100)
    )

    return buf.getvalue()
