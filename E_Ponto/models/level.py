# =====================================================================
# models/level.py — Nível hierárquico do cargo
# ---------------------------------------------------------------------
# Diferente do Role (que é o "tipo" de acesso), o Level descreve o
# nível hierárquico dentro da empresa (ex.: "júnior", "pleno",
# "sênior", "gerente"). É um campo opcional na associação RoleUser.
# =====================================================================

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .role_user import RoleUser


# === Level (nível hierárquico) ===
class Level(db.Model):
    __tablename__ = "levels"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Nome do nível — único para evitar duplicatas como "Junior" e "junior".
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(db.String(255))
    # Permite desativar um nível sem perder o histórico.
    status: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    # Quais associações RoleUser referenciam este nível.
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="level"
    )

    def __repr__(self) -> str:
        return f"<Level {self.name}>"
