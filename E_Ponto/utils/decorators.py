# =====================================================================
# utils/decorators.py — Decoradores reutilizáveis para as views
# ---------------------------------------------------------------------
# Decoradores envolvem uma função e adicionam comportamento antes ou
# depois dela. Aqui temos dois:
#   - role_required: restringe rota a usuários com determinados papéis
#   - empresa_required: garante que há empresa selecionada na sessão
# =====================================================================

from functools import wraps  # preserva nome/docstring da função decorada
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*role_names):
    """
    Decorator: requires user to have at least one of the given roles
    in any business.

    Uso:
        @role_required('admin', 'super_admin')
        def minha_view(): ...
    """
    # Por usar argumentos (*role_names), temos um nível extra:
    # role_required('admin') retorna o `decorator`, que é o decorador real.
    def decorator(f):
        # @wraps(f) faz `decorated.__name__ == f.__name__` — importante
        # para que o Flask consiga registrar a rota corretamente.
        @wraps(f)
        def decorated(*args, **kwargs):
            # 1) usuário precisa estar logado
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            # 2) usuário precisa ter pelo menos um dos papéis exigidos
            user_role_names = [r.name for r in current_user.roles]
            if not any(r in user_role_names for r in role_names):
                # abort(403) gera resposta HTTP "Forbidden".
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def empresa_required(f):
    """
    Decorator: requires a valid empresa_id in session.
    Coloca a empresa em `g.empresa` para a view usar.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Imports aqui dentro evitam ciclo (decorators -> models -> ...).
        from flask import session, g
        from E_Ponto.models.business import Business

        empresa_id = session.get('empresa_id')
        if not empresa_id:
            flash('Selecione uma empresa para continuar.', 'warning')
            return redirect(url_for('main.selecionar_empresa'))

        empresa = Business.query.get(empresa_id)
        if not empresa:
            # ID pendurado na sessão mas o registro sumiu (apagado, etc.).
            flash('Empresa invalida.', 'danger')
            return redirect(url_for('main.selecionar_empresa'))

        # `g` é um objeto da requisição corrente. Disponibiliza
        # `g.empresa` para qualquer código rodando neste request.
        g.empresa = empresa
        return f(*args, **kwargs)
    return decorated
