"""Modelo RoleUser: associacao User <-> Role (nucleo de permissoes).

Cada linha diz "o usuario X tem o papel Y na empresa Z (com nivel W)".
E uma tabela muitos-para-muitos enriquecida com contexto (Business, Level)
e datas de vigencia (created_at / finished_at).
"""

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


class RoleUser(db.Model):
    __tablename__ = "roles_has_users"
    __table_args__ = (
        # Impede combinacao (user, role, business) duplicada
        UniqueConstraint(
            "user_id",
            "role_id",
            "business_id",
            name="uq_user_role_business"
        ),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(db.ForeignKey("roles.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    # Opcional: papel "admin do sistema" pode nao ter empresa
    business_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("businesses.id"), nullable=True, index=True)
    level_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("levels.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Preenchido quando o vinculo termina (ex.: demissao)
    finished_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))

    # Relacionamentos
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
