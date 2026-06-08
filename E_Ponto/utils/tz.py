"""Conversao de horarios UTC -> fuso local.

O app grava sempre em UTC, mas o SQLite devolve datetimes "naive". Tratar
todo valor naive como UTC antes de converter evita o erro de offset
(comprovante mostrando hora errada). Funciona em SQLite e PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Optional


def to_local(dt: Optional[datetime]) -> Optional[datetime]:
    """Converte um datetime (UTC) para o fuso local do servidor.

    Valores naive sao interpretados como UTC. Retorna None se dt for None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def fmt_local(dt: Optional[datetime], fmt: str = '%d/%m/%Y %H:%M:%S') -> str:
    """to_local + strftime — usado como filtro Jinja.

    Uso no template: {{ reg.timestamp_utc|localdt('%H:%M:%S') }}
    """
    local = to_local(dt)
    return local.strftime(fmt) if local else ''
