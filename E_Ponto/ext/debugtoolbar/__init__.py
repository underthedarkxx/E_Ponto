"""ext/debugtoolbar: barra de depuracao no navegador (apenas com DEBUG=True)."""

from flask_debugtoolbar import DebugToolbarExtension

toolbar = DebugToolbarExtension()


def init_app(app):
    """Registra a Debug Toolbar no app."""
    toolbar.init_app(app)
