"""Modelos City e Address.

City e uma lista normalizada de cidades; Address e o endereco de um
usuario, com FK para User e City.
"""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .user import User


class City(db.Model):
    __tablename__ = "cities"

    __table_args__ = (
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
    state: Mapped[Optional[str]] = mapped_column(db.String(2))
    country: Mapped[Optional[str]] = mapped_column(db.String(50))
    region: Mapped[Optional[str]] = mapped_column(db.String(50))

    addresses: Mapped[List["Address"]] = relationship(
        "Address",
        back_populates="city"
    )

    def __repr__(self) -> str:
        return f"<City {self.name}{' - ' + self.state if self.state else ''}>"


class Address(db.Model):
    __tablename__ = "address"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    road: Mapped[Optional[str]] = mapped_column(db.String(100))
    number: Mapped[Optional[int]] = mapped_column(db.Integer)
    district: Mapped[Optional[str]] = mapped_column(db.String(100))
    zipcode: Mapped[Optional[str]] = mapped_column(db.String(15))

    # CASCADE: apagar o usuario apaga seus enderecos
    user_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # SET NULL: apagar a cidade apenas zera a referencia
    city_id: Mapped[int | None] = mapped_column(
        db.Integer,
        db.ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="addresses")
    city: Mapped["City"] = relationship("City", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address {self.road}, {self.number} - {self.district}>"
