"""Decoradores reutilizaveis para as views.

role_required: restringe a rota a determinados papeis.
empresa_required: exige uma empresa selecionada na sessao.
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*role_names):
    """Exige que o usuario tenha ao menos um dos papeis informados.

    Uso:
        @role_required('admin', 'super_admin')
        def minha_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            user_role_names = [r.name for r in current_user.roles]
            if not any(r in user_role_names for r in role_names):
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def empresa_required(f):
    """Exige um empresa_id valido na sessao e expoe a empresa em g.empresa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Imports locais evitam ciclo (decorators -> models -> ...)
        from flask import session, g
        from E_Ponto.models.business import Business

        empresa_id = session.get('empresa_id')
        if not empresa_id:
            flash('Selecione uma empresa para continuar.', 'warning')
            return redirect(url_for('main.selecionar_empresa'))

        empresa = Business.query.get(empresa_id)
        if not empresa:
            # ID na sessao mas registro inexistente (apagado, etc.)
            flash('Empresa invalida.', 'danger')
            return redirect(url_for('main.selecionar_empresa'))

        g.empresa = empresa
        return f(*args, **kwargs)
    return decorated
