# =====================================================================
# tests/test_ponto.py — Bater ponto (data/hora/localização) e histórico
# Cobre: captura correta de data/hora e localização ao registrar o ponto,
# a marcação de "suspeito" quando fora do raio, e o histórico do usuário.
# =====================================================================

from datetime import datetime, timezone


def _bater(client, org, lat, lon, tipo="entrada"):
    return client.post("/ponto/bater", data={
        "tipo": tipo, "local_trabalho_id": str(org["local_id"]),
        "latitude": str(lat), "longitude": str(lon), "precisao": "10",
        "justificativa": "",
    })


def test_bater_ponto_dentro_do_raio(app, org, login):
    """Bate ponto na coordenada do local → registro criado, NÃO suspeito,
    com data/hora atual e a localização gravada."""
    c = app.test_client()
    login(c, org["func_email"])
    resp = _bater(c, org, -20.34, -40.29)        # exatamente no local
    assert resp.status_code == 302               # vai para o comprovante

    with app.app_context():
        from E_Ponto.models.registro import Registro
        reg = (Registro.query.filter_by(user_id=org["func_id"])
               .order_by(Registro.id.desc()).first())
        assert reg is not None
        assert reg.suspeito_geo is False
        # Localização gravada corretamente.
        assert abs(float(reg.latitude) - (-20.34)) < 1e-6
        assert abs(float(reg.longitude) - (-40.29)) < 1e-6
        # Data/hora: deve ser ~agora (gravado em UTC).
        ts = reg.timestamp_utc
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        assert abs((datetime.utcnow() - ts).total_seconds()) < 120


def test_bater_ponto_fora_do_raio_marca_suspeito(app, org, login):
    """Bate ponto longe do local (outra cidade) → salvo, mas suspeito_geo=True
    (a batida não é bloqueada, conforme exigência legal)."""
    c = app.test_client()
    login(c, org["func_email"])
    resp = _bater(c, org, -23.55, -46.63)        # São Paulo, ~longe demais
    assert resp.status_code == 302

    with app.app_context():
        from E_Ponto.models.registro import Registro
        reg = (Registro.query.filter_by(user_id=org["func_id"])
               .order_by(Registro.id.desc()).first())
        assert reg is not None
        assert reg.suspeito_geo is True


def test_historico_mostra_batidas(app, org, login, criar_registro):
    """O histórico do funcionário lista suas batidas (NSR e data/hora)."""
    criar_registro(org["func_id"], "entrada",
                   datetime(2026, 5, 20, 9, 15, tzinfo=timezone.utc),
                   lat=-20.34, lon=-40.29, local_id=org["local_id"])
    c = app.test_client()
    login(c, org["func_email"])
    html = c.get("/ponto/historico").get_data(as_text=True)
    assert "20/05/2026 09:15:00" in html         # data/hora local (TZ=UTC)


def test_historico_so_mostra_proprias_batidas(app, org, login, criar_registro):
    """Funcionário só vê as próprias batidas — não as de outro usuário."""
    # Batida do ADMIN (não deve aparecer no histórico do funcionário).
    criar_registro(org["admin_id"], "entrada",
                   datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc))
    # Batida do FUNCIONÁRIO.
    criar_registro(org["func_id"], "entrada",
                   datetime(2026, 5, 21, 8, 0, tzinfo=timezone.utc))
    c = app.test_client()
    login(c, org["func_email"])
    html = c.get("/ponto/historico").get_data(as_text=True)
    assert "21/05/2026 08:00:00" in html
    assert "21/05/2026 10:00:00" not in html
