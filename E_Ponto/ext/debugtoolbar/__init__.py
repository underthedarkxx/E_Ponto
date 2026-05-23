# =====================================================================
# ext/debugtoolbar — Barra de depuração no navegador
# ---------------------------------------------------------------------
# Flask-DebugToolbar injeta uma barra lateral na resposta HTML
# mostrando: queries SQL executadas, variáveis do template, tempo
# de cada middleware, headers, etc.
#
# A barra só aparece quando DEBUG=True. Em produção fica inativa.
# =====================================================================

from flask_debugtoolbar import DebugToolbarExtension

# Singleton da extensão.
toolbar = DebugToolbarExtension()


def init_app(app):
    """Registra a Debug Toolbar no app."""
    toolbar.init_app(app)
