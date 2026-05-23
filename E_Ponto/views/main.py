# =====================================================================
# views/main.py — Rotas principais (home / seleção de empresa)
# ---------------------------------------------------------------------
# Blueprint que cuida da tela inicial. Como um usuário pode pertencer
# a mais de uma empresa, este módulo também trata da troca de
# contexto (qual empresa está "ativa" na sessão).
# =====================================================================

from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_login import login_required, current_user
from E_Ponto.models.business import Business
from E_Ponto.models.role_user import RoleUser

# Cria o Blueprint "main". Sem url_prefix — rotas ficam na raiz (/, /index).
bp_main = Blueprint("main", __name__)


@bp_main.route('/')
@bp_main.route('/index')
@login_required  # exige que o usuário esteja autenticado
def index():
    """Página inicial: mostra as empresas do usuário e seu papel ativo."""
    # Busca todas as empresas ativas onde o usuário tem algum vínculo
    # (RoleUser). O JOIN dispara um SELECT com INNER JOIN no SQL.
    empresas = (Business.query
                .join(RoleUser, RoleUser.business_id == Business.id)
                .filter(RoleUser.user_id == current_user.id, Business.is_active == True)
                .all())

    # A sessão Flask guarda a empresa atualmente selecionada.
    empresa_id = session.get('empresa_id')
    empresa = Business.query.get(empresa_id) if empresa_id else None

    # Se ainda não há empresa selecionada mas o usuário tem alguma,
    # seleciona a primeira automaticamente.
    if not empresa and empresas:
        empresa = empresas[0]
        session['empresa_id'] = empresa.id

    # Lista de papéis do usuário (string) — usada no template para
    # mostrar/esconder menus.
    user_roles = [r.name for r in current_user.roles] if current_user.is_authenticated else []
    return render_template('main/index.html', empresa=empresa, empresas=empresas, user_roles=user_roles)


@bp_main.route('/empresa/<int:empresa_id>/selecionar')
@login_required
def selecionar_empresa(empresa_id):
    """Troca a empresa ativa na sessão."""
    # Antes de aceitar, confirma que o usuário realmente pertence
    # à empresa pedida (proteção contra IDOR — Insecure Direct Object Reference).
    assoc = RoleUser.query.filter_by(user_id=current_user.id, business_id=empresa_id).first()
    if not assoc:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    # Atualiza a sessão e volta pra home (que agora vai mostrar
    # informações da nova empresa).
    session['empresa_id'] = empresa_id
    flash('Empresa selecionada com sucesso.', 'success')
    return redirect(url_for('main.index'))
