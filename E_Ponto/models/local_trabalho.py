"""Modelo LocalTrabalho: endereco fisico onde o ponto pode ser batido.

Uma empresa pode ter varios locais (matriz, filial, obra). Os campos de
latitude/longitude/raio_metros permitem validar a geolocalizacao da batida.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, Numeric
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .business import Business


class LocalTrabalho(db.Model):
    __tablename__ = "locais_trabalho"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(db.String(100), nullable=False)

    logradouro: Mapped[Optional[str]] = mapped_column(db.String(120))
    numero: Mapped[Optional[str]] = mapped_column(db.String(10))
    cidade: Mapped[Optional[str]] = mapped_column(db.String(60))
    uf: Mapped[Optional[str]] = mapped_column(db.String(2))
    cep: Mapped[Optional[str]] = mapped_column(db.String(10))

    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    # Raio (m) ao redor do ponto para aceitar a batida
    raio_metros: Mapped[int] = mapped_column(db.Integer, default=200, nullable=False)

    ativo: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    empresa: Mapped["Business"] = relationship("Business", back_populates="locais_trabalho")

    def __repr__(self) -> str:
        return f"<LocalTrabalho {self.nome}>"
