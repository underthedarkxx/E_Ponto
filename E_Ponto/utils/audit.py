# pyright: reportCallIssue=false
"""Helper para gravar entradas de auditoria (AuditLog) a partir das views.

Captura automaticamente user_id (current_user), empresa_id (sessao) e
ip_address (request). Por padrao apenas adiciona ao session; o chamador
deve fazer commit (ou passar commit=True).
"""

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
    """Grava uma entrada no audit log.

    acao         Nome da acao em SCREAMING_SNAKE_CASE (ex.: 'CRIAR_REGISTRO').
    tabela       Tabela afetada (ex.: 'registros', 'users').
    registro_id  ID da linha afetada (opcional).
    dados_antes  Estado anterior (serializado em JSON).
    dados_depois Estado novo (serializado em JSON).
    empresa_id   Override; se None, le da session.
    commit       Se True, faz commit ao final (padrao False).
    """
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    if has_request_context():
        if current_user.is_authenticated:
            user_id = current_user.id
        ip_address = request.remote_addr
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
