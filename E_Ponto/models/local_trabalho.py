# =====================================================================
# models/local_trabalho.py — Local físico de trabalho
# ---------------------------------------------------------------------
# Representa um endereço onde o funcionário pode bater o ponto.
# Uma mesma empresa pode ter vários locais (matriz, filial, obra...).
#
# Os campos de latitude/longitude/raio_metros permitem validar
# geolocalização: o ponto só é aceito se o funcionário estiver
# dentro do raio definido a partir do ponto cadastrado.
# =====================================================================

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
    # A qual empresa este local pertence.
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Apelido visível ao usuário (ex.: "Matriz Centro").
    nome: Mapped[str] = mapped_column(db.String(100), nullable=False)

    # Endereço descritivo (também aparece em relatórios).
    logradouro: Mapped[Optional[str]] = mapped_column(db.String(120))
    numero: Mapped[Optional[str]] = mapped_column(db.String(10))
    cidade: Mapped[Optional[str]] = mapped_column(db.String(60))
    uf: Mapped[Optional[str]] = mapped_column(db.String(2))
    cep: Mapped[Optional[str]] = mapped_column(db.String(10))

    # Numeric(10, 7) = até 10 dígitos, sendo 7 decimais.
    # Precisão de ~1 cm — suficiente para geofencing.
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    # Raio (em metros) ao redor do ponto para aceitar a batida.
    # 200m é um bom valor para cobrir o prédio inteiro mesmo com erro
    # do GPS.
    raio_metros: Mapped[int] = mapped_column(db.Integer, default=200, nullable=False)

    # Permite desativar um local sem perder o histórico.
    ativo: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    # Relacionamento inverso: empresa.locais_trabalho.
    empresa: Mapped["Business"] = relationship("Business", back_populates="locais_trabalho")

    def __repr__(self) -> str:
        return f"<LocalTrabalho {self.nome}>"
