# pyright: reportCallIssue=false
# =====================================================================
# tasks.py — Tarefas do Invoke (semelhante a um Makefile)
# ---------------------------------------------------------------------
# A linha "# pyright: reportCallIssue=false" no topo desativa, somente
# neste arquivo, o aviso do Pylance sobre os construtores dos modelos
# do Flask-SQLAlchemy (ex.: User(name=...), Business(corporate_name=...)).
# O Pylance nao consegue inferir os parametros desses construtores a
# partir dos campos Mapped[...]; o codigo funciona em runtime.
# ---------------------------------------------------------------------
# Invoke é uma biblioteca que transforma funções Python em comandos
# de linha. Cada função decorada com @task vira um subcomando do `inv`:
#     inv install   -> tasks.install()
#     inv run       -> tasks.run()
#     inv test      -> tasks.test()
# É usado para padronizar comandos comuns do projeto (instalar,
# rodar, testar, fazer seed, empacotar zip, etc.).
# =====================================================================

from invoke.tasks import task
from datetime import datetime, date
from dotenv import load_dotenv
import os
import zipfile


# ==========================================================
# GERENCIAMENTO DE AMBIENTE
# ==========================================================
def load_env(env: str):
    """
    Carrega o arquivo .env correspondente ao ambiente.
    Ex: dev, test, prod
    """
    env_file = f".env.{env}"

    # Confirma que o arquivo existe antes de tentar carregar.
    if os.path.exists(env_file):
        # override=True faz o .env sobrescrever variáveis já no shell.
        load_dotenv(env_file, override=True)
        print(f"[ENV] Carregado: {env_file}")
    else:
        # Falha alta — sem .env não dá pra rodar o app corretamente.
        raise FileNotFoundError(f"{env_file} nao encontrado")


# ==========================================================
# INSTALACAO
# ==========================================================
@task
def install(c, dev=True):
    """
    Instala o projeto.
    Use `inv install` para instalar com deps de dev/test (modo padrão).
    """
    if dev:
        # pip install -e: modo "editable" — alterações no código surtem
        # efeito sem reinstalar.
        c.run('pip install -e ".[dev,test]"', echo=True)
    else:
        c.run("pip install .", echo=True)


@task
def uninstall(c):
    """
    Remove o pacote instalado.
    """
    c.run("pip uninstall -y E_Ponto", echo=True)


# ==========================================================
# EXECUCAO
# ==========================================================
@task
def run(c):
    """
    Executa a aplicacao Flask em ambiente de desenvolvimento.
    """
    load_env("dev")
    # flask run usa a variável FLASK_APP do .env para achar o app.
    c.run("flask run")


@task
def prod(c):
    """
    Executa a aplicacao em modo producao.
    Em produção real, troque por gunicorn/uwsgi.
    """
    load_env("prod")
    c.run("flask run")


# ==========================================================
# TESTES
# ==========================================================
@task
def test(c):
    """
    Executa os testes automatizados.
    """
    load_env("test")
    # Setar PYTHONPATH via os.environ funciona no Windows e no Linux.
    # A forma "PYTHONPATH=. pytest" so funciona em shells unix (bash/zsh).
    os.environ["PYTHONPATH"] = "."
    c.run("pytest -v")


# ==========================================================
# BANCO DE DADOS / SEED
# ==========================================================
@task
def initdb(c):
    """
    Cria todas as tabelas no banco (uso unico em dev).
    Em producao usar 'flask db upgrade'.
    """
    load_env("dev")
    from app import create_app
    from E_Ponto.ext.db import db
    app = create_app()
    # app_context é necessário porque create_all() acessa app.config.
    with app.app_context():
        db.create_all()
        print("[DB] Tabelas criadas.")


# ==========================================================
# MIGRACOES (Flask-Migrate / Alembic)
# ==========================================================
# Diferente do initdb (db.create_all, que so CRIA tabelas novas e nunca
# ALTERA as existentes), as migracoes versionam o schema: cada mudanca
# de model vira um script aplicavel sem perder dados — o caminho correto
# para producao. load_env("dev") carrega FLASK_APP=app.py no ambiente, o
# que o CLI do flask precisa para localizar a aplicacao.
@task
def migrate(c, message="migracao"):
    """
    Gera um novo script de migracao comparando os models com o banco.
    Uso: inv migrate -m "adiciona coluna cargo"
    Depois aplique com `inv upgrade`.
    """
    load_env("dev")
    c.run(f'flask db migrate -m "{message}"', echo=True)


@task
def upgrade(c):
    """
    Aplica as migracoes pendentes no banco (cria/altera tabelas).
    Use em producao no lugar de `inv initdb`.
    """
    load_env("dev")
    c.run("flask db upgrade", echo=True)


@task
def downgrade(c):
    """
    Desfaz a ultima migracao aplicada (rollback de schema).
    """
    load_env("dev")
    c.run("flask db downgrade", echo=True)


@task
def dbcurrent(c):
    """
    Mostra em qual versao de migracao o banco esta atualmente.
    """
    load_env("dev")
    c.run("flask db current", echo=True)


@task
def seed(c):
    """
    Insere dados iniciais: papeis, super_admin, empresa demo.
    """
    load_env("dev")
    # Imports dentro da função para não pagar o custo quando não chamada.
    from app import create_app
    from E_Ponto.ext.db import db
    from E_Ponto.models.role import Role
    from E_Ponto.models.user import User
    from E_Ponto.models.business import Business
    from E_Ponto.models.role_user import RoleUser
    from flask_bcrypt import generate_password_hash

    app = create_app()
    with app.app_context():
        # ---- Cria papéis se ainda não existem ----------------------
        for nome in ["super_admin", "admin", "rh", "funcionario"]:
            if not Role.query.filter_by(name=nome).first():
                db.session.add(Role(name=nome))
        # flush() persiste no banco mas sem fechar a transação (assim
        # já podemos consultar pelos IDs recém-criados).
        db.session.flush()

        # ---- Cria super admin ---------------------------------------
        admin = User.query.filter_by(email="admin@eponto.com").first()
        if not admin:
            admin = User(
                name="Administrador",
                email="admin@eponto.com",
                cpf="00000000000",
                pis_nis="00000000000",
                password=generate_password_hash("admin123").decode(),
                is_active=True,
            )
            db.session.add(admin)
            db.session.flush()
            print("[SEED] Super admin criado: admin@eponto.com / admin123")
        # Guarda de runtime: ao contrario de assert, NUNCA e' removido
        # quando o Python roda com -O (modo otimizado / producao).
        if admin is None:
            raise RuntimeError("Falha ao criar/recuperar super admin no seed.")

        # ---- Cria empresa demonstração ------------------------------
        empresa = Business.query.filter_by(cnpj="00000000000000").first()
        if not empresa:
            empresa = Business(
                owner_user_id=admin.id,
                corporate_name="Empresa Demonstracao LTDA",
                trade_name="E-Ponto Demo",
                cnpj="00000000000000",
                cidade="Vila Velha",
                uf="ES",
                is_active=True,
            )
            db.session.add(empresa)
            db.session.flush()
            print(f"[SEED] Empresa criada: {empresa.trade_name}")
        if empresa is None:
            raise RuntimeError("Falha ao criar/recuperar empresa demo no seed.")

        # ---- Vincula admin à empresa como super_admin ---------------
        role_admin = Role.query.filter_by(name="super_admin").first()
        if role_admin is None:
            raise RuntimeError(
                "Role 'super_admin' nao foi criado. "
                "Verifique o loop de papeis no inicio do seed."
            )
        if not RoleUser.query.filter_by(user_id=admin.id, business_id=empresa.id, role_id=role_admin.id).first():
            db.session.add(RoleUser(user_id=admin.id, business_id=empresa.id, role_id=role_admin.id))

        # ---- Funcionário de teste -----------------------------------
        func = User.query.filter_by(email="joao@eponto.com").first()
        if not func:
            func = User(
                name="Joao da Silva",
                email="joao@eponto.com",
                cpf="11111111111",
                pis_nis="11111111111",
                cargo="Analista",
                data_admissao=date.today(),
                password=generate_password_hash("joao123").decode(),
                is_active=True,
            )
            db.session.add(func)
            db.session.flush()
            role_func = Role.query.filter_by(name="funcionario").first()
            if role_func is None:
                raise RuntimeError("Role 'funcionario' nao foi criado.")
            db.session.add(RoleUser(user_id=func.id, business_id=empresa.id, role_id=role_func.id))
            print("[SEED] Funcionario criado: joao@eponto.com / joao123")

        # commit() persiste tudo de uma vez (uma transação só).
        db.session.commit()
        print("[SEED] Concluido.")


# ==========================================================
# QUALIDADE DE CODIGO
# ==========================================================
@task
def lint(c):
    """
    Verifica qualidade de codigo.
    """
    # flake8 acusa estilo PEP-8 + erros estáticos básicos.
    c.run("flake8")


@task
def format(c):
    """
    Formata o codigo automaticamente.
    """
    # black reformata todo o código no padrão definido pela ferramenta.
    c.run("black .")


# ==========================================================
# EMPACOTAMENTO
# ==========================================================
@task
def zip(c, name=None):
    """Cria um zip do projeto excluindo arquivos pesados/sensíveis."""
    # Nome com timestamp para evitar sobrescrever zips antigos.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_filename = name or f"E_Ponto{timestamp}.zip"
    # Salva o zip no diretório pai (fora do próprio projeto).
    zip_path = os.path.abspath(os.path.join("..", zip_filename))

    print(f"→ Criando ZIP: {zip_path}")

    # Pastas que NÃO devem entrar no zip.
    excludes = [
        "venv",
        "__pycache__",
        ".git",
        ".vscode",
        "delivery.egg-info"
    ]

    # ZIP_DEFLATED = compressão padrão (similar ao zip do Windows).
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # os.walk percorre recursivamente diretórios. dirs é uma lista
        # mutável que o walk usa internamente — alterá-la in-place (com
        # dirs[:] = ...) impede que ele desça nas pastas excluídas.
        for root, dirs, files in os.walk("."):

            dirs[:] = [d for d in dirs if d not in excludes]

            for file in files:
                # Ignora arquivos compilados, logs e bancos de dados.
                if file.endswith((".pyc", ".pyo", ".pyd", ".log", ".db", ".sqlite3")):
                    continue

                filepath = os.path.join(root, file)
                zipf.write(filepath)

    # Confirmação e tamanho final em MB.
    if os.path.exists(zip_path):
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"→ ZIP criado com sucesso: {zip_path}")
        print(f"   Tamanho: {size_mb:.2f} MB")
