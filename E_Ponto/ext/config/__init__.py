"""ext/config: carrega o .env e popula app.config.

Primeira extensao a ser inicializada, pois as demais dependem das
configuracoes (URL do banco, SECRET_KEY, etc.).
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Raiz do projeto: config -> ext -> E_Ponto -> raiz
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# FLASK_ENV -> sufixo dos arquivos .env.*
_ENV_SUFFIX = {
    "development": "dev",
    "testing": "test",
    "production": "prod",
}


def _load_env_file():
    """Carrega o .env.* correto conforme FLASK_ENV.

    Cobre o caso de `flask run` direto (sem `inv`), em que nenhum .env
    foi carregado. Usa override=False para nao sobrescrever variaveis ja
    presentes no ambiente, preservando o fluxo do `inv`.
    """
    env = os.environ.get("FLASK_ENV", "development")
    suffix = _ENV_SUFFIX.get(env, "dev")
    env_file = PROJECT_ROOT / f".env.{suffix}"

    if env_file.exists():
        load_dotenv(env_file, override=False)
    else:
        load_dotenv(override=False)


def init_app(app):
    """Carrega o .env e preenche app.config com todos os parametros."""

    _load_env_file()

    # Configuracoes gerais do Flask
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    # Falha cedo, com mensagem clara, se faltar a SECRET_KEY (exceto em testes)
    if not app.config['SECRET_KEY'] and os.environ.get('FLASK_ENV') != 'testing':
        raise RuntimeError(
            "SECRET_KEY ausente. Provavelmente o arquivo .env.dev não existe "
            "(ele é ignorado pelo Git e não vem no download do projeto).\n"
            "Crie-o a partir do exemplo e rode novamente:\n"
            "    Windows:    copy .env.example .env.dev\n"
            "    Linux/Mac:  cp .env.example .env.dev"
        )
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'

    # E-mail (Flask-Mail / SMTP)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@eponto.local')
    # True: nao envia de verdade, apenas loga (util em dev/test)
    app.config['MAIL_SUPPRESS_SEND'] = os.environ.get('MAIL_SUPPRESS_SEND', 'True') == 'True'

    # Banco de dados (SQLite por padrao)
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///eponto.db')

    # Converte caminho SQLite relativo em absoluto, ancorado na raiz do
    # projeto, para nao depender do diretorio de onde o servidor subiu.
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        rel = db_url.replace('sqlite:///', '', 1)
        if not os.path.isabs(rel):
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            abs_path = os.path.join(project_root, rel)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            db_url = f'sqlite:///{abs_path}'
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Rate limiting e CSRF
    app.config['RATELIMIT_STORAGE_URI'] = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    # Desabilite em testes com WTF_CSRF_ENABLED=0 no .env.test
    app.config['WTF_CSRF_ENABLED'] = os.environ.get('WTF_CSRF_ENABLED', '1') != '0'

    # Debug Toolbar (apenas em modo debug)
    if app.debug:
        app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
