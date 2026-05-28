# =====================================================================
# tests/test_calculos.py — Cálculo de horas trabalhadas, extras e atrasos
# Os horários são gravados em UTC e o conftest fixa TZ=UTC, então o
# horário local usado nos cálculos é igual ao UTC (determinístico).
# A jornada do funcionário (fixture `org`): 40h/semana = 8h/dia,
# entrada 08:00, tolerância 5 min.
# =====================================================================

from datetime import datetime, timezone, date


def _dt(h, m=0):
    """Datetime UTC em 04/03/2024 (segunda-feira, dia útil)."""
    return datetime(2024, 3, 4, h, m, tzinfo=timezone.utc)


def _saldo_do_dia(app, org):
    """Roda calcular_saldo_mes de março/2024 e devolve o dict do dia 04."""
    from E_Ponto.models.jornada import Jornada
    from E_Ponto.utils.banco_horas import calcular_saldo_mes
    with app.app_context():
        jornada = Jornada.query.get(org["jornada_id"])
        resultado = calcular_saldo_mes(org["func_id"], org["empresa_id"],
                                       2024, 3, jornada)
    return next(d for d in resultado["dias"] if d["dia"] == date(2024, 3, 4))


def test_horas_trabalhadas_jornada_cheia(app, org, criar_registro):
    """8h cheias (08-12 e 13-17) → 480 min trabalhados, saldo 0, sem extra."""
    criar_registro(org["func_id"], "entrada", _dt(8))
    criar_registro(org["func_id"], "saida_almoco", _dt(12))
    criar_registro(org["func_id"], "retorno_almoco", _dt(13))
    criar_registro(org["func_id"], "saida", _dt(17))

    dia = _saldo_do_dia(app, org)
    assert dia["trabalhado_min"] == 480
    assert dia["extra_min"] == 0
    assert dia["saldo_min"] == 0
    assert dia["atraso_min"] == 0


def test_horas_extras(app, org, criar_registro):
    """Saída às 18h (1h a mais) → 540 min, saldo +60, extra 60."""
    criar_registro(org["func_id"], "entrada", _dt(8))
    criar_registro(org["func_id"], "saida_almoco", _dt(12))
    criar_registro(org["func_id"], "retorno_almoco", _dt(13))
    criar_registro(org["func_id"], "saida", _dt(18))

    dia = _saldo_do_dia(app, org)
    assert dia["trabalhado_min"] == 540
    assert dia["extra_min"] == 60
    assert dia["saldo_min"] == 60


def test_atraso_na_entrada(app, org, criar_registro):
    """Entrada 08:30 (contratual 08:00, tolerância 5) → atraso de 25 min."""
    criar_registro(org["func_id"], "entrada", _dt(8, 30))
    criar_registro(org["func_id"], "saida_almoco", _dt(12))
    criar_registro(org["func_id"], "retorno_almoco", _dt(13))
    criar_registro(org["func_id"], "saida", _dt(17))

    dia = _saldo_do_dia(app, org)
    assert dia["atraso_min"] == 25
    # Trabalhou 30 min a menos que a jornada cheia.
    assert dia["trabalhado_min"] == 450


def test_entrada_dentro_da_tolerancia_sem_atraso(app, org, criar_registro):
    """Entrada 08:04 (dentro dos 5 min de tolerância) → sem atraso."""
    criar_registro(org["func_id"], "entrada", _dt(8, 4))
    criar_registro(org["func_id"], "saida", _dt(17))

    dia = _saldo_do_dia(app, org)
    assert dia["atraso_min"] == 0
