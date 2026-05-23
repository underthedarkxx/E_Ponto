# =====================================================================
# models/role.py — Papel (perfil de acesso) do usuário
# ---------------------------------------------------------------------
# Exemplos de Roles no sistema: "admin", "rh", "funcionario".
# Cada usuário pode ter mais de um papel — a ligação User<->Role é
# feita pela tabela intermediária RoleUser (que também guarda a
# empresa em que esse papel vale).
# =====================================================================

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .role_user import RoleUser


# === Role (papel) ===
class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Nome único para identificar o papel — usado em checagens tipo
    # `if "admin" in current_user.roles`.
    name: Mapped[str] = mapped_column(db.String(30), unique=True, index=True)
    # Permite desativar um papel sem apagá-lo.
    status: Mapped[bool] = mapped_column(db.Boolean, default=True)

    # Lista de associações que apontam para este papel.
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
