# =====================================================================
# utils/tz.py — Conversao de horarios UTC -> fuso local
# ---------------------------------------------------------------------
# O app SEMPRE grava os timestamps em UTC. O problema: o SQLite nao
# armazena o fuso horario, entao ao ler de volta o valor volta "naive"
# (tzinfo=None). Se chamarmos .astimezone() direto num datetime naive,
# o Python ASSUME que ele ja esta no fuso local e NAO aplica o offset —
# era o bug das "3 horas a mais" no comprovante (mostrava 23h em vez de
# 20h no horario de Brasilia, UTC-3).
#
# A solucao e tratar todo valor naive como UTC antes de converter.
# Funciona tanto no SQLite (naive) quanto no PostgreSQL (aware).
# =====================================================================

from datetime import datetime, timezone
from typing import Optional


def to_local(dt: Optional[datetime]) -> Optional[datetime]:
    """Converte um datetime (UTC) para o fuso local do servidor.

    Valores "naive" (sem tzinfo) sao interpretados como UTC, pois o app
    sempre grava em UTC. Retorna None se a entrada for None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def fmt_local(dt: Optional[datetime], fmt: str = '%d/%m/%Y %H:%M:%S') -> str:
    """to_local + strftime numa tacada so — usado como filtro Jinja.

    Uso no template: {{ reg.timestamp_utc|localdt('%H:%M:%S') }}
    """
    local = to_local(dt)
    return local.strftime(fmt) if local else ''
