# =====================================================================
# utils/nsr.py — Geração atômica do NSR por empresa
# ---------------------------------------------------------------------
# O NSR (Número Sequencial de Registro) deve ser único e contínuo
# dentro de cada empresa. Se duas batidas acontecem ao mesmo tempo
# (concorrência), precisamos garantir que cada uma receba um NSR
# diferente — daí o uso de SELECT FOR UPDATE (lock de linha).
# =====================================================================

from E_Ponto.ext.db import db
from E_Ponto.models.nsr_sequencia import NsrSequencia


def get_next_nsr(empresa_id: int) -> int:
    """Atomically get next NSR for a company using row-level lock."""
    # with_for_update() adiciona "FOR UPDATE" ao SELECT. O banco trava
    # essa linha até o COMMIT, impedindo que outra conexão leia o
    # mesmo valor simultaneamente.
    #
    # Observação: SQLite ignora o FOR UPDATE (todo o banco já é
    # serializado por write lock). Em Postgres/MySQL funciona como
    # esperado.
    seq = (NsrSequencia.query
           .filter_by(empresa_id=empresa_id)
           .with_for_update()
           .first())

    # Se a empresa ainda não tem linha de sequência, cria com 0.
    if seq is None:
        seq = NsrSequencia(empresa_id=empresa_id, ultimo_nsr=0)
        db.session.add(seq)

    # Incrementa, dá flush (manda pro banco mas sem commit) e devolve
    # o novo valor. O commit final é responsabilidade da view chamadora.
    seq.ultimo_nsr += 1
    db.session.flush()
    return seq.ultimo_nsr
