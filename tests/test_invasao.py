# =====================================================================
# tests/test_invasao.py — Testes de INVASÃO / segurança (pentest)
# Contexto: avaliação de segurança autorizada do próprio projeto.
# Cobre: SQL injection, XSS armazenado, IDOR (acesso a recurso de
# outrem), escalada de privilégio, navegação forçada, open redirect
# e proteção CSRF.
# =====================================================================

from sqlalchemy.pool import StaticPool

from app import create_app


def _esta_logado(client):
    return client.get("/").status_code == 200


# ------------------------- SQL injection -----------------------------
def test_sql_injection_no_login_nao_autentica(client, org):
    """Payload clássico de SQLi no e-mail não burla a autenticação."""
    resp = client.post("/auth/login", data={
        "email": "admin@e.com' OR '1'='1", "password": "qualquer"})
    assert resp.status_code == 200          # nada de 500/erro de SQL
    assert not _esta_logado(client)


def test_sql_injection_em_filtro_nao_quebra(app, org, login):
    """Injeção nos filtros de busca do RH é neutralizada pelo ORM (sem 500)."""
    c = app.test_client()
    login(c, org["rh_email"])
    r1 = c.get("/rh/registros?data=' OR '1'='1")
    r2 = c.get("/rh/registros?user_id=1;DROP TABLE registros")
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Tabela continua de pé.
    with app.app_context():
        from E_Ponto.models.registro import Registro
        assert Registro.query.count() == 0   # existe e responde (vazia)


# ------------------------- XSS armazenado ----------------------------
def test_xss_no_nome_e_escapado(app, org, login):
    """Nome com <script> é escapado no HTML (Jinja autoescape) — não executa."""
    payload = "<script>alert('xss')</script>"
    c = app.test_client()
    login(c, org["admin_email"])
    c.post("/admin/usuarios/novo", data={
        "name": payload, "email": "xss@e.com", "cpf": "", "pis_nis": "",
        "phone": "", "cargo": "", "data_admissao": "2026-05-01",
        "role": "funcionario", "jornada_id": "0", "is_active": "y"})

    html = c.get("/admin/usuarios").get_data(as_text=True)
    assert payload not in html               # não aparece cru
    assert "&lt;script&gt;" in html          # aparece escapado


# ----------------------------- IDOR ----------------------------------
def test_idor_comprovante_de_outro_usuario(app, org, login, criar_registro):
    """Funcionário não acessa o comprovante de outro só trocando o id na URL."""
    from datetime import datetime, timezone
    reg_id = criar_registro(org["admin_id"], "entrada",
                            datetime(2026, 5, 20, 11, tzinfo=timezone.utc))
    c = app.test_client()
    login(c, org["func_email"])
    assert c.get(f"/ponto/comprovante/{reg_id}").status_code == 403


def test_idor_retificacao_de_registro_alheio(app, org, login, criar_registro):
    """Funcionário não abre retificação para um registro que não é dele."""
    from datetime import datetime, timezone
    reg_id = criar_registro(org["admin_id"], "entrada",
                            datetime(2026, 5, 20, 11, tzinfo=timezone.utc))
    c = app.test_client()
    login(c, org["func_email"])
    # A view nega e redireciona (302) — não cria retificação.
    resp = c.post(f"/funcionario/retificar/{reg_id}",
                  data={"motivo": "tentativa", "novo_timestamp": ""})
    assert resp.status_code in (302, 403)
    with app.app_context():
        from E_Ponto.models.retificacao import Retificacao
        assert Retificacao.query.count() == 0


# ---------------------- escalada de privilégio -----------------------
def test_escalada_funcionario_nao_cria_usuario(app, org, login):
    """Funcionário não consegue criar usuário pela rota de admin (403)."""
    c = app.test_client()
    login(c, org["func_email"])
    resp = c.post("/admin/usuarios/novo", data={
        "name": "Hacker Admin", "email": "hacker@e.com", "role": "admin",
        "jornada_id": "0", "data_admissao": "2026-05-01", "is_active": "y",
        "cpf": "", "pis_nis": "", "phone": "", "cargo": ""})
    assert resp.status_code == 403
    with app.app_context():
        from E_Ponto.models.user import User
        assert User.query.filter_by(email="hacker@e.com").first() is None


# ---------------------- navegação forçada ----------------------------
def test_navegacao_forcada_anonimo_nao_bate_ponto(app, org):
    """Anônimo dando POST direto em /ponto/bater é mandado pro login e
    nenhum registro é criado."""
    c = app.test_client()
    resp = c.post("/ponto/bater", data={
        "tipo": "entrada", "local_trabalho_id": "0",
        "latitude": "", "longitude": "", "precisao": ""})
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]
    with app.app_context():
        from E_Ponto.models.registro import Registro
        assert Registro.query.count() == 0


# ------------------------- open redirect -----------------------------
def test_open_redirect_externo_bloqueado(client, org):
    """?next=https://evil.com NÃO redireciona para fora do site (CWE-601)."""
    resp = client.post("/auth/login?next=https://evil.com",
                       data={"email": org["func_email"], "password": org["senha"]})
    assert resp.status_code == 302
    assert "evil.com" not in resp.headers["Location"]


def test_open_redirect_protocol_relative_bloqueado(client, org):
    """?next=//evil.com também é recusado."""
    resp = client.post("/auth/login?next=//evil.com",
                       data={"email": org["func_email"], "password": org["senha"]})
    assert resp.status_code == 302
    assert "evil.com" not in resp.headers["Location"]


def test_next_local_e_respeitado(client, org):
    """Um next LOCAL legítimo continua funcionando."""
    resp = client.post("/auth/login?next=/ponto/historico",
                       data={"email": org["func_email"], "password": org["senha"]})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ponto/historico")


# ----------------------------- CSRF ----------------------------------
def test_csrf_bloqueia_post_sem_token():
    """Com CSRF ativo (modo não-teste), POST sem token é rejeitado (400),
    e o formulário de login embute um token."""
    app = create_app(test_config={
        "TESTING": False, "WTF_CSRF_ENABLED": True, "SECRET_KEY": "k",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False}, "poolclass": StaticPool},
    })
    with app.app_context():
        from E_Ponto.ext.db import db
        db.create_all()
    c = app.test_client()
    html = c.get("/auth/login").get_data(as_text=True)
    assert "csrf_token" in html              # token embutido no form
    resp = c.post("/auth/login",
                  data={"email": "a@e.com", "password": "senha123"})
    assert resp.status_code == 400           # sem token → recusado
