# =====================================================================
# views/__init__.py — Registro de todos os Blueprints da aplicação
# ---------------------------------------------------------------------
# Cada Blueprint agrupa rotas relacionadas (auth, ponto, admin, etc.).
# A função `init_app()` é chamada por `create_app()` no app.py e
# garante que todos eles fiquem registrados no Flask.
# =====================================================================

"""
Views representam a camada de apresentacao da aplicacao.
Responsaveis por definir rotas e retornar respostas HTTP ao cliente.
"""

# Importa cada Blueprint dos módulos correspondentes.
# O `bcrypt` é importado junto porque mora em auth.py — precisamos
# inicializá-lo aqui.
from E_Ponto.views.main import bp_main
from E_Ponto.views.auth import bp_auth, bcrypt
from E_Ponto.views.ponto import bp_ponto
from E_Ponto.views.admin import bp_admin
from E_Ponto.views.rh import bp_rh
from E_Ponto.views.funcionario import bp_funcionario


def init_app(app):
    """
    Registra todos os blueprints e extensoes que dependem do app.
    """
    # Bcrypt cria os hashes de senha. Precisa receber o app para usar
    # configurações como o SALT do bcrypt.
    bcrypt.init_app(app)

    # Registrar = "ligar" o Blueprint ao Flask. A partir daqui as URLs
    # de cada um ficam ativas (/auth/..., /ponto/..., /admin/...).
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_ponto)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_rh)
    app.register_blueprint(bp_funcionario)

    app.logger.info("Blueprints registrados: auth, main, ponto, admin, rh, funcionario")
