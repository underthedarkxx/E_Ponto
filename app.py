# =====================================================================
# app.py — Fábrica de aplicação Flask (Application Factory Pattern)
# ---------------------------------------------------------------------
# Este arquivo é o ponto de entrada do projeto. Em vez de criar a
# instância do Flask diretamente no nível do módulo, usamos uma
# função `create_app()` que monta a aplicação. Esse padrão permite:
#   - criar várias instâncias (ex.: uma para testes, outra para dev);
#   - evitar problemas de importação circular entre extensões/modelos;
#   - injetar configurações específicas (ex.: banco em memória nos testes).
# =====================================================================

import logging
from flask import Flask


def create_app(test_config=None):
    """
    Cria e configura a instância do Flask.

    Parâmetros:
        test_config (dict | None): dicionário opcional com configurações
            que sobrescrevem as do .env. Usado principalmente pelos testes
            (pytest) para forçar TESTING=True, banco SQLite em memória, etc.

    Retorna:
        Flask: aplicação totalmente inicializada e pronta para servir.
    """
    # Instancia o Flask. `__name__` ajuda o Flask a descobrir o caminho
    # base do projeto (para localizar templates, static, etc.).
    app = Flask(__name__)

    # Quando rodando em modo debug, aumenta o nível de log para DEBUG
    # para que mensagens detalhadas apareçam no console.
    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    # -----------------------------------------------------------------
    # 1) Configuração via arquivos .env (.env.dev, .env.test, .env.prod)
    # -----------------------------------------------------------------
    # O arquivo correto já foi selecionado antes (pelo tasks.py via inv).
    # Este passo lê variáveis de ambiente e popula app.config.
    from E_Ponto.ext.config import init_app as init_config
    init_config(app)

    # Se foi passado um test_config, ele tem prioridade sobre o .env.
    # Útil para sobrescrever URI do banco em testes, desativar CSRF, etc.
    if test_config:
        app.config.update(test_config)

    # -----------------------------------------------------------------
    # 2) Banco de dados (SQLAlchemy)
    # -----------------------------------------------------------------
    # init_db registra a extensão SQLAlchemy no app.
    from E_Ponto.ext.db import init_app as init_db
    init_db(app)

    # register_models() importa cada arquivo de modelo para que o
    # SQLAlchemy "enxergue" todas as tabelas antes de qualquer operação
    # como create_all() ou migração.
    from E_Ponto.ext.db import register_models
    register_models()

    # -----------------------------------------------------------------
    # 3) Autenticação (Flask-Login)
    # -----------------------------------------------------------------
    # Configura o sistema de sessão de usuários: login, logout,
    # @login_required, current_user, etc.
    from E_Ponto.ext.auth import init_app as init_auth
    init_auth(app)

    # -----------------------------------------------------------------
    # 4) Migrations (Flask-Migrate / Alembic)
    # -----------------------------------------------------------------
    # Permite criar e aplicar migrações de schema do banco via
    # `flask db migrate` e `flask db upgrade`.
    from E_Ponto.ext.migrate import init_app as init_migrate
    init_migrate(app)

    # -----------------------------------------------------------------
    # 5) Extensões que NÃO devem rodar em modo de teste
    # -----------------------------------------------------------------
    # CSRF e Rate Limiter atrapalham os testes automatizados, então
    # só são ativados fora do modo TESTING.
    if not app.config.get("TESTING"):
        # CSRF Protection: protege formulários contra ataques CSRF.
        from E_Ponto.ext.wtf import init_app as init_wtf
        init_wtf(app)

        # Rate Limiter: limita número de requisições por IP/usuário
        # (ex.: tentativas de login).
        from E_Ponto.ext.limiter import init_app as init_limiter
        init_limiter(app)

    # -----------------------------------------------------------------
    # 6) Debug Toolbar (somente útil em desenvolvimento)
    # -----------------------------------------------------------------
    # Mostra uma barra lateral no navegador com queries SQL, tempo de
    # requisição, variáveis de template, etc. Ela só "aparece" quando
    # DEBUG=True; em produção fica inerte.
    from E_Ponto.ext.debugtoolbar import init_app as init_toolbar
    init_toolbar(app)

    # -----------------------------------------------------------------
    # 7) Blueprints (rotas/views)
    # -----------------------------------------------------------------
    # Registra todos os Blueprints (main, auth, admin, rh, ponto,
    # funcionario). Cada Blueprint agrupa um conjunto de rotas.
    from E_Ponto.views import init_app as init_site
    init_site(app)

    # App pronta para ser executada por `flask run` ou um WSGI server.
    return app
