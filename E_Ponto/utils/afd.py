# =====================================================================
# utils/afd.py — Gerador do Arquivo Fonte de Dados (AFD)
# ---------------------------------------------------------------------
# AFD é o arquivo TEXTO em formato fixo (sem separadores; tamanhos
# definidos coluna a coluna) que o Ministério do Trabalho exige
# como prova das batidas de ponto. Cada linha começa com um "tipo"
# (1, 3 ou 9) que indica o que vem em seguida.
#
# Layout simplificado aqui, focando nos campos essenciais. O layout
# oficial completo está na Portaria 671/2021.
# =====================================================================

from datetime import datetime, timezone
from io import StringIO

from E_Ponto.utils.tz import to_local


def gerar_afd(empresa, registros, data_inicio, data_fim) -> str:
    """
    Generate AFD (Arquivo Fonte de Dados) in the fixed format required by Portaria 671/2021.
    Returns ASCII string content.
    """
    # StringIO funciona como um arquivo em memória — eficiente para
    # construir strings grandes (evita concatenações que copiam o conteúdo).
    buf = StringIO()

    # --- Helpers para campos de tamanho fixo -------------------------
    def pad_right(s, n, char=' '):
        """Preenche à direita com `char` para chegar em n caracteres
        (e trunca se já for maior)."""
        s = str(s or '')
        return s[:n].ljust(n, char)

    def pad_left(s, n, char='0'):
        """Preenche à esquerda com `char` (geralmente zeros)."""
        s = str(s or '')
        return s[:n].rjust(n, char)

    def linha(conteudo):
        """Adiciona uma linha terminada com CRLF (\\r\\n) — formato
        de arquivos texto Windows, exigido pelo layout AFD."""
        buf.write(conteudo + '\r\n')

    agora = datetime.now(timezone.utc)
    # CNPJ no AFD vai sem pontuação.
    cnpj_limpo = (empresa.cnpj or '').replace('.', '').replace('/', '').replace('-', '')

    # ---- Tipo 1 - Header --------------------------------------------
    # Identifica a empresa e o período abrangido pelo arquivo.
    linha(
        '1' +
        pad_left(cnpj_limpo, 14) +
        pad_left(empresa.cei_caepf or '', 12) +
        pad_right(empresa.trade_name, 150) +
        agora.strftime('%d%m%Y') +    # data da geração
        agora.strftime('%H%M%S') +    # hora da geração
        data_inicio.strftime('%d%m%Y') +
        data_fim.strftime('%d%m%Y')
    )

    # ---- Tipo 3 - Records (batidas de ponto) ------------------------
    # O AFD diferencia: 3 = entrada/inclusão, 4 = saída.
    tipo_map = {
        'entrada': '3',
        'retorno_almoco': '3',
        'saida_almoco': '4',
        'saida': '4',
        'inclusao': '3',
        'alteracao': '3',
    }
    for idx, reg in enumerate(registros, start=1):
        # Converte UTC -> timezone local (definido pelo SO). to_local
        # trata valores "naive" do SQLite como UTC (ver utils/tz.py).
        ts = to_local(reg.timestamp_utc)
        tipo_evento = tipo_map.get(reg.tipo.value, '3')
        pis = reg.user.pis_nis or reg.user.cpf or ''
        linha(
            '3' +
            pad_left(idx, 9) +            # NSR sequencial dentro do arquivo
            ts.strftime('%d%m%Y') +
            ts.strftime('%H%M') +
            tipo_evento +
            pad_left(pis, 12) +
            pad_right(reg.hash_registro[:20], 20)  # hash truncado
        )

    # ---- Tipo 9 - Trailer (fim do arquivo) --------------------------
    # Total de registros e padding final.
    linha(
        '9' +
        pad_left(len(registros), 9) +
        pad_right('', 100)
    )

    return buf.getvalue()
