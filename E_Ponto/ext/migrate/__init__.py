"""ext/migrate: migracoes de banco via Flask-Migrate / Alembic."""

from flask_migrate import Migrate

migrate = Migrate()


def init_app(app):
    """Conecta o Flask-Migrate ao app e ao SQLAlchemy compartilhado."""
    # Import local: depende do `db` ja criado em ext/db
    from E_Ponto.ext.db import db
    migrate.init_app(app, db)
