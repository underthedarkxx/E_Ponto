"""ext/mail: inicializacao do Flask-Mail.

Em dev, MAIL_SUPPRESS_SEND=True (ver ext/config) faz as mensagens serem
apenas logadas. Para envio real, configure SMTP no .env.prod.
"""

from flask_mail import Mail

# Singleton importado por utils/mail.py
mail = Mail()


def init_app(app):
    """Conecta o Flask-Mail ao app."""
    mail.init_app(app)
