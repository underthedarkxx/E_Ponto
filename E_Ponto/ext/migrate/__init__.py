# =====================================================================
# ext/migrate — Migrações de banco (Flask-Migrate / Alembic)
# ---------------------------------------------------------------------
# Flask-Migrate é um wrapper do Alembic, a ferramenta padrão de
# versionamento de schema do SQLAlchemy. Permite usar:
#     flask db init       (uma vez, cria a pasta migrations/)
#     flask db migrate -m "mensagem"   (gera um script de migração)
#     flask db upgrade    (aplica as migrações no banco)
# =====================================================================

from flask_migrate import Migrate

# Singleton da extensão.
migrate = Migrate()


def init_app(app):
    """Conecta o Flask-Migrate ao app e ao SQLAlchemy compartilhado."""
    # Import dentro da função porque precisamos do `db` já criado
    # em ext/db, e queremos evitar carregar essa dependência só por
    # importar o pacote ext/migrate.
    from E_Ponto.ext.db import db
    migrate.init_app(app, db)
