# =====================================================================
# tests/test_auth.py — Autenticação e validação de credenciais
# Cobre: usuário/senha não cadastradas; limites de caracteres de
# login (e-mail) e senha (mínimo e o limite de 72 bytes do bcrypt).
# =====================================================================


def _esta_logado(client):
    """Logado = consegue abrir a home (/) sem ser redirecionado p/ login."""
    return client.get("/").status_code == 200


def test_login_usuario_nao_cadastrado(client, org):
    """E-mail inexistente: não autentica e permanece na tela de login."""
    resp = client.post("/auth/login",
                       data={"email": "naoexiste@e.com", "password": "qualquer"})
    assert resp.status_code == 200          # re-renderiza o form, não redireciona
    assert not _esta_logado(client)


def test_login_senha_errada(client, org):
    """Usuário existe mas a senha está errada: não autentica."""
    resp = client.post("/auth/login",
                       data={"email": org["func_email"], "password": "errada"})
    assert resp.status_code == 200
    assert not _esta_logado(client)


def test_login_credenciais_validas(client, org):
    """Credenciais corretas autenticam e redirecionam (302)."""
    resp = client.post("/auth/login",
                       data={"email": org["func_email"], "password": org["senha"]})
    assert resp.status_code == 302
    assert _esta_logado(client)


def test_senha_curta_rejeitada(client, org):
    """Senha com menos de 6 caracteres é barrada pela validação do form."""
    resp = client.post("/auth/login",
                       data={"email": org["func_email"], "password": "123"})
    assert resp.status_code == 200
    assert not _esta_logado(client)


def test_email_invalido_rejeitado(client, org):
    """E-mail em formato inválido é barrado pela validação do form."""
    resp = client.post("/auth/login",
                       data={"email": "isto-nao-e-email", "password": org["senha"]})
    assert resp.status_code == 200
    assert not _esta_logado(client)


def test_senha_gigante_nao_derruba_login(client, org):
    """Senha acima de 72 bytes (limite do bcrypt) NÃO pode gerar erro 500.

    É tratada como credencial inválida — defesa contra ataque de
    disponibilidade na rota de login.
    """
    resp = client.post("/auth/login",
                       data={"email": org["func_email"], "password": "A" * 500})
    assert resp.status_code == 200          # nunca 500
    assert not _esta_logado(client)
