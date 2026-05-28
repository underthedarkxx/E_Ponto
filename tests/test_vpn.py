# =====================================================================
# tests/test_vpn.py — Comportamento sob IP de VPN
# Uma VPN muda o IP de origem, mas NÃO a geolocalização (que vem do GPS
# do dispositivo). Verifica que:
#   - o IP de origem é registrado na batida (auditoria);
#   - a decisão de geofence (suspeito ou não) depende do GPS, não do IP
#     — ou seja, usar VPN não burla nem quebra o controle de localização.
# =====================================================================

IP_VPN = "203.0.113.45"      # IP de exemplo (bloco TEST-NET-3, RFC 5737)


def _bater(client, org, lat, lon, ip):
    return client.post("/ponto/bater", data={
        "tipo": "entrada", "local_trabalho_id": str(org["local_id"]),
        "latitude": str(lat), "longitude": str(lon), "precisao": "10",
        "justificativa": "",
    }, environ_base={"REMOTE_ADDR": ip})


def test_ip_de_origem_e_registrado(app, org, login):
    """A batida grava o IP de origem (mesmo vindo de uma VPN)."""
    c = app.test_client()
    login(c, org["func_email"])
    _bater(c, org, -20.34, -40.29, IP_VPN)

    with app.app_context():
        from E_Ponto.models.registro import Registro
        reg = (Registro.query.filter_by(user_id=org["func_id"])
               .order_by(Registro.id.desc()).first())
        assert reg.ip_address == IP_VPN


def test_geofence_independe_do_ip(app, org, login):
    """Mesma localização (dentro do raio) vinda de IPs diferentes →
    nunca é marcada como suspeita. O geofence usa GPS, não IP."""
    c = app.test_client()
    login(c, org["func_email"])
    _bater(c, org, -20.34, -40.29, "10.0.0.1")        # IP "interno"
    _bater(c, org, -20.34, -40.29, IP_VPN)            # IP "de VPN"

    with app.app_context():
        from E_Ponto.models.registro import Registro
        regs = Registro.query.filter_by(user_id=org["func_id"]).all()
        assert len(regs) == 2
        assert all(r.suspeito_geo is False for r in regs)


def test_localizacao_fora_do_raio_e_suspeita_mesmo_via_vpn(app, org, login):
    """GPS fora do raio é suspeito independentemente do IP — confirma que a
    decisão vem do GPS, não da rede."""
    c = app.test_client()
    login(c, org["func_email"])
    _bater(c, org, -23.55, -46.63, IP_VPN)            # longe do local

    with app.app_context():
        from E_Ponto.models.registro import Registro
        reg = (Registro.query.filter_by(user_id=org["func_id"])
               .order_by(Registro.id.desc()).first())
        assert reg.suspeito_geo is True
