# pyright: reportCallIssue=false
"""Tarefas do Invoke para o projeto E-Ponto.

Cada funcao decorada com @task vira um subcomando do `inv`
(ex.: `inv install`, `inv run`, `inv test`).
"""

from invoke.tasks import task
from datetime import date
from dotenv import load_dotenv
import os
import zipfile


# ==========================================================
# GERENCIAMENTO DE AMBIENTE
# ==========================================================
def load_env(env: str):
    """Carrega o arquivo .env correspondente ao ambiente (dev, test, prod)."""
    env_file = f".env.{env}"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"[ENV] Carregado: {env_file}")
    else:
        raise FileNotFoundError(f"{env_file} nao encontrado")


# ==========================================================
# INSTALACAO
# ==========================================================
@task
def install(c, dev=True):
    """Instala o projeto (com deps de dev/test por padrao)."""
    if dev:
        c.run('pip install -e ".[dev,test]"', echo=True)
    else:
        c.run("pip install .", echo=True)


@task
def uninstall(c):
    """Remove o pacote instalado."""
    c.run("pip uninstall -y E_Ponto", echo=True)


# ==========================================================
# EXECUCAO
# ==========================================================
@task
def run(c):
    """Executa a aplicacao Flask em ambiente de desenvolvimento."""
    load_env("dev")
    c.run("flask run")


@task
def prod(c):
    """Executa a aplicacao em modo producao."""
    load_env("prod")
    c.run("flask run")


# ==========================================================
# TESTES
# ==========================================================
@task
def test(c):
    """Executa os testes automatizados."""
    load_env("test")
    os.environ["PYTHONPATH"] = "."
    c.run("pytest -v")


# ==========================================================
# BANCO DE DADOS / SEED
# ==========================================================
@task
def initdb(c):
    """Cria todas as tabelas no banco (uso unico em dev)."""
    load_env("dev")
    from app import create_app
    from E_Ponto.ext.db import db
    app = create_app()
    with app.app_context():
        db.create_all()
        print("[DB] Tabelas criadas.")


# ==========================================================
# MIGRACOES (Flask-Migrate / Alembic)
# ==========================================================
@task
def migrate(c, message="migracao"):
    """Gera um novo script de migracao comparando os models com o banco."""
    load_env("dev")
    c.run(f'flask db migrate -m "{message}"', echo=True)


@task
def upgrade(c):
    """Aplica as migracoes pendentes no banco."""
    load_env("dev")
    c.run("flask db upgrade", echo=True)


@task
def downgrade(c):
    """Desfaz a ultima migracao aplicada (rollback de schema)."""
    load_env("dev")
    c.run("flask db downgrade", echo=True)


@task
def dbcurrent(c):
    """Mostra em qual versao de migracao o banco esta atualmente."""
    load_env("dev")
    c.run("flask db current", echo=True)


@task
def seed(c):
    """Insere dados iniciais: papeis, super_admin e empresa demo."""
    load_env("dev")
    from app import create_app
    from E_Ponto.ext.db import db
    from E_Ponto.models.role import Role
    from E_Ponto.models.user import User
    from E_Ponto.models.business import Business
    from E_Ponto.models.role_user import RoleUser
    from flask_bcrypt import generate_password_hash

    app = create_app()
    with app.app_context():
        # Papeis
        for nome in ["super_admin", "admin", "rh", "funcionario"]:
            if not Role.query.filter_by(name=nome).first():
                db.session.add(Role(name=nome))
        db.session.flush()

        # Super admin
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
        if admin is None:
            raise RuntimeError("Falha ao criar/recuperar super admin no seed.")

        # Empresa demonstracao
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

        # Vincula admin a empresa como super_admin
        role_admin = Role.query.filter_by(name="super_admin").first()
        if role_admin is None:
            raise RuntimeError("Role 'super_admin' nao foi criado.")
        if not RoleUser.query.filter_by(user_id=admin.id, business_id=empresa.id, role_id=role_admin.id).first():
            db.session.add(RoleUser(user_id=admin.id, business_id=empresa.id, role_id=role_admin.id))

        # Funcionario de teste
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

        db.session.commit()
        print("[SEED] Concluido.")


# ==========================================================
# QUALIDADE DE CODIGO
# ==========================================================
@task
def lint(c):
    """Verifica a qualidade do codigo com flake8."""
    c.run("flake8")


@task
def format(c):
    """Formata o codigo automaticamente com black."""
    c.run("black .")


# ==========================================================
# EMPACOTAMENTO
# ==========================================================
@task
def zip(c, name=None):
    """Cria o zip de entrega do projeto, excluindo arquivos pesados/sensiveis.

    Por padrao gera "Grupo5_E-Ponto.zip". Use `inv zip --name=Outro.zip`
    para sobrescrever o nome.
    """
    zip_filename = name or "Grupo5_E-Ponto.zip"
    zip_path = os.path.abspath(os.path.join("..", zip_filename))

    print(f"→ Criando ZIP: {zip_path}")

    excludes = [
        "venv",
        "__pycache__",
        ".git",
        ".vscode",
        "E_Ponto.egg-info",
        ".pytest_cache",
        "instance",
        # Material de apresentacao (entrega separada do codigo-fonte)
        "e-ponto-apresentacao",
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Altera dirs in-place para nao descer nas pastas excluidas.
            dirs[:] = [d for d in dirs if d not in excludes]

            for file in files:
                if file.endswith((".pyc", ".pyo", ".pyd", ".log", ".db", ".sqlite3")):
                    continue
                # Nunca inclui .env reais (contem segredos); mantem apenas *.example.
                if file.startswith(".env") and not file.endswith(".example"):
                    continue
                if file.endswith(".bak"):
                    continue
                # Nao inclui zips (evita zip-dentro-de-zip na entrega).
                if file.endswith(".zip"):
                    continue

                zipf.write(os.path.join(root, file))

    if os.path.exists(zip_path):
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"→ ZIP criado com sucesso: {zip_path}")
        print(f"   Tamanho: {size_mb:.2f} MB")
