# =====================================================================
# models/role_user.py — Tabela de associação User <-> Role
# ---------------------------------------------------------------------
# É o "núcleo" do modelo de permissões do sistema. Cada linha aqui diz:
#     "O usuário X tem o papel Y dentro da empresa Z (com nível W)."
#
# É uma tabela de muitos-para-muitos enriquecida: além de ligar User
# a Role, também carrega contexto (Business e Level) e datas de
# vigência (created_at / finished_at).
# =====================================================================

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, UniqueConstraint

from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .role import Role
    from .user import User
    from .business import Business
    from .level import Level


# === Associação entre usuário, papel e empresa ===
class RoleUser(db.Model):
    __tablename__ = "roles_has_users"
    __table_args__ = (
        # Garante que não exista a mesma combinação (user, role, business)
        # duplicada — ex.: não pode haver dois "Roberto admin da Padaria X".
        UniqueConstraint(
            "user_id",
            "role_id",
            "business_id",
            name="uq_user_role_business"
        ),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Foreign keys: cada coluna aponta para a PK da tabela respectiva.
    role_id: Mapped[int] = mapped_column(db.ForeignKey("roles.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    # business_id é opcional: papel "admin do sistema" pode não estar
    # vinculado a uma empresa específica.
    business_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("businesses.id"), nullable=True, index=True)
    level_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("levels.id"), nullable=True)
    # Data de criação do vínculo.
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Quando preenchido, indica que o vínculo terminou (ex.: demissão).
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))

    # ---- Relacionamentos (ORM) --------------------------------------
    # Permitem navegar entre objetos: role_user.role, role_user.user, etc.
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="role_associations"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="role_associations"
    )
    business: Mapped[Optional["Business"]] = relationship(
        "Business",
        back_populates="role_associations"
    )
    level: Mapped[Optional["Level"]] = relationship(
        "Level",
        back_populates="role_associations"
    )

    def __repr__(self) -> str:
        return (
            f"<RoleUser(user_id={self.user_id}, role_id={self.role_id}, business_id={self.business_id})>"
        )
