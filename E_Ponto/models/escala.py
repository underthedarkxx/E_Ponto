# =====================================================================
# models/escala.py — Atribuição de jornada a funcionário
# ---------------------------------------------------------------------
# "Liga" um funcionário (User) a uma jornada (Jornada) e um local
# (LocalTrabalho), dentro de uma empresa (Business), por um período
# (data_inicio até data_fim).
#
# Como o histórico é importante (alguém pode ter mudado de jornada
# duas vezes no ano), não apagamos escalas antigas — apenas fechamos
# definindo `data_fim` e/ou `ativo=False`.
# =====================================================================

from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, Date
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .business import Business
    from .jornada import Jornada
    from .local_trabalho import LocalTrabalho


class EscalaFuncionario(db.Model):
    __tablename__ = "escalas_funcionarios"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Jornada e local são opcionais para suportar alocações temporárias
    # sem horário/local definido ainda.
    jornada_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("jornadas.id"), nullable=True)
    local_trabalho_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("locais_trabalho.id"), nullable=True)

    # Vigência da escala (somente date, sem hora).
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    # data_fim=None significa "escala ainda vigente".
    data_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    ativo: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    # Relacionamentos — atalhos para navegar os objetos.
    user: Mapped["User"] = relationship("User")
    empresa: Mapped["Business"] = relationship("Business")
    jornada: Mapped[Optional["Jornada"]] = relationship("Jornada")
    local_trabalho: Mapped[Optional["LocalTrabalho"]] = relationship("LocalTrabalho")

    def __repr__(self) -> str:
        return f"<EscalaFuncionario user_id={self.user_id} empresa_id={self.empresa_id}>"
