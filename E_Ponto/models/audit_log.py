"""Modelo AuditLog: registro de auditoria das acoes do sistema.

Guarda quem fez (user_id), em qual empresa, o que fez (acao) e onde
(tabela + registro_id), alem do estado antes/depois em JSON. Exigido por
lei em sistemas trabalhistas.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, Text
from E_Ponto.ext.db import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # NULL para acoes sem empresa especifica (ex.: criacao de conta)
    empresa_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("businesses.id"), nullable=True, index=True)
    # NULL para acoes automaticas/sistema
    user_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True, index=True)

    acao: Mapped[str] = mapped_column(db.String(50), nullable=False)
    tabela: Mapped[str] = mapped_column(db.String(50), nullable=False)
    registro_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Estado anterior e novo em JSON (Text porque pode crescer)
    dados_antes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dados_depois: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AuditLog acao={self.acao} tabela={self.tabela} id={self.registro_id}>"
