"""Modelo Retificacao: pedido de correcao de ponto.

O funcionario abre uma retificacao e o RH aprova ou rejeita. O Registro
original nunca e alterado; quando aprovado, cria-se um novo registro
tipo ALTERACAO para preservar a auditoria.
"""

import enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .registro import Registro
    from .user import User


class StatusRetificacao(enum.Enum):
    PENDENTE = "pendente"
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class Retificacao(db.Model):
    __tablename__ = "retificacoes"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    registro_id: Mapped[int] = mapped_column(db.ForeignKey("registros.id"), nullable=False, index=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    solicitante_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    # Horario proposto; None para pedido de remocao/observacao
    novo_timestamp: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    # Obrigatorio — sai no relatorio de auditoria
    motivo: Mapped[str] = mapped_column(db.String(500), nullable=False)

    status: Mapped[StatusRetificacao] = mapped_column(
        db.Enum(StatusRetificacao), nullable=False, default=StatusRetificacao.PENDENTE
    )
    aprovador_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    observacao_aprovador: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )
    aprovado_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    # foreign_keys explicito: duas FKs apontando para users.id
    registro: Mapped["Registro"] = relationship("Registro")
    solicitante: Mapped["User"] = relationship("User", foreign_keys=[solicitante_id])
    aprovador: Mapped[Optional["User"]] = relationship("User", foreign_keys=[aprovador_id])

    def __repr__(self) -> str:
        return f"<Retificacao id={self.id} status={self.status.value}>"
