"""ext/auth: autenticacao de usuarios via Flask-Login."""

from flask_login import LoginManager

login_manager = LoginManager()


def init_app(app):
    """Configura o Flask-Login na aplicacao."""
    login_manager.init_app(app)

    # Para onde redirecionar usuarios nao autenticados (@login_required)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faca login para acessar esta pagina.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        # Import local para evitar importacao circular
        from E_Ponto.models.user import User
        return User.query.get(int(user_id))
