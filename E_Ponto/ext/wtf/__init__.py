# =====================================================================
# ext/wtf — Proteção CSRF (Flask-WTF)
# ---------------------------------------------------------------------
# CSRF (Cross-Site Request Forgery) é um ataque em que um site
# malicioso induz o navegador da vítima a fazer requisições para
# outro site onde ela está logada. A defesa é embutir um token
# secreto em cada formulário; o servidor só aceita a requisição
# se o token for válido.
#
# Flask-WTF faz isso automaticamente para formulários WTForms e
# pode ser desabilitado em testes (TESTING=True).
# =====================================================================

from flask_wtf import CSRFProtect

# Instância única do protetor CSRF.
csrf = CSRFProtect()


def init_app(app):
    """Ativa CSRF, exceto quando estamos em modo de testes."""
    # Durante os testes não queremos lidar com tokens — já desabilitamos
    # via WTF_CSRF_ENABLED=0 no .env.test, mas aqui evitamos até mesmo
    # registrar a extensão.
    if not app.config.get("TESTING"):
        csrf.init_app(app)
