"""Calculo de saldo de horas, atrasos e faltas.

Para cada dia do mes soma os minutos trabalhados (pares ABRE/FECHA) e
compara com a jornada esperada, apurando atrasos e faltas. O saldo do
mes (banco de horas) e a soma dos saldos diarios.

Modelo simplificado:
- Esperado por dia util = carga_semanal / 5 (sem jornada, assume 8h/dia)
- Sabado/domingo = 0 esperado
"""

from datetime import date, datetime, timezone, time
from calendar import monthrange
from typing import Optional, TypedDict

from E_Ponto.models.registro import Registro, TIPOS_ENTRADA, TIPOS_SAIDA, TipoRegistro
from E_Ponto.models.jornada import Jornada
from E_Ponto.models.escala import EscalaFuncionario
from E_Ponto.utils.tz import to_local


class SaldoDia(TypedDict):
    dia: date
    trabalhado_min: int
    esperado_min: int
    saldo_min: int
    extra_min: int
    atraso_min: int
    falta: bool
    eh_util: bool
    pre_admissao: bool


class ResultadoMes(TypedDict):
    user_id: int
    ano: int
    mes: int
    dias: list[SaldoDia]
    total_trabalhado_min: int
    total_esperado_min: int
    total_saldo_min: int
    total_extra_min: int
    total_atraso_min: int
    total_faltas: int


def get_jornada_funcionario(
    user_id: int, empresa_id: int, ref: Optional[date] = None
) -> Optional[Jornada]:
    """Descobre a jornada vigente de um funcionario na empresa.

    Tenta a escala ativa do funcionario; sem escala, cai para a primeira
    jornada ativa da empresa.
    """
    ref = ref or date.today()
    escala = (EscalaFuncionario.query
              .filter(EscalaFuncionario.user_id == user_id,
                      EscalaFuncionario.empresa_id == empresa_id,
                      EscalaFuncionario.ativo.is_(True),
                      EscalaFuncionario.jornada_id.isnot(None),
                      EscalaFuncionario.data_inicio <= ref)
              .order_by(EscalaFuncionario.data_inicio.desc())
              .first())
    if escala and escala.jornada_id:
        # Respeita a vigencia: ignora escalas ja encerradas
        if escala.data_fim is None or escala.data_fim >= ref:
            return escala.jornada
    return Jornada.query.filter_by(empresa_id=empresa_id, ativo=True).first()


def _esperado_minutos_por_dia(jornada: Optional[Jornada]) -> int:
    """Minutos esperados em um dia util (segunda a sexta)."""
    if jornada and jornada.carga_horaria_semanal:
        return int(float(jornada.carga_horaria_semanal) / 5 * 60)
    return 480  # 8h


def _minutos_trabalhados_no_dia(registros_do_dia: list[Registro]) -> int:
    """Soma os minutos entre pares ABRE -> FECHA do dia.

    ENTRADA/RETORNO_ALMOCO abrem; SAIDA_ALMOCO/SAIDA fecham. Entrada sem
    saida correspondente e ignorada, assim como o intervalo de almoco.
    """
    pares = sorted(
        [r for r in registros_do_dia
         if r.tipo in (TIPOS_ENTRADA + TIPOS_SAIDA)],
        key=lambda r: r.timestamp_utc,
    )

    total_min = 0
    abertura: Optional[datetime] = None
    for r in pares:
        if r.tipo in TIPOS_ENTRADA and abertura is None:
            abertura = r.timestamp_utc
        elif r.tipo in TIPOS_SAIDA and abertura is not None:
            delta = r.timestamp_utc - abertura
            total_min += int(delta.total_seconds() // 60)
            abertura = None

    return total_min


def _minutos_do_horario(t: Optional[time]) -> Optional[int]:
    """Converte um datetime.time em minutos desde a meia-noite."""
    if t is None:
        return None
    return t.hour * 60 + t.minute


def _atraso_no_dia(registros_do_dia: list[Registro], jornada: Optional[Jornada]) -> int:
    """Minutos de atraso na ENTRADA do dia.

    Compara a primeira ENTRADA (local) com o horario contratual,
    descontando a tolerancia. Retorna 0 quando nao ha como apurar.
    """
    if not jornada or jornada.horario_entrada is None:
        return 0
    entradas = sorted(
        [r for r in registros_do_dia if r.tipo == TipoRegistro.ENTRADA],
        key=lambda r: r.timestamp_utc,
    )
    if not entradas:
        return 0

    primeira = to_local(entradas[0].timestamp_utc)
    minutos_entrada = primeira.hour * 60 + primeira.minute
    minutos_contratual = _minutos_do_horario(jornada.horario_entrada)
    if minutos_contratual is None:
        return 0
    tolerancia = jornada.tolerancia_minutos or 0
    atraso = minutos_entrada - minutos_contratual - tolerancia
    return atraso if atraso > 0 else 0


def calcular_saldo_mes(
    user_id: int,
    empresa_id: int,
    ano: int,
    mes: int,
    jornada: Optional[Jornada] = None,
    data_admissao: Optional[date] = None,
) -> ResultadoMes:
    """Monta o relatorio do mes para o funcionario.

    data_admissao: dias anteriores nao contam (sem esperado/falta). Se
    None, busca a do proprio User; sem ela, conta o mes inteiro.
    """
    if data_admissao is None:
        from E_Ponto.models.user import User
        u = User.query.get(user_id)
        data_admissao = u.data_admissao if u else None

    # Limites do mes em UTC
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

    # Agrupa por dia em horario local
    por_dia: dict[date, list[Registro]] = {}
    for r in registros:
        d = to_local(r.timestamp_utc).date()
        por_dia.setdefault(d, []).append(r)

    esperado_por_util = _esperado_minutos_por_dia(jornada)

    dias: list[SaldoDia] = []
    total_trabalhado = 0
    total_esperado = 0
    total_extra = 0
    total_atraso = 0
    total_faltas = 0

    hoje = date.today()
    for dia_num in range(1, ultimo_dia_num + 1):
        d = date(ano, mes, dia_num)
        # Dia anterior a admissao fica neutro (sem esperado/falta/atraso)
        pre_admissao = bool(data_admissao and d < data_admissao)
        eh_util = (d.weekday() < 5) and not pre_admissao
        regs_dia = por_dia.get(d, [])
        trabalhado = _minutos_trabalhados_no_dia(regs_dia)
        esperado = esperado_por_util if eh_util else 0
        saldo = trabalhado - esperado
        extra = saldo if saldo > 0 else 0
        atraso = 0 if pre_admissao else _atraso_no_dia(regs_dia, jornada)
        falta = bool(eh_util and not regs_dia and d <= hoje)

        dias.append({
            'dia': d,
            'trabalhado_min': trabalhado,
            'esperado_min': esperado,
            'saldo_min': saldo,
            'extra_min': extra,
            'atraso_min': atraso,
            'falta': falta,
            'eh_util': eh_util,
            'pre_admissao': pre_admissao,
        })
        total_trabalhado += trabalhado
        total_esperado += esperado
        total_extra += extra
        total_atraso += atraso
        if falta:
            total_faltas += 1

    return {
        'user_id': user_id,
        'ano': ano,
        'mes': mes,
        'dias': dias,
        'total_trabalhado_min': total_trabalhado,
        'total_esperado_min': total_esperado,
        'total_saldo_min': total_trabalhado - total_esperado,
        'total_extra_min': total_extra,
        'total_atraso_min': total_atraso,
        'total_faltas': total_faltas,
    }


def format_min(minutos: int) -> str:
    """Formata minutos como 'HH:MM' (negativo vira '-HH:MM')."""
    sinal = '-' if minutos < 0 else ''
    m = abs(minutos)
    return f"{sinal}{m // 60:02d}:{m % 60:02d}"
