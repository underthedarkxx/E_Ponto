# =====================================================================
# models/jornada.py — Jornada de trabalho (carga horária)
# ---------------------------------------------------------------------
# Define a estrutura de horário de trabalho que pode ser aplicada a
# um ou vários funcionários (via EscalaFuncionario). Ex.: "Padrão
# Comercial 8h-18h", "12x36 noturno", "6x1 com folga rotativa".
# =====================================================================

from typing import Optional, TYPE_CHECKING
from datetime import datetime, time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, Numeric, Time
from E_Ponto.ext.db import db


class Jornada(db.Model):
    __tablename__ = "jornadas"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Cada jornada é específica de uma empresa.
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(db.String(60), nullable=False)

    # Tipo da jornada — define como o sistema deve calcular horas:
    #   'padrao'   : entrada/saída fixas (ex.: 8h às 18h)
    #   '12x36'    : 12 horas trabalhando, 36 descansando
    #   '6x1'      : 6 dias trabalhando, 1 folga
    #   'flexivel' : sem horários fixos, só fecha pela carga semanal
    tipo: Mapped[str] = mapped_column(db.String(20), nullable=False, default='padrao')

    # Carga horária semanal (44h é o padrão CLT).
    carga_horaria_semanal: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), default=44)
    # Horários fixos — opcionais para jornadas flexíveis.
    horario_entrada: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    horario_saida: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    # Duração do intervalo de almoço (em minutos).
    intervalo_minutos: Mapped[int] = mapped_column(db.Integer, default=60, nullable=False)
    # Tolerância para atrasos sem desconto (CLT permite até 5 min na
    # entrada e 5 min na saída).
    tolerancia_minutos: Mapped[int] = mapped_column(db.Integer, default=5, nullable=False)

    ativo: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Jornada {self.nome}>"
