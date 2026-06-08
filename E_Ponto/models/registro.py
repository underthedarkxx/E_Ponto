"""Modelo Registro: batida de ponto eletronica.

Inclui os dados exigidos pela Portaria 671/2021: NSR unico por empresa,
hash em cadeia (anti-adulteracao) e geolocalizacao para auditoria.
"""

import enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, Numeric, UniqueConstraint
from E_Ponto.ext.db import db

if TYPE_CHECKING:
    from .business import Business
    from .user import User
    from .local_trabalho import LocalTrabalho


class TipoRegistro(enum.Enum):
    ENTRADA = "entrada"
    SAIDA_ALMOCO = "saida_almoco"
    RETORNO_ALMOCO = "retorno_almoco"
    SAIDA = "saida"
    INCLUSAO = "inclusao"          # Ponto faltante incluido manualmente pelo RH
    ALTERACAO = "alteracao"        # Retificacao aprovada que mudou o horario


# Tipos que abrem e fecham um periodo trabalhado
TIPOS_ENTRADA = (TipoRegistro.ENTRADA, TipoRegistro.RETORNO_ALMOCO)
TIPOS_SAIDA = (TipoRegistro.SAIDA_ALMOCO, TipoRegistro.SAIDA)


class Registro(db.Model):
    __tablename__ = "registros"
    __table_args__ = (
        # NSR unico por empresa (exigencia REP-P)
        UniqueConstraint("empresa_id", "nsr", name="uq_empresa_nsr"),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # NSR — Numero Sequencial de Registro, gerenciado por NsrSequencia
    nsr: Mapped[int] = mapped_column(db.Integer, nullable=False)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    tipo: Mapped[TipoRegistro] = mapped_column(db.Enum(TipoRegistro), nullable=False)
    # Sempre em UTC; convertido para o fuso local apenas na exibicao
    timestamp_utc: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, index=True)

    # Geolocalizacao
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    precisao_metros: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    # True quando a batida esta fora do raio do local; aceita mas sinalizada ao RH
    suspeito_geo: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    local_trabalho_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("locais_trabalho.id"), nullable=True)
    justificativa: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Integridade (hash chain)
    hash_registro: Mapped[str] = mapped_column(db.String(64), nullable=False)
    hash_anterior: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)

    # Para registros tipo INCLUSAO/ALTERACAO
    solicitante_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    aprovador_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    # Relacionamentos
    empresa: Mapped["Business"] = relationship("Business", back_populates="registros")
    # foreign_keys explicito: ha 3 FKs para users.id (user, solicitante, aprovador)
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    solicitante: Mapped[Optional["User"]] = relationship("User", foreign_keys=[solicitante_id])
    aprovador: Mapped[Optional["User"]] = relationship("User", foreign_keys=[aprovador_id])
    local_trabalho: Mapped[Optional["LocalTrabalho"]] = relationship("LocalTrabalho")

    _TIPO_LABELS = {
        TipoRegistro.ENTRADA: "Entrada",
        TipoRegistro.SAIDA_ALMOCO: "Saída p/ Almoço",
        TipoRegistro.RETORNO_ALMOCO: "Retorno do Almoço",
        TipoRegistro.SAIDA: "Saída Final",
        TipoRegistro.INCLUSAO: "Inclusão Manual",
        TipoRegistro.ALTERACAO: "Alteração",
    }

    @property
    def tipo_display(self) -> str:
        """Retorna o nome do tipo formatado para exibicao em UI."""
        return self._TIPO_LABELS.get(self.tipo, self.tipo.value)

    @property
    def eh_entrada(self) -> bool:
        """True para tipos que abrem um periodo (Entrada / Retorno)."""
        return self.tipo in TIPOS_ENTRADA

    def __repr__(self) -> str:
        return f"<Registro nsr={self.nsr} tipo={self.tipo.value} empresa_id={self.empresa_id}>"
