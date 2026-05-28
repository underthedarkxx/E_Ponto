# =====================================================================
# tests/conftest.py — Preparação compartilhada dos testes (pytest)
# ---------------------------------------------------------------------
# Fixtures: pedaços de preparação que o pytest injeta no teste que pedir
# (basta o teste ter um parâmetro com o mesmo nome do fixture).
#
#   - app          : aplicação Flask em modo teste (SQLite em memória).
#   - client       : cliente HTTP falso (faz requisições sem subir servidor).
#   - usuario      : um usuário ativo simples (usado pelos smoke tests).
#   - org          : organização completa (empresa + papéis + admin/rh/
#                    funcionário + jornada + local). Devolve só IDs/dados.
#   - login        : função login(client, email) que autentica e coloca
#                    a empresa na sessão.
#   - criar_registro : factory para inserir batidas de ponto direto no banco.
# =====================================================================

import os
import time as _time

# Fuso fixo em UTC: torna os cálculos de horas/atrasos (que usam
# to_local/astimezone) determinísticos, independentes da máquina do CI.
os.environ['TZ'] = 'UTC'
try:
    _time.tzset()
except AttributeError:  # tzset não existe no Windows; CI roda em Linux.
    pass

from datetime import date, time  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import create_app  # noqa: E402
from E_Ponto.ext.db import db as _db  # noqa: E402

SENHA = "senha123"


@pytest.fixture
def app():
    """App Flask de teste, com banco SQLite em memória e isolado."""
    app = create_app(test_config={
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
        "WTF_CSRF_ENABLED": False,
    })

    # Contexto empurrado SÓ para criar/derrubar o schema — NÃO durante o
    # teste. Manter o contexto aberto durante as requisições embaralha a
    # sessão scoped do SQLAlchemy entre múltiplos clientes de teste.
    ctx = app.app_context()
    ctx.push()
    _db.create_all()
    ctx.pop()

    yield app

    ctx = app.app_context()
    ctx.push()
    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    """Cliente de teste: faz GET/POST na app sem precisar de servidor real."""
    return app.test_client()


@pytest.fixture
def usuario(app):
    """Cria um usuário ativo simples e devolve email + senha em texto puro."""
    from E_Ponto.ext.db import db
    from E_Ponto.models.user import User
    from E_Ponto.views.auth import bcrypt

    with app.app_context():
        user = User(
            name="Usuario de Teste",
            email="teste@eponto.com",
            cpf="12345678900",
            pis_nis="12345678900",
            password=bcrypt.generate_password_hash(SENHA).decode(),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
    return {"email": "teste@eponto.com", "senha": SENHA}


@pytest.fixture
def org(app):
    """Cria a organização completa para os testes e devolve um dict de IDs.

    empresa + papéis (super_admin/admin/rh/funcionario) + 3 usuários
    (admin@e.com, rh@e.com, func@e.com, todos com a mesma SENHA) +
    1 jornada padrão (8h/dia, entrada 08:00, tolerância 5min) ligada ao
    funcionário via escala + 1 local de trabalho com geofence de 200m.
    """
    from E_Ponto.ext.db import db
    from E_Ponto.models.user import User
    from E_Ponto.models.business import Business
    from E_Ponto.models.role import Role
    from E_Ponto.models.role_user import RoleUser
    from E_Ponto.models.jornada import Jornada
    from E_Ponto.models.escala import EscalaFuncionario
    from E_Ponto.models.local_trabalho import LocalTrabalho
    from E_Ponto.views.auth import bcrypt

    with app.app_context():
        roles = {n: Role(name=n) for n in
                 ["super_admin", "admin", "rh", "funcionario"]}
        for r in roles.values():
            db.session.add(r)
        db.session.flush()

        def mk(email, cpf):
            u = User(name=email.split('@')[0], email=email, cpf=cpf, pis_nis=cpf,
                     password=bcrypt.generate_password_hash(SENHA).decode(),
                     is_active=True, data_admissao=date(2020, 1, 1))
            db.session.add(u)
            db.session.flush()
            return u

        admin = mk("admin@e.com", "00000000001")
        rh = mk("rh@e.com", "00000000002")
        func = mk("func@e.com", "00000000003")

        emp = Business(owner_user_id=admin.id, corporate_name="Demo LTDA",
                       trade_name="Demo", cnpj="00000000000000",
                       cidade="Vila Velha", uf="ES", is_active=True)
        db.session.add(emp)
        db.session.flush()

        for u, role in [(admin, "admin"), (rh, "rh"), (func, "funcionario")]:
            db.session.add(RoleUser(user_id=u.id, business_id=emp.id,
                                    role_id=roles[role].id))

        jornada = Jornada(empresa_id=emp.id, nome="Padrao", tipo="padrao",
                          carga_horaria_semanal=40, horario_entrada=time(8, 0),
                          horario_saida=time(17, 0), intervalo_minutos=60,
                          tolerancia_minutos=5, ativo=True)
        db.session.add(jornada)
        db.session.flush()
        db.session.add(EscalaFuncionario(
            user_id=func.id, empresa_id=emp.id, jornada_id=jornada.id,
            data_inicio=date(2020, 1, 1), ativo=True))

        local = LocalTrabalho(empresa_id=emp.id, nome="Matriz",
                              latitude=-20.34, longitude=-40.29,
                              raio_metros=200, ativo=True)
        db.session.add(local)
        db.session.commit()

        return {
            "empresa_id": emp.id, "admin_id": admin.id, "rh_id": rh.id,
            "func_id": func.id, "jornada_id": jornada.id, "local_id": local.id,
            "senha": SENHA, "admin_email": "admin@e.com",
            "rh_email": "rh@e.com", "func_email": "func@e.com",
        }


@pytest.fixture
def login(org):
    """Devolve uma função login(client, email) que autentica e coloca a
    empresa do `org` na sessão."""
    def _login(client, email):
        resp = client.post("/auth/login",
                           data={"email": email, "password": org["senha"]})
        with client.session_transaction() as s:
            s["empresa_id"] = org["empresa_id"]
        return resp
    return _login


@pytest.fixture
def criar_registro(app, org):
    """Factory que insere uma batida de ponto direto no banco e devolve o id.

    Uso: criar_registro(user_id, 'entrada', dt_utc, lat=..., lon=...,
                         local_id=..., suspeito=False)
    """
    from E_Ponto.ext.db import db
    from E_Ponto.models.registro import Registro, TipoRegistro
    from E_Ponto.utils.nsr import get_next_nsr

    def _criar(user_id, tipo, dt_utc, lat=None, lon=None,
               local_id=None, suspeito=False, justificativa=None):
        with app.app_context():
            # get_next_nsr mantém a tabela NsrSequencia em sincronia, para
            # não colidir com registros criados depois pelas rotas reais.
            nsr = get_next_nsr(org["empresa_id"])
            tipo_enum = (tipo if isinstance(tipo, TipoRegistro)
                         else TipoRegistro(tipo))
            reg = Registro(
                nsr=nsr, empresa_id=org["empresa_id"], user_id=user_id,
                tipo=tipo_enum, timestamp_utc=dt_utc, latitude=lat,
                longitude=lon, local_trabalho_id=local_id, suspeito_geo=suspeito,
                justificativa=justificativa, hash_registro="0" * 64)
            db.session.add(reg)
            db.session.commit()
            return reg.id
    return _criar
