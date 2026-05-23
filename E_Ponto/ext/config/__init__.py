# =====================================================================
# ext/config — Carrega variáveis de ambiente e popula app.config
# ---------------------------------------------------------------------
# Lê o arquivo .env (já selecionado por tasks.py: .env.dev, .env.test
# ou .env.prod) e converte cada variável em uma chave de app.config.
#
# É a primeira extensão a ser inicializada porque todas as outras
# dependem das configurações (URL do banco, SECRET_KEY, etc.).
# =====================================================================

import os
from dotenv import load_dotenv


def init_app(app):
    """Carrega o .env e preenche app.config com todos os parâmetros."""

    # `override=True` faz com que valores do .env sobrescrevam variáveis
    # já existentes no ambiente do sistema.
    load_dotenv(override=True)

    # ---- Configurações gerais do Flask -------------------------------
    # SECRET_KEY: usada para assinar cookies de sessão e tokens CSRF.
    # NUNCA deve ser exposta publicamente.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    # DEBUG: ativa o modo de depuração (recarregamento automático,
    # mensagens de erro detalhadas). Só deve ser True em desenvolvimento.
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'

    # ---- Configurações de e-mail (Flask-Mail / SMTP) -----------------
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # ---- Banco de dados ---------------------------------------------
    # Por padrão usa SQLite com arquivo `eponto.db`.
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///eponto.db')

    # Quando o usuário define um caminho relativo (sqlite:///foo.db),
    # o Flask interpreta em relação ao diretório atual de execução —
    # o que pode quebrar dependendo de onde o servidor foi iniciado.
    # O bloco abaixo converte o caminho relativo para absoluto,
    # ancorando-o na raiz do projeto.
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        rel = db_url.replace('sqlite:///', '', 1)
        if not os.path.isabs(rel):
            # Sobe 4 níveis: config/__init__.py -> config -> ext -> E_Ponto -> raiz
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            abs_path = os.path.join(project_root, rel)
            # Garante que o diretório onde o .db ficará exista.
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            db_url = f'sqlite:///{abs_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # Evita warnings desnecessários do SQLAlchemy e melhora performance.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ---- Rate limiting e CSRF ---------------------------------------
    # Onde o Flask-Limiter armazenará os contadores de requisição
    # (memory://, redis://..., etc.).
    app.config['RATELIMIT_STORAGE_URI'] = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    # CSRF é habilitado por padrão. Para desabilitar em testes,
    # basta colocar WTF_CSRF_ENABLED=0 no .env.test.
    app.config['WTF_CSRF_ENABLED'] = os.environ.get('WTF_CSRF_ENABLED', '1') != '0'

    # ---- Debug Toolbar ----------------------------------------------
    # Só faz sentido configurar quando estamos em modo debug.
    if app.debug:
        # Permite editar templates Jinja direto da toolbar.
        app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
        # Não intercepta redirecionamentos (302) — comportamento mais
        # natural durante navegação no dev server.
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
