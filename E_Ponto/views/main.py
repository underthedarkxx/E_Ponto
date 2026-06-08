"""Rotas principais: home e selecao da empresa ativa.

Como um usuario pode pertencer a mais de uma empresa, este modulo trata
da troca de contexto (qual empresa esta ativa na sessao).
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_login import login_required, current_user
from E_Ponto.models.business import Business
from E_Ponto.models.role_user import RoleUser

bp_main = Blueprint("main", __name__)


@bp_main.route('/')
@bp_main.route('/index')
@login_required
def index():
    """Pagina inicial: empresas do usuario e empresa ativa."""
    empresas = (Business.query
                .join(RoleUser, RoleUser.business_id == Business.id)
                .filter(RoleUser.user_id == current_user.id, Business.is_active == True)
                .all())

    empresa_id = session.get('empresa_id')
    empresa = Business.query.get(empresa_id) if empresa_id else None

    # Sem empresa selecionada, escolhe a primeira automaticamente
    if not empresa and empresas:
        empresa = empresas[0]
        session['empresa_id'] = empresa.id

    user_roles = [r.name for r in current_user.roles] if current_user.is_authenticated else []
    return render_template('main/index.html', empresa=empresa, empresas=empresas, user_roles=user_roles)


@bp_main.route('/empresa/<int:empresa_id>/selecionar')
@login_required
def selecionar_empresa(empresa_id):
    """Troca a empresa ativa na sessao."""
    # Confirma o vinculo do usuario com a empresa (protecao contra IDOR)
    assoc = RoleUser.query.filter_by(user_id=current_user.id, business_id=empresa_id).first()
    if not assoc:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    session['empresa_id'] = empresa_id
    flash('Empresa selecionada com sucesso.', 'success')
    return redirect(url_for('main.index'))
