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
from pathlib import Path
from dotenv import load_dotenv


# Raiz do projeto: config/__init__.py -> config -> ext -> E_Ponto -> raiz
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Mapeia FLASK_ENV (nomes longos) para o sufixo dos arquivos .env.*
_ENV_SUFFIX = {
    "development": "dev",
    "testing": "test",
    "production": "prod",
}


def _load_env_file():
    """
    Garante que o arquivo .env.* correto seja carregado.

    Quando o app sobe via `inv run/test/prod`, o tasks.py já carregou o
    .env certo no ambiente. Mas quando alguém roda `flask run` direto,
    ninguém carregou nada — a SECRET_KEY fica vazia e o app quebra com
    "The session is unavailable because no secret key was set".

    Aqui cobrimos os dois casos: descobrimos o ambiente por FLASK_ENV
    (default: development) e carregamos o .env.<sufixo> correspondente.
    Usamos override=False para NÃO sobrescrever variáveis já presentes
    no ambiente — preservando o fluxo do `inv`, que carrega o .env antes.
    """
    env = os.environ.get("FLASK_ENV", "development")
    suffix = _ENV_SUFFIX.get(env, "dev")
    env_file = PROJECT_ROOT / f".env.{suffix}"

    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        # Sem .env.<suffix>: tenta um .env genérico, se houver.
        load_dotenv(override=False)


def init_app(app):
    """Carrega o .env e preenche app.config com todos os parâmetros."""

    _load_env_file()

    # ---- Configurações gerais do Flask -------------------------------
    # SECRET_KEY: usada para assinar cookies de sessão e tokens CSRF.
    # NUNCA deve ser exposta publicamente.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    # Falha cedo, com mensagem clara, em vez de um 500 críptico em runtime.
    # (Em testes a SECRET_KEY costuma vir via test_config; não bloqueamos.)
    if not app.config['SECRET_KEY'] and os.environ.get('FLASK_ENV') != 'testing':
        raise RuntimeError(
            "SECRET_KEY ausente. Provavelmente o arquivo .env.dev não existe "
            "(ele é ignorado pelo Git e não vem no download do projeto).\n"
            "Crie-o a partir do exemplo e rode novamente:\n"
            "    Windows:    copy .env.example .env.dev\n"
            "    Linux/Mac:  cp .env.example .env.dev"
        )
    # DEBUG: ativa o modo de depuração (recarregamento automático,
    # mensagens de erro detalhadas). Só deve ser True em desenvolvimento.
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'

    # ---- Configurações de e-mail (Flask-Mail / SMTP) -----------------
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    # MAIL_PORT precisa ser int. Default 587 (TLS).
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@eponto.local')
    # MAIL_SUPPRESS_SEND=True: nao envia de verdade, so loga.
    # Util em dev/test para nao precisar de SMTP configurado.
    app.config['MAIL_SUPPRESS_SEND'] = os.environ.get('MAIL_SUPPRESS_SEND', 'True') == 'True'

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
