# =====================================================================
# utils/banco_horas.py — Calculo de saldo de horas trabalhadas
# ---------------------------------------------------------------------
# Para cada dia do mes, soma os minutos trabalhados (pares ENTRADA/SAIDA)
# e compara com a jornada esperada do funcionario. O saldo do mes e a
# soma dos saldos diarios.
#
# Modelo simplificado:
#   - Jornada esperada por dia util = carga_semanal / 5
#   - Sabado e domingo = 0 esperado
#   - Sem jornada cadastrada -> assume 8h/dia (44h/5.5)
# =====================================================================

from datetime import date, datetime, timezone, timedelta
from calendar import monthrange
from typing import Optional, TypedDict

from E_Ponto.models.registro import Registro, TipoRegistro
from E_Ponto.models.jornada import Jornada


class SaldoDia(TypedDict):
    dia: date
    trabalhado_min: int
    esperado_min: int
    saldo_min: int
    eh_util: bool


class ResultadoMes(TypedDict):
    user_id: int
    ano: int
    mes: int
    dias: list[SaldoDia]
    total_trabalhado_min: int
    total_esperado_min: int
    total_saldo_min: int


def _esperado_minutos_por_dia(jornada: Optional[Jornada]) -> int:
    """Retorna minutos esperados em um dia util (segunda a sexta)."""
    if jornada and jornada.carga_horaria_semanal:
        # carga_horaria_semanal / 5 dias uteis * 60 minutos
        return int(float(jornada.carga_horaria_semanal) / 5 * 60)
    # Default 8h = 480 min
    return 480


def _minutos_trabalhados_no_dia(registros_do_dia: list[Registro]) -> int:
    """
    Soma os minutos entre pares ENTRADA -> SAIDA do dia.

    Ordena por timestamp e processa em sequencia: cada ENTRADA "abre"
    e cada SAIDA "fecha" um intervalo. Se houver entrada sem saida
    (esqueceu de bater), aquele bloco e ignorado.

    INCLUSAO e ALTERACAO sao tratadas como ENTRADA/SAIDA conforme o
    contexto — para simplicidade aqui sao ignoradas (so usamos
    ENTRADA e SAIDA puras).
    """
    pares = sorted(
        [r for r in registros_do_dia
         if r.tipo in (TipoRegistro.ENTRADA, TipoRegistro.SAIDA)],
        key=lambda r: r.timestamp_utc,
    )

    total_min = 0
    entrada: Optional[datetime] = None
    for r in pares:
        if r.tipo == TipoRegistro.ENTRADA and entrada is None:
            entrada = r.timestamp_utc
        elif r.tipo == TipoRegistro.SAIDA and entrada is not None:
            delta = r.timestamp_utc - entrada
            total_min += int(delta.total_seconds() // 60)
            entrada = None
        # Outros casos (ex.: duas ENTRADAs seguidas) sao silenciosamente
        # ignorados — o ultimo "abre" e o que vale.

    return total_min


def calcular_saldo_mes(
    user_id: int,
    empresa_id: int,
    ano: int,
    mes: int,
    jornada: Optional[Jornada] = None,
) -> ResultadoMes:
    """
    Monta o relatorio do mes para o funcionario.

    Parametros:
        user_id, empresa_id    Filtra registros do funcionario na empresa.
        ano, mes               Mes alvo (ex.: 2026, 5).
        jornada                Jornada do funcionario (opcional — se
                               None, assume 8h/dia util).
    """
    # Limites do mes em UTC.
    primeiro = datetime(ano, mes, 1, tzinfo=timezone.utc)
    _, ultimo_dia_num = monthrange(ano, mes)
    ultimo = datetime(ano, mes, ultimo_dia_num, 23, 59, 59, tzinfo=timezone.utc)

    registros = (Registro.query
                 .filter(Registro.user_id == user_id,
                         Registro.empresa_id == empresa_id,
                         Registro.timestamp_utc >= primeiro,
                         Registro.timestamp_utc <= ultimo)
                 .order_by(Registro.timestamp_utc)
                 .all())

    # Agrupa por dia (em horario local — usa a tz do servidor).
    por_dia: dict[date, list[Registro]] = {}
    for r in registros:
        d = r.timestamp_utc.astimezone().date()
        por_dia.setdefault(d, []).append(r)

    esperado_por_util = _esperado_minutos_por_dia(jornada)

    dias: list[SaldoDia] = []
    total_trabalhado = 0
    total_esperado = 0

    for dia_num in range(1, ultimo_dia_num + 1):
        d = date(ano, mes, dia_num)
        eh_util = d.weekday() < 5  # 0=segunda, 4=sexta
        trabalhado = _minutos_trabalhados_no_dia(por_dia.get(d, []))
        esperado = esperado_por_util if eh_util else 0
        saldo = trabalhado - esperado

        dias.append({
            'dia': d,
            'trabalhado_min': trabalhado,
            'esperado_min': esperado,
            'saldo_min': saldo,
            'eh_util': eh_util,
        })
        total_trabalhado += trabalhado
        total_esperado += esperado

    return {
        'user_id': user_id,
        'ano': ano,
        'mes': mes,
        'dias': dias,
        'total_trabalhado_min': total_trabalhado,
        'total_esperado_min': total_esperado,
        'total_saldo_min': total_trabalhado - total_esperado,
    }


def format_min(minutos: int) -> str:
    """Formata minutos como 'HH:MM' (negativo vira '-HH:MM')."""
    sinal = '-' if minutos < 0 else ''
    m = abs(minutos)
    return f"{sinal}{m // 60:02d}:{m % 60:02d}"
