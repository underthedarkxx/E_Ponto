# =====================================================================
# ext/mail — Inicializacao do Flask-Mail
# ---------------------------------------------------------------------
# Singleton da extensao Flask-Mail. Em dev, MAIL_SUPPRESS_SEND=True
# (definido no ext/config) faz com que as mensagens sejam apenas
# logadas no console, sem precisar de SMTP configurado.
#
# Para envio real em producao, configure no .env.prod:
#     MAIL_SERVER=smtp.gmail.com
#     MAIL_PORT=587
#     MAIL_USE_TLS=True
#     MAIL_USERNAME=...
#     MAIL_PASSWORD=...        (senha de aplicativo, nao a senha real)
#     MAIL_SUPPRESS_SEND=False
# =====================================================================

from flask_mail import Mail

# Singleton importado por utils/mail.py para enviar mensagens.
mail = Mail()


def init_app(app):
    """Conecta o Flask-Mail ao app."""
    mail.init_app(app)
