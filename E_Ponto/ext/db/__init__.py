# =====================================================================
# ext/db — Banco de dados (SQLAlchemy)
# ---------------------------------------------------------------------
# Mantém a instância única do SQLAlchemy (`db`) que é compartilhada
# por todos os modelos do projeto. Também oferece `register_models()`
# para garantir que todas as classes de modelo sejam importadas antes
# do SQLAlchemy precisar do metadata (ex.: para criar tabelas).
# =====================================================================

from flask_sqlalchemy import SQLAlchemy

# Singleton da extensão. Os modelos importam este objeto:
#     from E_Ponto.ext.db import db
#     class Foo(db.Model): ...
db = SQLAlchemy()


def init_app(app):
    """Conecta a extensão SQLAlchemy à instância do Flask."""
    db.init_app(app)


def register_models():
    """
    Importa todos os módulos de modelo do projeto.

    Por quê isto é necessário?
        O SQLAlchemy só "conhece" um modelo depois que a classe é
        importada (porque é a importação que dispara a metaclass que
        registra a tabela no metadata). Como criamos a aplicação via
        factory, precisamos forçar essa importação manualmente — caso
        contrário, comandos como `db.create_all()` ou migrações podem
        ignorar tabelas que nunca foram referenciadas em código.

    A ordem dos imports importa parcialmente: modelos referenciados
    por chaves estrangeiras (Role, User, Business...) vêm primeiro,
    e os que dependem deles vêm depois.
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
