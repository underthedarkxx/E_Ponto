# =====================================================================
# tests/test_acesso.py — Controle de acesso (acesso via alteração de URL)
# Verifica que digitar a URL de uma área protegida não dá acesso a quem
# não tem permissão: anônimo é mandado pro login (302) e papel sem
# permissão recebe 403 (Forbidden).
# =====================================================================

import pytest

# Rotas administrativas (só admin/super_admin).
ROTAS_ADMIN = ["/admin/", "/admin/usuarios", "/admin/usuarios/novo",
               "/admin/locais", "/admin/locais/novo", "/admin/jornadas"]
# Rotas do RH (rh/admin/super_admin).
ROTAS_RH = ["/rh/", "/rh/registros", "/rh/retificacoes", "/rh/auditoria",
            "/rh/banco-horas", "/rh/relatorios"]
# Rotas de qualquer usuário logado.
ROTAS_LOGADO = ["/", "/funcionario/", "/ponto/bater", "/ponto/historico"]


def _client_logado(app, login, email):
    c = app.test_client()
    login(c, email)
    return c


@pytest.mark.parametrize("rota", ROTAS_ADMIN + ROTAS_RH + ROTAS_LOGADO)
def test_anonimo_redirecionado_para_login(app, org, rota):
    """Anônimo digitando qualquer URL protegida → 302 para o login."""
    resp = app.test_client().get(rota)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


@pytest.mark.parametrize("rota", ROTAS_ADMIN)
def test_funcionario_nao_acessa_admin(app, org, login, rota):
    """Funcionário tentando abrir área de admin pela URL → 403."""
    c = _client_logado(app, login, org["func_email"])
    assert c.get(rota).status_code == 403


@pytest.mark.parametrize("rota", ROTAS_RH)
def test_funcionario_nao_acessa_rh(app, org, login, rota):
    """Funcionário tentando abrir área de RH pela URL → 403."""
    c = _client_logado(app, login, org["func_email"])
    assert c.get(rota).status_code == 403


@pytest.mark.parametrize("rota", ROTAS_ADMIN)
def test_rh_nao_acessa_admin(app, org, login, rota):
    """RH não tem privilégio de admin → 403 nas rotas de admin."""
    c = _client_logado(app, login, org["rh_email"])
    assert c.get(rota).status_code == 403


@pytest.mark.parametrize("rota", ROTAS_RH)
def test_rh_acessa_rh(app, org, login, rota):
    """RH acessa suas próprias rotas (200)."""
    c = _client_logado(app, login, org["rh_email"])
    assert c.get(rota).status_code == 200


@pytest.mark.parametrize("rota", ROTAS_ADMIN + ROTAS_RH)
def test_admin_acessa_tudo(app, org, login, rota):
    """Admin acessa tanto /admin quanto /rh (200)."""
    c = _client_logado(app, login, org["admin_email"])
    assert c.get(rota).status_code == 200


def test_funcionario_nao_ve_comprovante_de_outro(app, org, login, criar_registro):
    """Funcionário não pode ver, alterando a URL, o comprovante de outro.

    O admin bate um ponto; o funcionário tenta abrir /ponto/comprovante/<id>
    desse registro alheio → 403.
    """
    from datetime import datetime, timezone
    reg_id = criar_registro(org["admin_id"], "entrada",
                            datetime(2026, 5, 20, 11, 0, tzinfo=timezone.utc))
    c = _client_logado(app, login, org["func_email"])
    assert c.get(f"/ponto/comprovante/{reg_id}").status_code == 403
