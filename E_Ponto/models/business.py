# =====================================================================
# models/business.py — Empresa / estabelecimento
# ---------------------------------------------------------------------
# Representa uma empresa que usa o sistema E-Ponto. Cada empresa tem:
#   - um dono (User);
#   - funcionários (via RoleUser);
#   - locais de trabalho (LocalTrabalho);
#   - registros de ponto (Registro).
#
# Os campos REP-P são dados exigidos pela Portaria 671/2021 (sistema
# eletrônico de registro de ponto via programa).
# =====================================================================

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


# === Business (empresa / estabelecimento) ===
class Business(db.Model):
    __tablename__ = "businesses"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # Dono da empresa (quem fez o cadastro e tem permissão total).
    owner_user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    # Razão social (nome jurídico, ex.: "Padaria Brasil Ltda").
    corporate_name: Mapped[str] = mapped_column(db.String(120), nullable=False)
    # Nome fantasia (nome visível ao público, ex.: "Padaria do João").
    trade_name: Mapped[str] = mapped_column(db.String(120), nullable=False, index=True)
    # CNPJ único — não pode haver duas empresas com o mesmo CNPJ.
    cnpj: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False, index=True)
    business_type: Mapped[Optional[str]] = mapped_column(db.String(50))
    description: Mapped[Optional[str]] = mapped_column(db.String(255))
    # Soft-delete: empresas inativas continuam no banco mas não aparecem.
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), server_default=func.now())

    # ---- Campos exigidos pelo REP-P (legislação trabalhista) --------
    # CEI/CAEPF: Cadastro Específico do INSS / Cadastro de Atividade
    # Econômica de Pessoa Física — usados quando não há CNPJ.
    cei_caepf: Mapped[Optional[str]] = mapped_column(db.String(20))
    # Endereço completo da empresa (sai no AFD/AEJ).
    logradouro: Mapped[Optional[str]] = mapped_column(db.String(120))
    numero: Mapped[Optional[str]] = mapped_column(db.String(10))
    complemento: Mapped[Optional[str]] = mapped_column(db.String(60))
    bairro: Mapped[Optional[str]] = mapped_column(db.String(60))
    cidade: Mapped[Optional[str]] = mapped_column(db.String(60))
    uf: Mapped[Optional[str]] = mapped_column(db.String(2))
    cep: Mapped[Optional[str]] = mapped_column(db.String(10))
    telefone: Mapped[Optional[str]] = mapped_column(db.String(20))

    # ---- Relacionamentos --------------------------------------------
    # Dono (User) — relação simples 1:N (uma empresa, um dono).
    owner: Mapped["User"] = relationship("User")

    # Funcionários ligados à empresa por meio da tabela RoleUser.
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    # Todos os registros de ponto feitos nesta empresa.
    registros: Mapped[List["Registro"]] = relationship(
        "Registro",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    # Locais físicos onde o ponto pode ser batido (matriz, filial...).
    locais_trabalho: Mapped[List["LocalTrabalho"]] = relationship(
        "LocalTrabalho",
        back_populates="empresa",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Business {self.trade_name}>"
