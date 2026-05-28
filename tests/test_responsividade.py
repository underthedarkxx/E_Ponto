# =====================================================================
# tests/test_responsividade.py — Fundamentos de responsividade
# Responsividade visual de verdade exige um navegador (ex.: Playwright).
# Aqui validamos automaticamente os PRÉ-REQUISITOS que tornam o layout
# responsivo: a meta tag viewport e o framework CSS (Bootstrap) presentes
# nas páginas, além do uso de grid responsivo (classes col-*).
# =====================================================================


def test_login_tem_viewport_e_bootstrap(client):
    """A página pública de login declara viewport e carrega o Bootstrap."""
    html = client.get("/auth/login").get_data(as_text=True)
    assert '<meta name="viewport"' in html
    assert "width=device-width" in html
    assert "bootstrap" in html.lower()


def test_dashboard_funcionario_e_responsivo(app, org, login):
    """Página autenticada herda a base responsiva (viewport) e usa grid."""
    c = app.test_client()
    login(c, org["func_email"])
    html = c.get("/funcionario/").get_data(as_text=True)
    assert "width=device-width" in html
    # Grid responsivo do Bootstrap (colunas que se adaptam ao tamanho).
    assert "col-md" in html or "col-lg" in html or "container" in html


def test_pagina_de_locais_usa_tabela(app, org, login):
    """A listagem usa componentes do Bootstrap (tabela estilizada)."""
    c = app.test_client()
    login(c, org["admin_email"])
    html = c.get("/admin/locais").get_data(as_text=True)
    assert "table" in html
