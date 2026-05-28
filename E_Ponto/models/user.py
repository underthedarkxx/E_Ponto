# =====================================================================
# models/user.py — Modelo User (usuário do sistema)
# ---------------------------------------------------------------------
# Representa qualquer pessoa que faz login: funcionário, RH ou admin.
# O papel (Role) e a empresa são definidos pela tabela RoleUser.
# =====================================================================

from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from flask_login import UserMixin
from E_Ponto.ext.db import db

# TYPE_CHECKING é True só durante análise estática (mypy, pyright).
# Importações aqui dentro NÃO rodam em runtime, evitando ciclos
# (User precisa saber o tipo de RoleUser, mas RoleUser também precisa
# de User — sem este truque haveria ImportError).
if TYPE_CHECKING:
    from .role_user import RoleUser
    from .location import Address


# === User (usuário) ===
# Herda de:
#   - UserMixin: ganha os métodos exigidos pelo Flask-Login
#     (is_authenticated, is_active, get_id(), etc.)
#   - db.Model: classe-base do SQLAlchemy
class User(UserMixin, db.Model):
    # Nome da tabela no banco.
    __tablename__ = "users"
    # extend_existing=True permite redefinir a tabela durante reimport
    # (útil em testes e no debug com reload).
    __table_args__ = {'extend_existing': True}

    # ---- Identificação ----------------------------------------------
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), index=True)
    # Email é único: ninguém pode se cadastrar duas vezes com o mesmo.
    email: Mapped[str] = mapped_column(db.String(100), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(15))
    # Cargo/função do funcionário (ex.: "Analista de RH", "Vendedor").
    cargo: Mapped[Optional[str]] = mapped_column(db.String(80))
    # Data de admissão: a partir de quando o funcionário passa a "contar"
    # ponto. Dias anteriores a ela NÃO geram falta nem horas esperadas
    # (ver utils/banco_horas.py). Default: o dia do cadastro.
    data_admissao: Mapped[Optional[date]] = mapped_column(db.Date)
    # Marca quando o usuário confirmou o email; None = ainda não confirmou.
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime(timezone=True))
    # Caminho da foto de perfil (relativo ao /static).
    photo: Mapped[Optional[str]] = mapped_column(db.String(100))

    # ---- Autenticação -----------------------------------------------
    # Hash da senha (nunca a senha em texto puro!). Optional porque
    # usuários que entraram por Google/Facebook podem não ter senha.
    password: Mapped[Optional[str]] = mapped_column(db.String(255))
    google_id: Mapped[Optional[str]] = mapped_column(db.String(255))
    facebook_id: Mapped[Optional[str]] = mapped_column(db.String(255))

    # ---- Documentos brasileiros -------------------------------------
    cpf: Mapped[Optional[str]] = mapped_column(db.String(15), index=True)
    # PIS/NIS é exigido pela legislação trabalhista para o ponto.
    pis_nis: Mapped[Optional[str]] = mapped_column(db.String(15), index=True)

    # ---- Autenticação de dois fatores (2FA) -------------------------
    # Segredo TOTP (Google Authenticator, Authy, etc.).
    totp_secret: Mapped[Optional[str]] = mapped_column(db.String(64))
    two_factor_enabled: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # ---- Timestamps -------------------------------------------------
    # server_default=func.now(): o banco preenche automaticamente.
    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    # onupdate=func.now(): atualiza sozinho a cada UPDATE.
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        db.DateTime(timezone=True),
        onupdate=func.now()
    )

    # Soft-delete: em vez de apagar usuários inativos, marca como False.
    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # ---- Relacionamentos --------------------------------------------
    # Lista de associações Role/Business/Level que o usuário tem.
    # cascade="all, delete-orphan": ao apagar o User, apaga essas
    # associações automaticamente.
    role_associations: Mapped[List["RoleUser"]] = relationship(
        "RoleUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Endereços cadastrados pelo usuário.
    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # ---- Métodos auxiliares -----------------------------------------
    @property
    def roles(self):
        """Lista os Role(s) do usuário, ignorando associações sem role."""
        return [assoc.role for assoc in self.role_associations if assoc.role]

    def get_id(self):
        """Flask-Login espera uma string como ID na sessão."""
        return str(self.id)

    def __repr__(self) -> str:
        # Representação útil para debug (aparece no shell, logs, toolbar).
        return f"<User {self.email}>"
