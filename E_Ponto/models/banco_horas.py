# =====================================================================
# models/banco_horas.py — Banco de horas mensal por funcionário
# ---------------------------------------------------------------------
# Mantém o saldo agregado de horas extras (positivo) e horas faltantes
# (negativo) de cada funcionário, mês a mês.
#
# Em vez de calcular tudo na hora a partir da tabela `registros`
# (que pode ter milhares de linhas), esse acumulado é atualizado
# periodicamente — é uma tabela de "snapshot" para fechamento de
# folha de pagamento.
# =====================================================================

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, UniqueConstraint
from E_Ponto.ext.db import db


class BancoHoras(db.Model):
    __tablename__ = "banco_horas"
    __table_args__ = (
        # Garante uma única linha por (usuário, empresa, mês).
        UniqueConstraint("user_id", "empresa_id", "periodo", name="uq_banco_horas_user_empresa_periodo"),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Período no formato "YYYY-MM" (ex.: "2025-11"). String evita
    # complicações com tipos DATE específicos do banco.
    periodo: Mapped[str] = mapped_column(db.String(7), nullable=False)
    # Acumuladores em minutos (inteiros são mais precisos que float).
    minutos_positivos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    minutos_negativos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    # Saldo = positivos - negativos. Pode ser negativo (deve horas).
    saldo_minutos: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    # Quando o RH fecha o mês, esta data é preenchida — depois disso
    # o saldo não muda mais (é congelado para a folha).
    fechado_em: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True), onupdate=func.now()
    )

    @property
    def saldo_formatado(self) -> str:
        """Retorna o saldo no formato humano: '5h 30m' ou '-2h 15m'."""
        total = abs(self.saldo_minutos)
        # divmod(min, 60) -> (horas, minutos restantes)
        horas, mins = divmod(total, 60)
        sinal = "-" if self.saldo_minutos < 0 else ""
        return f"{sinal}{horas}h {mins:02d}m"

    def __repr__(self) -> str:
        return f"<BancoHoras user_id={self.user_id} periodo={self.periodo} saldo={self.saldo_minutos}>"
