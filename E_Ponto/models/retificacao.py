# =====================================================================
# models/retificacao.py — Pedido de correção de ponto
# ---------------------------------------------------------------------
# Quando o funcionário esquece de bater o ponto ou bate um horário
# errado, ele abre uma retificação. O RH analisa e aprova ou rejeita.
#
# Não alteramos o Registro original — para manter a auditoria,
# criamos um novo registro tipo ALTERACAO se a retificação for
# aprovada.
# =====================================================================

import enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .registro import Registro
    from .user import User


# Enum dos possíveis status de uma retificação.
class StatusRetificacao(enum.Enum):
    PENDENTE = "pendente"     # Aguardando análise do RH
    APROVADA = "aprovada"     # RH aceitou; novo Registro foi criado
    REJEITADA = "rejeitada"   # RH negou; Registro original permanece


class Retificacao(db.Model):
    __tablename__ = "retificacoes"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Qual registro o funcionário quer corrigir.
    registro_id: Mapped[int] = mapped_column(db.ForeignKey("registros.id"), nullable=False, index=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Quem pediu (geralmente o próprio dono do registro).
    solicitante_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    # Horário proposto. None se for um pedido de remoção/observação.
    novo_timestamp: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)
    # Explicação obrigatória — sai no relatório de auditoria.
    motivo: Mapped[str] = mapped_column(db.String(500), nullable=False)

    status: Mapped[StatusRetificacao] = mapped_column(
        db.Enum(StatusRetificacao), nullable=False, default=StatusRetificacao.PENDENTE
    )
    # Quem decidiu (membro do RH).
    aprovador_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    # Resposta opcional do RH (ex.: "Aprovado — confirmado com gerente").
    observacao_aprovador: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )
    # Marca quando o RH decidiu — None = ainda pendente.
    aprovado_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True), nullable=True)

    # Relacionamentos com foreign_keys explícito (mesma situação do Registro:
    # duas FKs apontando para users.id).
    registro: Mapped["Registro"] = relationship("Registro")
    solicitante: Mapped["User"] = relationship("User", foreign_keys=[solicitante_id])
    aprovador: Mapped[Optional["User"]] = relationship("User", foreign_keys=[aprovador_id])

    def __repr__(self) -> str:
        return f"<Retificacao id={self.id} status={self.status.value}>"
