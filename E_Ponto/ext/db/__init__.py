"""ext/db: instancia unica do SQLAlchemy compartilhada pelos modelos.

Tambem oferece register_models() para garantir que todas as classes de
modelo sejam importadas antes de o SQLAlchemy precisar do metadata.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


# Base herdando de DeclarativeBase (SQLAlchemy 2.0): permite ao Pylance
# inferir os parametros do construtor a partir dos campos Mapped[...].
class Base(DeclarativeBase):
    pass


# Singleton importado pelos modelos: `from E_Ponto.ext.db import db`
db = SQLAlchemy(model_class=Base)


def init_app(app):
    """Conecta a extensao SQLAlchemy a instancia do Flask."""
    db.init_app(app)


def register_models():
    """Importa todos os modulos de modelo.

    Necessario porque o SQLAlchemy so registra uma tabela quando a classe
    e importada. Como usamos factory, forcamos a importacao aqui para que
    db.create_all()/migracoes nao ignorem tabelas. Modelos referenciados
    por FKs vem primeiro.
    """
    import E_Ponto.models.role
    import E_Ponto.models.user
    import E_Ponto.models.level
    import E_Ponto.models.business
    import E_Ponto.models.role_user
    import E_Ponto.models.location
    import E_Ponto.models.nsr_sequencia
    import E_Ponto.models.local_trabalho
    import E_Ponto.models.jornada
    import E_Ponto.models.escala
    import E_Ponto.models.registro
    import E_Ponto.models.retificacao
    import E_Ponto.models.banco_horas
    import E_Ponto.models.audit_log
