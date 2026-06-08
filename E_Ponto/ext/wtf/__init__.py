"""ext/wtf: protecao CSRF via Flask-WTF (desativada em testes)."""

from flask_wtf import CSRFProtect

csrf = CSRFProtect()


def init_app(app):
    """Ativa CSRF, exceto em modo de testes."""
    if not app.config.get("TESTING"):
        csrf.init_app(app)
