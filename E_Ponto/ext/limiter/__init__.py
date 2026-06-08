"""ext/limiter: rate limiting via Flask-Limiter.

Identifica o cliente pelo IP remoto e aplica limites globais, mitigando
forca bruta no login e abuso de requisicoes.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def init_app(app):
    """Inicializa o limiter usando o storage configurado em app.config.

    Le RATELIMIT_STORAGE_URI de ext/config (memoria por padrao; em
    producao prefira Redis para compartilhar o contador entre workers).
    """
    limiter.init_app(app)
