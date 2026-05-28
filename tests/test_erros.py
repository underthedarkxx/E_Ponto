# =====================================================================
# tests/test_erros.py — Páginas de erro customizadas (403/404)
# Verifica que os erros retornam o status correto E renderizam a página
# amigável do sistema (não o traceback padrão do Flask).
# =====================================================================


def test_404_pagina_inexistente(client):
    """URL inexistente → 404 com a página customizada."""
    resp = client.get("/rota/que/nao/existe")
    assert resp.status_code == 404
    html = resp.get_data(as_text=True)
    assert "404" in html
    assert "não encontrada" in html


def test_403_acesso_negado_renderiza_pagina(app, org, login):
    """Funcionário em rota de admin → 403 com a página 'Acesso negado'."""
    c = app.test_client()
    login(c, org["func_email"])
    resp = c.get("/admin/usuarios")
    assert resp.status_code == 403
    assert "Acesso negado" in resp.get_data(as_text=True)
