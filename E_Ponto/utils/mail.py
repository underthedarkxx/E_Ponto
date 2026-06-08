"""Helper para envio de e-mails.

Centraliza o uso do Flask-Mail. Em dev (MAIL_SUPPRESS_SEND=True) as
mensagens nao saem pelo SMTP, apenas aparecem no log.
"""

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
    """Envia um e-mail renderizando templates/emails/<template>.{txt,html}.

    to        Destinatario(s).
    subject   Assunto.
    template  Nome base do template em templates/emails/ (sem extensao).
    context   Variaveis passadas ao Jinja.

    Retorna a Message enviada, ou None se nao houver MAIL_SERVER.
    """
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.info(
            f'[MAIL skip] sem MAIL_SERVER configurado. Iria enviar para '
            f'{to}: "{subject}"'
        )
        return None

    recipients = [to] if isinstance(to, str) else to
    msg = Message(subject=subject, recipients=recipients)

    # Corpo texto sempre; HTML opcional
    msg.body = render_template(f'emails/{template}.txt', **context)
    try:
        msg.html = render_template(f'emails/{template}.html', **context)
    except Exception:
        pass

    mail.send(msg)

    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        current_app.logger.info(
            f'[MAIL dev] (suprimido) para {recipients}: "{subject}"'
        )
    return msg
