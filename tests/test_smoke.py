# =====================================================================
# tests/test_smoke.py — Testes de fumaça ("smoke tests")
# ---------------------------------------------------------------------
# "Smoke test" = verificação rápida de que o básico funciona: a app
# sobe e as rotas principais respondem. Não cobrem regras de negócio a
# fundo; servem para pegar quebras grosseiras logo de cara.
#
# Cada função `test_*` é um teste. Os parâmetros (client, usuario) são
# os fixtures definidos em conftest.py — o pytest os injeta sozinho.
# A palavra `assert` é a checagem: se a expressão for falsa, o teste falha.
# =====================================================================


def test_pagina_login_responde(client):
    """A tela de login é pública: um GET deve devolver 200 (OK)."""
    resp = client.get("/auth/login")
    assert resp.status_code == 200


def test_home_exige_login(client):
    """A home tem @login_required: sem sessão, redireciona (302) p/ o login."""
    resp = client.get("/")
    assert resp.status_code == 302
    # O Flask-Login manda para /auth/login (com ?next=... no fim).
    assert "/auth/login" in resp.headers["Location"]


def test_login_com_credenciais_validas(client, usuario):
    """Login válido autentica e redireciona para a home (main.index = '/')."""
    resp = client.post(
        "/auth/login",
        data={"email": usuario["email"], "password": usuario["senha"]},
        follow_redirects=False,  # queremos VER o 302, não segui-lo
    )
    assert resp.status_code == 302
    # A home (main.index) atende tanto "/" quanto "/index"; o url_for pode
    # gerar qualquer um dos dois. O que importa é que NÃO voltou pro login.
    assert resp.headers["Location"].endswith(("/", "/index"))
    assert "/auth/login" not in resp.headers["Location"]


def test_login_com_senha_errada(client, usuario):
    """Senha errada não autentica: continua na tela de login (200)."""
    resp = client.post(
        "/auth/login",
        data={"email": usuario["email"], "password": "senha-errada"},
        follow_redirects=False,
    )
    # Sem login bem-sucedido, a view só re-renderiza o formulário (200),
    # sem redirecionar.
    assert resp.status_code == 200
