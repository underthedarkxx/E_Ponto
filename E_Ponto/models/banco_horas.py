"""Modelo BancoHoras: saldo mensal de horas por funcionario.

Snapshot agregado de horas extras (positivo) e faltantes (negativo),
atualizado periodicamente para o fechamento de folha — evita recalcular
tudo a partir da tabela de registros.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, UniqueConstraint
from E_Ponto.ext.db import db


class BancoHoras(db.Model):
    __tablename__ = "banco_horas"
    __table_args__ = (
        # Uma unica linha por (usuario, empresa, mes)
        UniqueConstraint("user_id", "empresa_id", "periodo", name="uq_banco_horas_user_empresa_periodo"),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Periodo no formato "YYYY-MM" (ex.: "2025-11")
    periodo: Mapped[str] = mapped_column(db.String(7), nullable=False)
    # Acumuladores em minutos
    minutos_positivos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    minutos_negativos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    saldo_minutos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    # Preenchido quando o RH fecha o mes; depois disso o saldo e congelado
    fechado_em: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True), onupdate=func.now()
    )

    @property
    def saldo_formatado(self) -> str:
        """Retorna o saldo no formato humano: '5h 30m' ou '-2h 15m'."""
        total = abs(self.saldo_minutos)
        horas, mins = divmod(total, 60)
        sinal = "-" if self.saldo_minutos < 0 else ""
        return f"{sinal}{horas}h {mins:02d}m"

    def __repr__(self) -> str:
        return f"<BancoHoras user_id={self.user_id} periodo={self.periodo} saldo={self.saldo_minutos}>"
