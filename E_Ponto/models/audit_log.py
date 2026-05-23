# =====================================================================
# models/audit_log.py — Log de auditoria
# ---------------------------------------------------------------------
# Registra TODAS as ações relevantes no sistema (criação, alteração,
# exclusão, login, etc.). Em sistemas trabalhistas isso é exigido
# por lei para que se prove quem mudou o quê.
#
# Cada linha guarda:
#   - quem fez (user_id), em qual empresa (empresa_id);
#   - o que fez (acao) e onde (tabela + registro_id);
#   - como estava antes (dados_antes) e como ficou (dados_depois),
#     ambos em JSON serializado (Text).
# =====================================================================

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import func, Text
from E_Ponto.ext.db import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Pode ser NULL para ações que não pertencem a uma empresa
    # específica (ex.: criação de conta).
    empresa_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("businesses.id"), nullable=True, index=True)
    # Pode ser NULL para ações automáticas/sistema.
    user_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True, index=True)

    # Nome da ação (ex.: "CRIAR_REGISTRO", "APROVAR_RETIFICACAO").
    acao: Mapped[str] = mapped_column(db.String(50), nullable=False)
    # Tabela do banco afetada (ex.: "registros", "users").
    tabela: Mapped[str] = mapped_column(db.String(50), nullable=False)
    # ID da linha afetada na tabela acima.
    registro_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # JSON com o estado anterior e o novo. Text porque pode crescer.
    dados_antes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dados_depois: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # IP de quem fez a ação (IPv6 cabe em 45 chars).
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AuditLog acao={self.acao} tabela={self.tabela} id={self.registro_id}>"
