# =====================================================================
# views/funcionario.py — Painel do funcionário
# ---------------------------------------------------------------------
# Rotas voltadas ao funcionário "comum":
#   - Dashboard com batidas do dia e histórico de retificações próprias;
#   - Solicitar retificação de um ponto específico.
#
# Não há @role_required — qualquer usuário logado pode acessar.
# A verificação fina (registro pertence a mim?) é feita dentro
# de cada rota.
# =====================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import date

from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.registro import Registro
from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
from E_Ponto.forms.rh import RetificacaoForm

bp_funcionario = Blueprint('funcionario', __name__, url_prefix='/funcionario')


def _empresa():
    """Empresa ativa na sessão (mesmo padrão das outras views)."""
    empresa_id = session.get('empresa_id')
    return Business.query.get(empresa_id) if empresa_id else None


@bp_funcionario.route('/')
@login_required
def dashboard():
    """Dashboard com batidas de hoje e últimas 10 retificações do próprio usuário."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    hoje = date.today()
    # Batidas do dia, em ordem cronológica.
    registros_hoje = (Registro.query
                      .filter_by(empresa_id=empresa.id, user_id=current_user.id)
                      .filter(db.func.date(Registro.timestamp_utc) == hoje)
                      .order_by(Registro.timestamp_utc)
                      .all())
    # Status das próprias retificações (pendentes, aprovadas, rejeitadas).
    minhas_retificacoes = (Retificacao.query
                           .filter_by(empresa_id=empresa.id, solicitante_id=current_user.id)
                           .order_by(Retificacao.created_at.desc())
                           .limit(10).all())
    return render_template('funcionario/dashboard.html', empresa=empresa,
                           registros_hoje=registros_hoje,
                           minhas_retificacoes=minhas_retificacoes)


@bp_funcionario.route('/retificar/<int:reg_id>', methods=['GET', 'POST'])
@login_required
def solicitar_retificacao(reg_id):
    """Funcionário abre um pedido de correção para um registro seu."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    reg = Registro.query.get_or_404(reg_id)

    # Proteção: só o dono do registro pode pedir retificação, e dentro
    # da empresa atual.
    if reg.user_id != current_user.id or reg.empresa_id != empresa.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('funcionario.dashboard'))

    form = RetificacaoForm()
    if form.validate_on_submit():
        # Cria a retificação em estado PENDENTE. O RH vai analisar depois.
        ret = Retificacao(
            registro_id=reg.id,
            empresa_id=empresa.id,
            solicitante_id=current_user.id,
            novo_timestamp=form.novo_timestamp.data,
            motivo=form.motivo.data,
            status=StatusRetificacao.PENDENTE,
        )
        db.session.add(ret)
        db.session.commit()
        flash('Solicitação enviada para análise do RH.', 'success')
        return redirect(url_for('funcionario.dashboard'))
    return render_template('funcionario/solicitar_retificacao.html',
                           form=form, reg=reg, empresa=empresa)
