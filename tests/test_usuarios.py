# =====================================================================
# tests/test_usuarios.py — Cadastro de usuários/funcionários e listagem
# Cobre: registro de usuário, registro de novos funcionários e a
# atualização correta da lista de usuários após o cadastro.
# =====================================================================


def _cadastrar(client, **campos):
    base = {
        "name": "Maria Souza", "email": "maria@e.com", "cpf": "99999999900",
        "pis_nis": "99999999900", "phone": "", "cargo": "Analista",
        "data_admissao": "2026-05-01", "role": "funcionario",
        "jornada_id": "0", "is_active": "y",
    }
    base.update(campos)
    return client.post("/admin/usuarios/novo", data=base)


def test_cadastro_de_usuario_cria_no_banco(app, org, login):
    """Admin cadastra um usuário novo → é criado no banco e vinculado."""
    c = app.test_client()
    login(c, org["admin_email"])
    resp = _cadastrar(c, email="maria@e.com")
    assert resp.status_code == 302       # redireciona para a lista

    with app.app_context():
        from E_Ponto.models.user import User
        u = User.query.filter_by(email="maria@e.com").first()
        assert u is not None
        assert u.name == "Maria Souza"
        assert "funcionario" in [r.name for r in u.roles]


def test_cadastro_de_funcionario_com_papel_correto(app, org, login):
    """Novo funcionário recebe especificamente o papel 'funcionario'."""
    c = app.test_client()
    login(c, org["admin_email"])
    _cadastrar(c, email="joao.novo@e.com", name="Joao Novo", role="funcionario")

    with app.app_context():
        from E_Ponto.models.user import User
        u = User.query.filter_by(email="joao.novo@e.com").first()
        assert u is not None
        papeis = [r.name for r in u.roles]
        assert papeis == ["funcionario"]


def test_lista_de_usuarios_atualiza(app, org, login):
    """Após cadastrar, a lista /admin/usuarios passa a exibir o novo usuário."""
    c = app.test_client()
    login(c, org["admin_email"])

    antes = c.get("/admin/usuarios").get_data(as_text=True)
    assert "Carla Lima" not in antes

    _cadastrar(c, name="Carla Lima", email="carla@e.com")

    depois = c.get("/admin/usuarios").get_data(as_text=True)
    assert "Carla Lima" in depois


def test_email_duplicado_nao_cria_segundo_usuario(app, org, login):
    """Cadastrar o mesmo e-mail de novo apenas vincula — não duplica o User."""
    c = app.test_client()
    login(c, org["admin_email"])
    _cadastrar(c, email="repetido@e.com", name="Primeiro")
    _cadastrar(c, email="repetido@e.com", name="Segundo")

    with app.app_context():
        from E_Ponto.models.user import User
        assert User.query.filter_by(email="repetido@e.com").count() == 1
