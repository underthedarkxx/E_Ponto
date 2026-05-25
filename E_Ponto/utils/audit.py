# pyright: reportCallIssue=false
# =====================================================================
# utils/audit.py — Helper para gravar logs de auditoria
# ---------------------------------------------------------------------
# Centraliza a criacao de AuditLog para ser chamado das views.
# Captura automaticamente:
#   - user_id (de current_user, se logado)
#   - empresa_id (da sessao Flask)
#   - ip_address (do request)
#
# Uso tipico em uma view:
#     from E_Ponto.utils.audit import log_action
#     log_action('CRIAR_REGISTRO', 'registros', reg.id,
#                dados_depois={'tipo': reg.tipo.value, 'nsr': reg.nsr})
#
# IMPORTANTE: a funcao apenas adiciona ao session — quem chamou
# precisa fazer db.session.commit() depois (ou ja ter feito).
# =====================================================================

import json
from typing import Optional, Any

from flask import request, session, has_request_context
from flask_login import current_user

from E_Ponto.ext.db import db
from E_Ponto.models.audit_log import AuditLog


def log_action(
    acao: str,
    tabela: str,
    registro_id: Optional[int] = None,
    dados_antes: Optional[dict[str, Any]] = None,
    dados_depois: Optional[dict[str, Any]] = None,
    empresa_id: Optional[int] = None,
    commit: bool = False,
) -> AuditLog:
    """
    Grava uma entrada no audit log.

    Parametros:
        acao         Nome da acao em SCREAMING_SNAKE_CASE
                     (ex.: 'CRIAR_REGISTRO', 'APROVAR_RETIFICACAO').
        tabela       Nome da tabela afetada (ex.: 'registros', 'users').
        registro_id  ID da linha afetada (opcional para acoes "soltas").
        dados_antes  Dict com o estado anterior (serializado em JSON).
        dados_depois Dict com o estado novo (serializado em JSON).
        empresa_id   Override; se None, le da session do Flask.
        commit       Se True, faz db.session.commit() ao final. Por
                     padrao False — a view chama commit junto com as
                     outras alteracoes (transacao atomica).
    """
    # user_id: pega do current_user se houver request HTTP ativo
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    if has_request_context():
        if current_user.is_authenticated:
            user_id = current_user.id
        # request.remote_addr respeita X-Forwarded-For se configurado
        # no proxy (Nginx, etc.). Em dev local, vira "127.0.0.1".
        ip_address = request.remote_addr
        # Se empresa_id nao foi passado, pega da sessao
        if empresa_id is None:
            empresa_id = session.get('empresa_id')

    entry = AuditLog(
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        user_id=user_id,
        empresa_id=empresa_id,
        ip_address=ip_address,
        dados_antes=json.dumps(dados_antes, default=str) if dados_antes else None,
        dados_depois=json.dumps(dados_depois, default=str) if dados_depois else None,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry
