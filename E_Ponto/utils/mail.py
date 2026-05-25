# =====================================================================
# utils/mail.py — Helper para envio de e-mails
# ---------------------------------------------------------------------
# Centraliza o envio para que as views nao precisem conhecer Flask-Mail.
#
# Em dev (MAIL_SUPPRESS_SEND=True), as mensagens nao saem pelo SMTP —
# apenas aparecem no log do Flask. Isso evita precisar configurar
# senha de Gmail/SMTP durante desenvolvimento.
# =====================================================================

from typing import Optional, Any
from flask import current_app, render_template
from flask_mail import Message

from E_Ponto.ext.mail import mail


def send_notification(
    to: str | list[str],
    subject: str,
    template: str,
    **context: Any,
) -> Optional[Message]:
    """
    Envia um e-mail renderizando dois templates Jinja:
      - templates/emails/<template>.txt   (corpo texto puro)
      - templates/emails/<template>.html  (corpo HTML, opcional)

    Parametros:
        to        Endereco(s) destinatario(s).
        subject   Assunto da mensagem.
        template  Nome base do template em templates/emails/ (sem ext).
        context   Variaveis passadas para o Jinja.

    Retorna:
        A Message enviada, ou None se nao houver MAIL_SERVER configurado.
    """
    # Sem MAIL_SERVER nao tem pra onde mandar — apenas loga e sai.
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.info(
            f'[MAIL skip] sem MAIL_SERVER configurado. Iria enviar para '
            f'{to}: "{subject}"'
        )
        return None

    recipients = [to] if isinstance(to, str) else to
    msg = Message(subject=subject, recipients=recipients)

    # Corpo texto sempre. Corpo HTML opcional.
    msg.body = render_template(f'emails/{template}.txt', **context)
    try:
        msg.html = render_template(f'emails/{template}.html', **context)
    except Exception:
        # Sem template HTML: tudo bem, fica so com texto.
        pass

    mail.send(msg)

    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        current_app.logger.info(
            f'[MAIL dev] (suprimido) para {recipients}: "{subject}"'
        )
    return msg
