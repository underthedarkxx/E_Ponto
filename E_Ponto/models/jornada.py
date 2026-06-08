"""Modelo Jornada: estrutura de horario de trabalho.

Pode ser aplicada a um ou varios funcionarios via EscalaFuncionario
(ex.: "Padrao Comercial 8h-18h", "12x36 noturno").
"""

from typing import Optional
from datetime import datetime, time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, Numeric, Time
from E_Ponto.ext.db import db


class Jornada(db.Model):
    __tablename__ = "jornadas"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(db.String(60), nullable=False)

    # Define como calcular horas: 'padrao', '12x36', '6x1' ou 'flexivel'
    tipo: Mapped[str] = mapped_column(db.String(20), nullable=False, default='padrao')

    # Carga horaria semanal (44h e o padrao CLT)
    carga_horaria_semanal: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), default=44)
    # Horarios fixos — opcionais para jornadas flexiveis
    horario_entrada: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    horario_saida: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    intervalo_minutos: Mapped[int] = mapped_column(db.Integer, default=60, nullable=False)
    # Tolerancia para atrasos sem desconto (CLT permite ate 5 min)
    tolerancia_minutos: Mapped[int] = mapped_column(db.Integer, default=5, nullable=False)

    ativo: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Jornada {self.nome}>"
