# =====================================================================
# models/registro.py — Batida de ponto (registro eletrônico)
# ---------------------------------------------------------------------
# Cada linha desta tabela é uma batida de ponto. Inclui dados
# obrigatórios pela Portaria 671/2021:
#   - NSR (Número Sequencial de Registro), único por empresa
#   - Hash em cadeia (hash_anterior + dados -> hash_registro)
#     para garantir que registros não foram adulterados retroativamente
#   - Geolocalização para auditoria
# =====================================================================

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


# Enum de tipos de registro. Usar Enum em vez de string evita typos
# ("entrada" vs "Entrada" vs "entrar").
class TipoRegistro(enum.Enum):
    ENTRADA = "entrada"                  # Início da jornada
    SAIDA_ALMOCO = "saida_almoco"        # Saída para o intervalo de almoço
    RETORNO_ALMOCO = "retorno_almoco"    # Retorno do intervalo de almoço
    SAIDA = "saida"                      # Saída final (fim da jornada)
    INCLUSAO = "inclusao"                # RH incluiu manualmente um ponto faltante
    ALTERACAO = "alteracao"              # Retificação aprovada que mudou o horário


# Tipos que "abrem" um período trabalhado (funcionário começa a contar horas).
TIPOS_ENTRADA = (TipoRegistro.ENTRADA, TipoRegistro.RETORNO_ALMOCO)
# Tipos que "fecham" um período trabalhado.
TIPOS_SAIDA = (TipoRegistro.SAIDA_ALMOCO, TipoRegistro.SAIDA)


class Registro(db.Model):
    __tablename__ = "registros"
    __table_args__ = (
        # NSR deve ser único dentro de uma mesma empresa (exigência REP-P).
        UniqueConstraint("empresa_id", "nsr", name="uq_empresa_nsr"),
        {'extend_existing': True}
    )

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    # NSR — Número Sequencial de Registro. Começa em 1 e nunca repete
    # ou pula. É gerenciado pela tabela NsrSequencia.
    nsr: Mapped[int] = mapped_column(db.Integer, nullable=False)
    empresa_id: Mapped[int] = mapped_column(db.ForeignKey("businesses.id"), nullable=False, index=True)
    # Funcionário a quem o registro pertence.
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    tipo: Mapped[TipoRegistro] = mapped_column(db.Enum(TipoRegistro), nullable=False)
    # Sempre armazenamos em UTC; converte-se para timezone local no
    # template/relatório. Evita bagunça em horário de verão / fusos.
    timestamp_utc: Mapped[datetime] = mapped_column(db.DateTime(timezone=True), nullable=False, index=True)

    # ---- Geolocalização --------------------------------------------
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7), nullable=True)
    # Precisão reportada pelo GPS do dispositivo (em metros).
    precisao_metros: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(db.String(45), nullable=True)
    # Marcado True quando a batida está fora do raio do LocalTrabalho.
    # O ponto é aceito mas fica destacado para o RH revisar.
    suspeito_geo: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    local_trabalho_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("locais_trabalho.id"), nullable=True)
    # Quando o funcionário bate fora do raio, pede uma justificativa.
    justificativa: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # ---- Integridade (hash chain) ----------------------------------
    # Hash SHA-256 deste registro, calculado a partir dos seus campos.
    hash_registro: Mapped[str] = mapped_column(db.String(64), nullable=False)
    # Hash do registro anterior — encadeia para detectar adulterações.
    hash_anterior: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)

    # ---- Para registros tipo INCLUSAO/ALTERACAO --------------------
    # Quem solicitou e quem aprovou (geralmente, funcionário e RH).
    solicitante_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    aprovador_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    # ---- Relacionamentos -------------------------------------------
    empresa: Mapped["Business"] = relationship("Business", back_populates="registros")
    # foreign_keys explícito porque a tabela tem 3 FKs para users.id
    # (user, solicitante, aprovador) e o SQLAlchemy precisa saber qual.
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    solicitante: Mapped[Optional["User"]] = relationship("User", foreign_keys=[solicitante_id])
    aprovador: Mapped[Optional["User"]] = relationship("User", foreign_keys=[aprovador_id])
    local_trabalho: Mapped[Optional["LocalTrabalho"]] = relationship("LocalTrabalho")

    # Tradução para exibição amigável no template.
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
        """Retorna o nome do tipo formatado para exibição em UI."""
        return self._TIPO_LABELS.get(self.tipo, self.tipo.value)

    @property
    def eh_entrada(self) -> bool:
        """True para tipos que 'abrem' um período (Entrada / Retorno)."""
        return self.tipo in TIPOS_ENTRADA

    def __repr__(self) -> str:
        return f"<Registro nsr={self.nsr} tipo={self.tipo.value} empresa_id={self.empresa_id}>"
