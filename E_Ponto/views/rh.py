# =====================================================================
# views/rh.py — Painel do RH
# ---------------------------------------------------------------------
# Rotas para o RH:
#   - Dashboard com KPIs (registros do dia, retificações pendentes...);
#   - Listagem e filtros de registros de todos os funcionários;
#   - Análise/aprovação de retificações;
#   - Download dos arquivos AFD (diário) e AEJ (mensal) exigidos pela
#     Portaria 671/2021.
# =====================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file
from flask_login import login_required, current_user
from datetime import datetime, timezone, date
from io import BytesIO
import calendar  # usado para descobrir o último dia do mês

from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.registro import Registro
from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
from E_Ponto.models.user import User
from E_Ponto.models.role_user import RoleUser
from E_Ponto.utils.decorators import role_required
from E_Ponto.utils.afd import gerar_afd   # gera arquivo AFD (formato texto)
from E_Ponto.utils.aej import gerar_aej   # gera arquivo AEJ (formato texto)
from E_Ponto.forms.rh import AprovarRetificacaoForm

bp_rh = Blueprint('rh', __name__, url_prefix='/rh')


def _empresa():
    """Mesmo helper das outras views — empresa ativa na sessão."""
    empresa_id = session.get('empresa_id')
    return Business.query.get(empresa_id) if empresa_id else None


@bp_rh.route('/')
@login_required
@role_required('rh', 'admin', 'super_admin')
def dashboard():
    """Dashboard do RH: principais indicadores."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    # Retificações esperando decisão.
    pendentes = Retificacao.query.filter_by(
        empresa_id=empresa.id, status=StatusRetificacao.PENDENTE
    ).count()
    # Total de batidas hoje.
    total_hoje = (Registro.query
                  .filter_by(empresa_id=empresa.id)
                  .filter(db.func.date(Registro.timestamp_utc) == date.today())
                  .count())
    # Registros que foram marcados como suspeitos por geolocalização.
    suspeitos = (Registro.query
                 .filter_by(empresa_id=empresa.id, suspeito_geo=True)
                 .count())
    return render_template('rh/dashboard.html', empresa=empresa,
                           pendentes=pendentes, total_hoje=total_hoje,
                           suspeitos=suspeitos)


@bp_rh.route('/registros')
@login_required
@role_required('rh', 'admin', 'super_admin')
def registros():
    """Lista todos os registros com filtros opcionais (usuário e data)."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    # Lê parâmetros da query string (?page=&user_id=&data=).
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    data_str = request.args.get('data')

    # Monta a query incrementalmente, aplicando filtros se vierem.
    q = Registro.query.filter_by(empresa_id=empresa.id)
    if user_id:
        q = q.filter_by(user_id=user_id)
    if data_str:
        try:
            d = date.fromisoformat(data_str)
            q = q.filter(db.func.date(Registro.timestamp_utc) == d)
        except ValueError:
            # Data mal formatada: ignora o filtro silenciosamente.
            pass

    # Pagina o resultado.
    registros_pag = q.order_by(Registro.timestamp_utc.desc()).paginate(page=page, per_page=50)

    # Lista de funcionários — popula o <select> de filtro no template.
    funcionarios = (User.query
                    .join(RoleUser, RoleUser.user_id == User.id)
                    .filter(RoleUser.business_id == empresa.id)
                    .order_by(User.name)
                    .all())
    return render_template('rh/registros.html', empresa=empresa,
                           registros=registros_pag,
                           funcionarios=funcionarios,
                           user_id_filtro=user_id,
                           data_filtro=data_str)


@bp_rh.route('/retificacoes')
@login_required
@role_required('rh', 'admin', 'super_admin')
def retificacoes():
    """Lista retificações pendentes (em destaque) e histórico das últimas 50."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    pendentes = (Retificacao.query
                 .filter_by(empresa_id=empresa.id, status=StatusRetificacao.PENDENTE)
                 .order_by(Retificacao.created_at.desc())
                 .all())
    historico = (Retificacao.query
                 .filter_by(empresa_id=empresa.id)
                 .filter(Retificacao.status != StatusRetificacao.PENDENTE)
                 .order_by(Retificacao.aprovado_at.desc())
                 .limit(50).all())
    return render_template('rh/retificacoes.html', empresa=empresa,
                           pendentes=pendentes, historico=historico)


@bp_rh.route('/retificacoes/<int:ret_id>/decidir', methods=['GET', 'POST'])
@login_required
@role_required('rh', 'admin', 'super_admin')
def decidir_retificacao(ret_id):
    """Tela onde o RH aprova ou rejeita uma retificação."""
    empresa = _empresa()
    ret = Retificacao.query.get_or_404(ret_id)

    # Proteção contra acesso a retificação de outra empresa.
    if ret.empresa_id != empresa.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.retificacoes'))

    form = AprovarRetificacaoForm()
    if form.validate_on_submit():
        ret.aprovador_id = current_user.id
        ret.observacao_aprovador = form.observacao.data
        ret.aprovado_at = datetime.now(timezone.utc)

        # A escolha do <select> determina o novo status.
        if form.acao.data == 'aprovar':
            ret.status = StatusRetificacao.APROVADA
            flash('Retificação aprovada.', 'success')
        else:
            ret.status = StatusRetificacao.REJEITADA
            flash('Retificação rejeitada.', 'warning')
        db.session.commit()
        return redirect(url_for('rh.retificacoes'))
    return render_template('rh/decidir_retificacao.html',
                           empresa=empresa, ret=ret, form=form)


@bp_rh.route('/relatorios')
@login_required
@role_required('rh', 'admin', 'super_admin')
def relatorios():
    """Tela com os botões de download dos relatórios (AFD / AEJ)."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    # Passa datas padrão para os inputs do formulário.
    return render_template('rh/relatorios.html', empresa=empresa,
                           hoje=date.today().isoformat(),
                           primeiro_dia_mes=date.today().replace(day=1).isoformat(),
                           mes_atual=date.today().strftime('%Y-%m'))


@bp_rh.route('/relatorios/afd')
@login_required
@role_required('rh', 'admin', 'super_admin')
def download_afd():
    """Gera e baixa o AFD (Arquivo Fonte de Dados) no período pedido."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    # Datas vêm como YYYY-MM-DD na query string.
    data_inicio_str = request.args.get('inicio', date.today().replace(day=1).isoformat())
    data_fim_str = request.args.get('fim', date.today().isoformat())
    try:
        data_inicio = date.fromisoformat(data_inicio_str)
        data_fim = date.fromisoformat(data_fim_str)
    except ValueError:
        flash('Datas inválidas.', 'danger')
        return redirect(url_for('rh.relatorios'))

    # Busca todos os registros do período, ORDENADOS POR NSR (sequencial).
    registros = (Registro.query
                 .filter_by(empresa_id=empresa.id)
                 .filter(db.func.date(Registro.timestamp_utc) >= data_inicio)
                 .filter(db.func.date(Registro.timestamp_utc) <= data_fim)
                 .order_by(Registro.nsr)
                 .all())

    # gerar_afd retorna o texto formatado conforme layout AFD.
    conteudo = gerar_afd(empresa, registros, data_inicio, data_fim)

    # Envia como arquivo de texto ASCII (exigência do layout AFD).
    return send_file(
        BytesIO(conteudo.encode('ascii', errors='replace')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'AFD_{empresa.cnpj}_{data_inicio_str}_{data_fim_str}.txt'
    )


@bp_rh.route('/relatorios/aej')
@login_required
@role_required('rh', 'admin', 'super_admin')
def download_aej():
    """Gera e baixa o AEJ (Arquivo Eletrônico de Jornada) do mês."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    # Período no formato "YYYY-MM" (ex.: "2025-11").
    periodo = request.args.get('periodo', date.today().strftime('%Y-%m'))
    try:
        ano, mes = map(int, periodo.split('-'))
        data_inicio = date(ano, mes, 1)
        # monthrange(ano, mes) -> (dia_semana_do_dia_1, ultimo_dia).
        data_fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    except (ValueError, AttributeError):
        flash('Período inválido.', 'danger')
        return redirect(url_for('rh.relatorios'))

    # Para o AEJ precisamos agrupar registros POR FUNCIONÁRIO.
    funcionarios = (User.query
                    .join(RoleUser, RoleUser.user_id == User.id)
                    .filter(RoleUser.business_id == empresa.id)
                    .order_by(User.name)
                    .all())
    funcionarios_registros = []
    for user in funcionarios:
        regs = (Registro.query
                .filter_by(empresa_id=empresa.id, user_id=user.id)
                .filter(db.func.date(Registro.timestamp_utc) >= data_inicio)
                .filter(db.func.date(Registro.timestamp_utc) <= data_fim)
                .order_by(Registro.timestamp_utc)
                .all())
        # Só inclui funcionários que tiveram batidas no período.
        if regs:
            funcionarios_registros.append((user, regs))

    conteudo = gerar_aej(empresa, funcionarios_registros, periodo)
    return send_file(
        BytesIO(conteudo.encode('ascii', errors='replace')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'AEJ_{empresa.cnpj}_{periodo}.txt'
    )
