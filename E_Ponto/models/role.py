"""Modelo Role: papel de acesso do usuario (ex.: admin, rh, funcionario).

A ligacao User <-> Role e feita pela tabela RoleUser, que tambem guarda
a empresa em que o papel vale.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .role_user import RoleUser


class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, index=True)
    status: Mapped[bool] = mapped_column(db.Boolean, default=True)

    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
