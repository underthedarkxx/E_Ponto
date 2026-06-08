"""Modelo Business: empresa/estabelecimento que usa o E-Ponto.

Cada empresa tem um dono (User), funcionarios (via RoleUser), locais de
trabalho e registros de ponto. Os campos REP-P sao exigidos pela
Portaria 671/2021.
"""

from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .role_user import RoleUser
    from .registro import Registro
    from .local_trabalho import LocalTrabalho


class Business(db.Model):
    __tablename__ = "businesses"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    corporate_name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    trade_name: Mapped[str] = mapped_column(db.String(120), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False, index=True)
    business_type: Mapped[Optional[str]] = mapped_column(db.String(50))
    description: Mapped[Optional[str]] = mapped_column(db.String(255))
    # Soft-delete: empresas inativas permanecem no banco
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    # Campos exigidos pelo REP-P (Portaria 671/2021)
    cei_caepf: Mapped[Optional[str]] = mapped_column(db.String(20))
    logradouro: Mapped[Optional[str]] = mapped_column(db.String(120))
    numero: Mapped[Optional[str]] = mapped_column(db.String(10))
    complemento: Mapped[Optional[str]] = mapped_column(db.String(60))
    bairro: Mapped[Optional[str]] = mapped_column(db.String(60))
    cidade: Mapped[Optional[str]] = mapped_column(db.String(60))
    uf: Mapped[Optional[str]] = mapped_column(db.String(2))
    cep: Mapped[Optional[str]] = mapped_column(db.String(10))
    telefone: Mapped[Optional[str]] = mapped_column(db.String(20))

    # Relacionamentos
    owner: Mapped["User"] = relationship("User")
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="business",
        cascade="all, delete-orphan"
    )
    registros: Mapped[List["Registro"]] = relationship(
        "Registro",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )
    locais_trabalho: Mapped[List["LocalTrabalho"]] = relationship(
        "LocalTrabalho",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Business {self.trade_name}>"
