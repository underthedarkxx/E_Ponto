# =====================================================================
# tests/test_dashboard.py — Atualização dos dashboards
# Verifica que o painel do funcionário reflete as batidas registradas
# (horas trabalhadas do mês) e que o painel do RH responde.
# =====================================================================

from datetime import datetime, timezone, date


def _hoje_utc(h):
    t = date.today()
    return datetime(t.year, t.month, t.day, h, 0, tzinfo=timezone.utc)


def test_dashboard_funcionario_reflete_batidas(app, org, login, criar_registro):
    """Dashboard começa sem 4h trabalhadas; após bater 08-12 hoje, passa a
    exibir '04:00' nas horas trabalhadas do mês."""
    c = app.test_client()
    login(c, org["func_email"])

    antes = c.get("/funcionario/").get_data(as_text=True)
    assert antes.count("04:00") == 0

    # 4 horas trabalhadas hoje.
    criar_registro(org["func_id"], "entrada", _hoje_utc(8),
                   lat=-20.34, lon=-40.29, local_id=org["local_id"])
    criar_registro(org["func_id"], "saida", _hoje_utc(12),
                   lat=-20.34, lon=-40.29, local_id=org["local_id"])

    depois = c.get("/funcionario/").get_data(as_text=True)
    assert "04:00" in depois


def test_dashboard_funcionario_responde(app, org, login):
    """Painel do funcionário abre normalmente (200) mesmo sem batidas."""
    c = app.test_client()
    login(c, org["func_email"])
    assert c.get("/funcionario/").status_code == 200


def test_dashboard_rh_responde(app, org, login):
    """Painel do RH abre normalmente (200)."""
    c = app.test_client()
    login(c, org["rh_email"])
    assert c.get("/rh/").status_code == 200
