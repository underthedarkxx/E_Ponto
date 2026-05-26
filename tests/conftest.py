# =====================================================================
# tests/conftest.py — Preparação compartilhada dos testes (pytest)
# ---------------------------------------------------------------------
# Um "fixture" é um pedaço de preparação que o pytest injeta no teste
# que pedir por ele — basta o teste ter um parâmetro com o mesmo nome
# do fixture. Aqui criamos três:
#   - app:     a aplicação Flask configurada para teste (banco isolado);
#   - client:  um cliente HTTP falso que faz requisições sem subir servidor;
#   - usuario: cria um usuário ativo no banco e devolve suas credenciais.
# =====================================================================

import pytest
from sqlalchemy.pool import StaticPool

# `app.py` fica na raiz do projeto. O `inv test` roda com PYTHONPATH=.,
# então a importação direta funciona.
from app import create_app
from E_Ponto.ext.db import db as _db


@pytest.fixture
def app():
    """App Flask em modo de teste, com banco SQLite em memória e isolado."""
    app = create_app(test_config={
        # TESTING=True faz o app.py NÃO ligar CSRF nem rate-limit (atrapalham).
        "TESTING": True,
        # SECRET_KEY é obrigatória para assinar a sessão/cookies de login.
        "SECRET_KEY": "test-secret-key",
        # "sqlite://" (sem caminho) = banco em MEMÓRIA: nasce vazio e some
        # ao fim do teste, sem deixar arquivo .db por aí.
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        # StaticPool + check_same_thread=False fazem TODAS as conexões
        # compartilharem o MESMO banco em memória. Sem isso, cada conexão
        # abriria um banco vazio próprio e as tabelas "sumiriam" entre a
        # criação (abaixo) e as requisições do teste.
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
        "WTF_CSRF_ENABLED": False,
    })

    # create_all() precisa de um app_context ativo para enxergar a config
    # do banco. Tudo entre o `with` e o fim roda com esse contexto ligado.
    with app.app_context():
        _db.create_all()       # cria todas as tabelas (vazias) p/ o teste
        yield app              # entrega o app pronto; o teste roda aqui
        _db.session.remove()   # fecha a sessão do SQLAlchemy
        _db.drop_all()         # derruba as tabelas (limpeza final)


@pytest.fixture
def client(app):
    """Cliente de teste: faz GET/POST na app sem precisar de servidor real."""
    return app.test_client()


@pytest.fixture
def usuario(app):
    """Cria um usuário ativo de teste e devolve email + senha em texto puro."""
    from E_Ponto.ext.db import db
    from E_Ponto.models.user import User
    from E_Ponto.views.auth import bcrypt

    senha = "senha123"
    with app.app_context():
        user = User(
            name="Usuario de Teste",
            email="teste@eponto.com",
            cpf="12345678900",
            pis_nis="12345678900",
            # No banco guardamos só o HASH da senha, nunca o texto puro.
            password=bcrypt.generate_password_hash(senha).decode(),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
    return {"email": "teste@eponto.com", "senha": senha}
