"""Modelo User: qualquer pessoa que faz login (funcionario, RH ou admin).

O papel (Role) e a empresa do usuario sao definidos pela tabela RoleUser.
"""

from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from flask_login import UserMixin
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .role_user import RoleUser
    from .location import Address


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    # Identificacao
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), index=True)
    email: Mapped[str] = mapped_column(db.String(100), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(15))
    cargo: Mapped[Optional[str]] = mapped_column(db.String(80))
    # A partir da data de admissao o funcionario passa a contar ponto;
    # dias anteriores nao geram falta nem horas esperadas (ver utils/banco_horas.py).
    data_admissao: Mapped[Optional[date]] = mapped_column(db.Date)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    photo: Mapped[Optional[str]] = mapped_column(db.String(100))

    # Autenticacao (password e Optional: login social pode nao ter senha)
    password: Mapped[Optional[str]] = mapped_column(db.String(255))
    google_id: Mapped[Optional[str]] = mapped_column(db.String(255))
    facebook_id: Mapped[Optional[str]] = mapped_column(db.String(255))

    # Documentos brasileiros (pis_nis exigido pela legislacao do ponto)
    cpf: Mapped[Optional[str]] = mapped_column(db.String(15), index=True)
    pis_nis: Mapped[Optional[str]] = mapped_column(db.String(15), index=True)

    # Autenticacao de dois fatores (TOTP)
    totp_secret: Mapped[Optional[str]] = mapped_column(db.String(64))
    two_factor_enabled: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True),
        onupdate=func.now()
    )

    # Soft-delete: usuarios inativos sao marcados, nao apagados
    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # Relacionamentos
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    @property
    def roles(self):
        """Lista os Role(s) do usuario, ignorando associacoes sem role."""
        return [assoc.role for assoc in self.role_associations if assoc.role]

    def get_id(self):
        """Flask-Login espera uma string como ID na sessao."""
        return str(self.id)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
