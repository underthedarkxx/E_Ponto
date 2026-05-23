# =====================================================================
# models/nsr_sequencia.py — Contador de NSR por empresa
# ---------------------------------------------------------------------
# A Portaria 671/2021 (REP-P) exige que o NSR (Número Sequencial de
# Registro) seja contínuo e crescente por empresa. Esta tabela é
# essencialmente um contador: para cada empresa, qual foi o último
# NSR emitido.
#
# Antes de gravar um Registro novo, o sistema lê esta tabela, soma 1
# e usa esse valor como NSR. A operação precisa ser atômica (numa
# transação com lock) para evitar duplicatas em ambiente concorrente.
# =====================================================================

from sqlalchemy.orm import Mapped, mapped_column
from E_Ponto.ext.db import db


class NsrSequencia(db.Model):
    __tablename__ = "nsr_sequencias"
    __table_args__ = {'extend_existing': True}

    # empresa_id é a chave primária — uma linha por empresa.
    empresa_id: Mapped[int] = mapped_column(
        db.ForeignKey("businesses.id"), primary_key=True
    )
    # Último NSR emitido. Próximo será ultimo_nsr + 1.
    ultimo_nsr: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<NsrSequencia empresa_id={self.empresa_id} ultimo_nsr={self.ultimo_nsr}>"
