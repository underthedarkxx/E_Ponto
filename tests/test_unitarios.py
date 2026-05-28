# =====================================================================
# tests/test_unitarios.py — Testes UNITÁRIOS (funções puras)
# Exercitam a lógica isolada (sem HTTP, sem banco): cálculo de
# distância/geofence, hash em cadeia, minutos trabalhados, atraso,
# formatação e conversão de fuso. Usamos objetos "dublê"
# (SimpleNamespace) no lugar dos modelos do ORM.
# =====================================================================

from types import SimpleNamespace
from datetime import datetime, timezone, time

from E_Ponto.utils.geo import haversine, verificar_geofence
from E_Ponto.utils.hashing import calcular_hash, verificar_integridade
from E_Ponto.utils.banco_horas import (
    format_min, _minutos_trabalhados_no_dia, _atraso_no_dia)
from E_Ponto.utils.tz import to_local, fmt_local
from E_Ponto.models.registro import TipoRegistro


# --------------------------- haversine -------------------------------
def test_haversine_mesmo_ponto_e_zero():
    assert haversine(-20.34, -40.29, -20.34, -40.29) == 0


def test_haversine_um_grau_de_latitude():
    """1° de latitude ≈ 111 km (tolerância de 1 km)."""
    d = haversine(0, 0, 1, 0)
    assert abs(d - 111_195) < 1000


# --------------------------- geofence --------------------------------
def _local(lat, lon, raio):
    return SimpleNamespace(latitude=lat, longitude=lon, raio_metros=raio)


def test_geofence_dentro_do_raio():
    dentro, dist = verificar_geofence(-20.34, -40.29, _local(-20.34, -40.29, 200))
    assert dentro is True
    assert dist < 1


def test_geofence_fora_do_raio():
    # ~1 km ao norte → fora de um raio de 200 m.
    dentro, dist = verificar_geofence(-20.331, -40.29, _local(-20.34, -40.29, 200))
    assert dentro is False
    assert dist > 200


def test_geofence_sem_local_e_permissivo():
    """Sem local (None) não há como julgar → considera dentro."""
    dentro, dist = verificar_geofence(-20.34, -40.29, None)
    assert dentro is True


def test_geofence_local_sem_coordenadas():
    dentro, _ = verificar_geofence(-20.34, -40.29, _local(None, None, 200))
    assert dentro is True


# --------------------------- hash chain ------------------------------
def test_hash_e_deterministico_e_64_hex():
    h1 = calcular_hash(1, "00000000000000", "111", "2026-05-20T08:00:00", "entrada", None)
    h2 = calcular_hash(1, "00000000000000", "111", "2026-05-20T08:00:00", "entrada", None)
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_hash_muda_com_qualquer_campo():
    base = calcular_hash(1, "cnpj", "111", "2026-05-20T08:00:00", "entrada", None)
    assert base != calcular_hash(2, "cnpj", "111", "2026-05-20T08:00:00", "entrada", None)
    assert base != calcular_hash(1, "cnpj", "111", "2026-05-20T09:00:00", "entrada", None)
    assert base != calcular_hash(1, "cnpj", "111", "2026-05-20T08:00:00", "saida", None)


def _reg_falso(nsr, ts, tipo, hash_anterior):
    """Monta um registro-dublê com hash JÁ calculado (cadeia válida)."""
    cnpj, pis = "00000000000000", "11111111111"
    h = calcular_hash(nsr, cnpj, pis, ts.isoformat(), tipo.value, hash_anterior)
    return SimpleNamespace(
        nsr=nsr, timestamp_utc=ts, tipo=tipo, hash_registro=h,
        hash_anterior=hash_anterior,
        empresa=SimpleNamespace(cnpj=cnpj),
        user=SimpleNamespace(pis_nis=pis, cpf=None))


def test_integridade_cadeia_valida():
    r1 = _reg_falso(1, datetime(2026, 5, 20, 8, tzinfo=timezone.utc),
                    TipoRegistro.ENTRADA, None)
    r2 = _reg_falso(2, datetime(2026, 5, 20, 17, tzinfo=timezone.utc),
                    TipoRegistro.SAIDA, r1.hash_registro)
    resultado = verificar_integridade([r1, r2])
    assert all(ok for _, ok in resultado)


def test_integridade_detecta_adulteracao():
    """Se alguém altera o horário de um registro sem refazer o hash,
    a verificação acusa que a cadeia foi quebrada."""
    r1 = _reg_falso(1, datetime(2026, 5, 20, 8, tzinfo=timezone.utc),
                    TipoRegistro.ENTRADA, None)
    r2 = _reg_falso(2, datetime(2026, 5, 20, 17, tzinfo=timezone.utc),
                    TipoRegistro.SAIDA, r1.hash_registro)
    # Adultera o horário do r1 SEM recalcular o hash dele.
    r1.timestamp_utc = datetime(2026, 5, 20, 7, tzinfo=timezone.utc)
    resultado = dict((r.nsr, ok) for r, ok in verificar_integridade([r1, r2]))
    assert resultado[1] is False        # registro adulterado é detectado


# --------------------- minutos trabalhados ---------------------------
def _r(tipo, h, m=0):
    return SimpleNamespace(tipo=tipo,
                           timestamp_utc=datetime(2026, 5, 20, h, m, tzinfo=timezone.utc))


def test_minutos_trabalhados_jornada_cheia():
    regs = [_r(TipoRegistro.ENTRADA, 8), _r(TipoRegistro.SAIDA_ALMOCO, 12),
            _r(TipoRegistro.RETORNO_ALMOCO, 13), _r(TipoRegistro.SAIDA, 17)]
    assert _minutos_trabalhados_no_dia(regs) == 480


def test_minutos_ignora_entrada_sem_saida():
    """Entrada sem saída correspondente não conta minutos."""
    regs = [_r(TipoRegistro.ENTRADA, 8)]
    assert _minutos_trabalhados_no_dia(regs) == 0


# --------------------------- atraso ----------------------------------
def test_atraso_calculado_com_tolerancia():
    jornada = SimpleNamespace(horario_entrada=time(8, 0), tolerancia_minutos=5)
    regs = [_r(TipoRegistro.ENTRADA, 8, 30)]      # 30 min atrasado
    assert _atraso_no_dia(regs, jornada) == 25     # menos 5 de tolerância


def test_sem_atraso_dentro_da_tolerancia():
    jornada = SimpleNamespace(horario_entrada=time(8, 0), tolerancia_minutos=5)
    regs = [_r(TipoRegistro.ENTRADA, 8, 4)]
    assert _atraso_no_dia(regs, jornada) == 0


def test_sem_jornada_nao_ha_atraso():
    assert _atraso_no_dia([_r(TipoRegistro.ENTRADA, 9)], None) == 0


# --------------------------- format_min ------------------------------
def test_format_min():
    assert format_min(0) == "00:00"
    assert format_min(90) == "01:30"
    assert format_min(480) == "08:00"
    assert format_min(-60) == "-01:00"


# --------------------------- timezone --------------------------------
def test_to_local_trata_naive_como_utc():
    """Datetime sem tzinfo é assumido como UTC (com TZ=UTC do conftest,
    o horário local resultante é igual)."""
    dt = datetime(2026, 5, 20, 8, 0)            # naive
    local = to_local(dt)
    assert local.hour == 8


def test_fmt_local_formata():
    dt = datetime(2026, 5, 20, 8, 30, tzinfo=timezone.utc)
    assert fmt_local(dt, '%d/%m/%Y %H:%M') == "20/05/2026 08:30"


def test_to_local_none():
    assert to_local(None) is None
