# pyright: reportCallIssue=false
"""Geracao atomica do NSR (Numero Sequencial de Registro) por empresa.

O NSR deve ser unico e continuo por empresa. Usa SELECT FOR UPDATE
(lock de linha) para que batidas concorrentes recebam NSRs distintos.
"""

from E_Ponto.ext.db import db
from E_Ponto.models.nsr_sequencia import NsrSequencia


def get_next_nsr(empresa_id: int) -> int:
    """Retorna o proximo NSR da empresa usando lock de linha.

    with_for_update() trava a linha ate o commit. (SQLite ignora o
    FOR UPDATE, mas ja serializa escritas; em Postgres/MySQL funciona.)
    O commit final fica a cargo da view chamadora.
    """
    seq = (NsrSequencia.query
           .filter_by(empresa_id=empresa_id)
           .with_for_update()
           .first())

    if seq is None:
        seq = NsrSequencia(empresa_id=empresa_id, ultimo_nsr=0)
        db.session.add(seq)

    seq.ultimo_nsr += 1
    db.session.flush()
    return seq.ultimo_nsr
