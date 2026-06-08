"""Modelo NsrSequencia: contador de NSR por empresa.

O REP-P (Portaria 671/2021) exige NSR continuo e crescente por empresa.
Esta tabela guarda o ultimo NSR emitido; a leitura/incremento deve ser
atomica (transacao com lock) para evitar duplicatas concorrentes.
"""

from sqlalchemy.orm import Mapped, mapped_column
from E_Ponto.ext.db import db


class NsrSequencia(db.Model):
    __tablename__ = "nsr_sequencias"
    __table_args__ = {'extend_existing': True}

    # Uma linha por empresa
    empresa_id: Mapped[int] = mapped_column(
        db.ForeignKey("businesses.id"), primary_key=True
    )
    # Proximo NSR sera ultimo_nsr + 1
    ultimo_nsr: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<NsrSequencia empresa_id={self.empresa_id} ultimo_nsr={self.ultimo_nsr}>"
