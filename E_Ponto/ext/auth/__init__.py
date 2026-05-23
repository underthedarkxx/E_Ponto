# =====================================================================
# ext/auth — Autenticação de usuários (Flask-Login)
# ---------------------------------------------------------------------
# O Flask-Login gerencia sessões de usuário: quando alguém faz login,
# ele guarda o id do usuário em um cookie de sessão assinado. Em cada
# requisição seguinte, ele descobre quem está logado e expõe isso via
# `current_user` (importável de flask_login).
# =====================================================================

from flask_login import LoginManager

# Singleton do gerenciador de login. Importado pelas views/forms
# que precisam decorar rotas com @login_required, por exemplo.
login_manager = LoginManager()


def init_app(app):
    """Configura o Flask-Login na aplicação."""
    login_manager.init_app(app)

    # Para onde redirecionar quando um usuário não autenticado tenta
    # acessar uma rota protegida (@login_required). O valor é o
    # endpoint da view de login (blueprint.função).
    login_manager.login_view = 'auth.login'

    # Mensagem flash exibida quando o redirecionamento acontece.
    login_manager.login_message = 'Faca login para acessar esta pagina.'
    # Categoria do flash (controla a cor/estilo no template — bootstrap).
    login_manager.login_message_category = 'warning'

    # -----------------------------------------------------------------
    # user_loader — função chamada a cada requisição
    # -----------------------------------------------------------------
    # O Flask-Login só guarda o ID do usuário na sessão. Para reidratar
    # o objeto User completo (e disponibilizá-lo em `current_user`),
    # ele chama esta função passando o ID que tinha sido salvo.
    @login_manager.user_loader
    def load_user(user_id):
        # Import dentro da função para evitar importação circular
        # (User -> db -> ... -> auth -> User).
        from E_Ponto.models.user import User
        return User.query.get(int(user_id))
