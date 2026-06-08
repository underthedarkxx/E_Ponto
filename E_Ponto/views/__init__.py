"""Registro de todos os Blueprints e extensoes que dependem do app.

init_app() e chamada por create_app() (app.py) e liga as rotas de cada
blueprint (auth, main, ponto, admin, rh, funcionario) ao Flask.
"""

from E_Ponto.views.main import bp_main
from E_Ponto.views.auth import bp_auth, bcrypt
from E_Ponto.views.ponto import bp_ponto
from E_Ponto.views.admin import bp_admin
from E_Ponto.views.rh import bp_rh
from E_Ponto.views.funcionario import bp_funcionario
from E_Ponto.utils.tz import to_local, fmt_local

from flask import render_template


def _register_error_handlers(app):
    """Paginas de erro amigaveis (mantem o visual do sistema)."""
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        # Desfaz transacoes meio-abertas para a sessao voltar a um estado usavel
        from E_Ponto.ext.db import db
        db.session.rollback()
        app.logger.exception('Erro interno (500)')
        return render_template('errors/500.html'), 500


def init_app(app):
    """Registra os blueprints, filtros Jinja e handlers de erro."""
    # Bcrypt gera os hashes de senha; mora em auth.py
    bcrypt.init_app(app)

    # Filtros Jinja para exibir horarios em fuso local
    #   {{ dt|localtime }}        -> datetime aware no fuso local
    #   {{ dt|localdt('%H:%M') }} -> string ja formatada
    app.add_template_filter(to_local, 'localtime')
    app.add_template_filter(fmt_local, 'localdt')

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_ponto)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_rh)
    app.register_blueprint(bp_funcionario)

    _register_error_handlers(app)

    app.logger.info("Blueprints registrados: auth, main, ponto, admin, rh, funcionario")
