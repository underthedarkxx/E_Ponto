# =====================================================================
# tests/test_retificacao.py — Ajustes manuais de registros e justificativa
# Fluxo: o funcionário solicita a correção de uma batida (com motivo);
# o RH aprova → cria um novo registro tipo ALTERACAO (o original nunca é
# apagado) — ou rejeita → nenhum registro novo é criado.
# =====================================================================

from datetime import datetime, timezone


def _abrir_retificacao(app, org, login, reg_id, motivo, novo_ts):
    """Abre a retificação pela rota do funcionário (testa o endpoint)."""
    c = app.test_client()
    login(c, org["func_email"])
    c.post(f"/funcionario/retificar/{reg_id}", data={
        "motivo": motivo,
        "novo_timestamp": novo_ts,   # formato '%Y-%m-%dT%H:%M'
    })
    with app.app_context():
        from E_Ponto.models.retificacao import Retificacao
        return Retificacao.query.order_by(Retificacao.id.desc()).first().id


def _criar_retificacao_db(app, org, reg_id, motivo, novo_ts):
    """Cria a retificação direto no banco (para os testes de decisão usarem
    apenas o client do RH — evita o efeito de múltiplos clients logados no
    mesmo teste com o pool de conexão único do SQLite em memória)."""
    from datetime import datetime
    with app.app_context():
        from E_Ponto.ext.db import db
        from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
        ret = Retificacao(
            registro_id=reg_id, empresa_id=org["empresa_id"],
            solicitante_id=org["func_id"],
            novo_timestamp=datetime.strptime(novo_ts, "%Y-%m-%dT%H:%M"),
            motivo=motivo, status=StatusRetificacao.PENDENTE)
        db.session.add(ret)
        db.session.commit()
        return ret.id


def test_funcionario_solicita_retificacao_com_justificativa(app, org, login,
                                                            criar_registro):
    """Pedido de correção é criado em estado PENDENTE com o motivo."""
    reg_id = criar_registro(org["func_id"], "entrada",
                            datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc))
    ret_id = _abrir_retificacao(app, org, login, reg_id,
                                "Esqueci de bater; entrei 08:00",
                                "2026-05-20T08:00")
    with app.app_context():
        from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
        ret = Retificacao.query.get(ret_id)
        assert ret.status == StatusRetificacao.PENDENTE
        assert ret.motivo.startswith("Esqueci")
        assert ret.registro_id == reg_id


def test_rh_aprova_cria_registro_alteracao(app, org, login, criar_registro):
    """RH aprova → status APROVADA e um novo Registro tipo ALTERACAO é
    criado com o horário corrigido e a justificativa."""
    reg_id = criar_registro(org["func_id"], "entrada",
                            datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc))
    ret_id = _criar_retificacao_db(app, org, reg_id,
                                   "Ajuste para 08:00", "2026-05-20T08:00")

    with app.app_context():
        from E_Ponto.models.registro import Registro, TipoRegistro
        antes = Registro.query.filter_by(tipo=TipoRegistro.ALTERACAO).count()

    c = app.test_client()
    login(c, org["rh_email"])
    resp = c.post(f"/rh/retificacoes/{ret_id}/decidir",
                  data={"acao": "aprovar", "observacao": "Confere"})
    assert resp.status_code == 302

    with app.app_context():
        from E_Ponto.models.registro import Registro, TipoRegistro
        from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
        assert Retificacao.query.get(ret_id).status == StatusRetificacao.APROVADA
        alteracoes = Registro.query.filter_by(tipo=TipoRegistro.ALTERACAO).all()
        assert len(alteracoes) == antes + 1
        nova = alteracoes[-1]
        assert nova.justificativa == "Ajuste para 08:00"
        # Registro original continua existindo (rastreabilidade).
        assert Registro.query.get(reg_id) is not None


def test_rh_rejeita_nao_cria_registro(app, org, login, criar_registro):
    """RH rejeita → status REJEITADA e nenhum registro de alteração é criado."""
    reg_id = criar_registro(org["func_id"], "entrada",
                            datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc))
    ret_id = _criar_retificacao_db(app, org, reg_id,
                                   "Pedido indevido", "2026-05-20T08:00")

    c = app.test_client()
    login(c, org["rh_email"])
    c.post(f"/rh/retificacoes/{ret_id}/decidir",
           data={"acao": "rejeitar", "observacao": "Sem comprovacao"})

    with app.app_context():
        from E_Ponto.models.registro import Registro, TipoRegistro
        from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
        assert Retificacao.query.get(ret_id).status == StatusRetificacao.REJEITADA
        assert Registro.query.filter_by(tipo=TipoRegistro.ALTERACAO).count() == 0
