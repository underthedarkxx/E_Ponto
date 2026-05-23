# =====================================================================
# models/location.py — Cidade e endereço (do usuário)
# ---------------------------------------------------------------------
# Duas tabelas:
#   - City: lista normalizada de cidades. Várias pessoas podem morar
#     na mesma cidade — separar evita repetir o nome em cada Address.
#   - Address: endereço de um usuário (FK para User e para City).
# =====================================================================

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .user import User


# === City (cidade) ===
class City(db.Model):
    __tablename__ = "cities"

    __table_args__ = (
        # Índice composto para busca rápida por nome+estado+país.
        db.Index(
            "idx_city_name_state_country",
            "name",
            "state",
            "country"
        ),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    # Sigla do estado (ES, SP, RJ...). Opcional para cidades fora do BR.
    state: Mapped[Optional[str]] = mapped_column(db.String(2))
    country: Mapped[Optional[str]] = mapped_column(db.String(50))
    # Região geográfica (Sudeste, Norte, etc.).
    region: Mapped[Optional[str]] = mapped_column(db.String(50))

    # Endereços que pertencem a esta cidade.
    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="city"
    )

    def __repr__(self) -> str:
        # Mostra "São Paulo - SP" se houver estado, senão só "São Paulo".
        return f"<City {self.name}{' - ' + self.state if self.state else ''}>"


# === Address (endereço) ===
class Address(db.Model):
    __tablename__ = "address"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # "road" = rua/logradouro. Os 4 campos são opcionais porque o
    # cadastro pode começar vazio e ser completado depois.
    road: Mapped[Optional[str]] = mapped_column(db.String(100))
    number: Mapped[Optional[int]] = mapped_column(db.Integer)
    district: Mapped[Optional[str]] = mapped_column(db.String(100))
    zipcode: Mapped[Optional[str]] = mapped_column(db.String(15))

    # Cada endereço pertence a um usuário. Se o usuário for apagado,
    # ondelete="CASCADE" faz o banco apagar o endereço junto.
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Cidade — pode ser NULL. Se a cidade for apagada, SET NULL apenas
    # zera a referência sem perder o endereço.
    city_id: Mapped[int | None] = mapped_column(
        db.Integer,
        db.ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="addresses")
    city: Mapped["City"] = relationship("City", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address {self.road}, {self.number} - {self.district}>"
