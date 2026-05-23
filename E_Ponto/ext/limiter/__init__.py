# =====================================================================
# ext/limiter — Rate Limiting (Flask-Limiter)
# ---------------------------------------------------------------------
# Limita o número de requisições que um cliente pode fazer em um dado
# intervalo. Usado para mitigar ataques de força bruta no login,
# DoS leve, scraping abusivo, etc.
# =====================================================================

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# `key_func` define como identificar o "cliente". Aqui usamos o IP
# remoto (get_remote_address). Em apps autenticadas, dá pra usar
# `lambda: current_user.id` para limitar por usuário.
#
# `default_limits` são limites globais aplicados a todas as rotas,
# salvo quando uma rota define seu próprio limite via decorator.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def init_app(app):
    """Inicializa o limiter usando o storage configurado em app.config."""
    # Flask-Limiter le RATELIMIT_STORAGE_URI direto do app.config
    # (definido em ext/config). Por padrão usa memória in-process;
    # em produção é melhor apontar para Redis para que o contador
    # seja compartilhado entre workers.
    limiter.init_app(app)
