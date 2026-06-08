"""Painel do RH.

Dashboard com KPIs, listagem/filtros de registros, analise de
retificacoes, banco de horas e download dos arquivos AFD/AEJ exigidos
pela Portaria 671/2021.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, date
from io import BytesIO
import calendar

from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.registro import Registro, TipoRegistro
from E_Ponto.models.retificacao import Retificacao, StatusRetificacao
from E_Ponto.models.user import User
from E_Ponto.models.role_user import RoleUser
from E_Ponto.models.audit_log import AuditLog
from E_Ponto.utils.decorators import role_required
from E_Ponto.utils.afd import gerar_afd
from E_Ponto.utils.aej import gerar_aej
from E_Ponto.utils.audit import log_action
from E_Ponto.utils.mail import send_notification
from E_Ponto.utils.banco_horas import (
    calcular_saldo_mes, format_min, get_jornada_funcionario)
from E_Ponto.utils.excel import gerar_banco_horas_xlsx, gerar_frequencia_xlsx
from E_Ponto.utils.nsr import get_next_nsr
from E_Ponto.utils.hashing import calcular_hash
from E_Ponto.forms.rh import AprovarRetificacaoForm

bp_rh = Blueprint('rh', __name__, url_prefix='/rh')


def _empresa():
    """Empresa ativa na sessao."""
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
    pendentes = Retificacao.query.filter_by(
        empresa_id=empresa.id, status=StatusRetificacao.PENDENTE
    ).count()
    total_hoje = (Registro.query
                  .filter_by(empresa_id=empresa.id)
                  .filter(db.func.date(Registro.timestamp_utc) == date.today())
                  .count())
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
    """Lista todos os registros com filtros opcionais (usuario e data)."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    data_str = request.args.get('data')

    q = Registro.query.filter_by(empresa_id=empresa.id)
    if user_id:
        q = q.filter_by(user_id=user_id)
    if data_str:
        try:
            d = date.fromisoformat(data_str)
            q = q.filter(db.func.date(Registro.timestamp_utc) == d)
        except ValueError:
            # Data mal formatada: ignora o filtro
            pass

    registros_pag = q.order_by(Registro.timestamp_utc.desc()).paginate(page=page, per_page=50)

    # Funcionarios para o <select> de filtro
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
    """Lista retificacoes pendentes e o historico das ultimas 50."""
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
    """Tela onde o RH aprova ou rejeita uma retificacao."""
    empresa = _empresa()
    ret = Retificacao.query.get_or_404(ret_id)

    # Protecao contra acesso a retificacao de outra empresa
    if ret.empresa_id != empresa.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('rh.retificacoes'))

    form = AprovarRetificacaoForm()
    if form.validate_on_submit():
        ret.aprovador_id = current_user.id
        ret.observacao_aprovador = form.observacao.data
        ret.aprovado_at = datetime.now(timezone.utc)

        # Captura o status antes da mudanca (para o audit log)
        status_antes = ret.status.value

        novo_registro = None
        if form.acao.data == 'aprovar':
            ret.status = StatusRetificacao.APROVADA
            acao_audit = 'APROVAR_RETIFICACAO'
            flash('Retificação aprovada.', 'success')

            # Materializa a correcao como um novo Registro ALTERACAO no
            # hash chain; o original nunca e apagado (auditoria)
            if ret.novo_timestamp:
                func_user = ret.registro.user
                # O funcionario informou hora local; converte para UTC
                ts_utc = ret.novo_timestamp.astimezone(timezone.utc)
                ultimo = (Registro.query
                          .filter_by(empresa_id=empresa.id)
                          .order_by(Registro.nsr.desc())
                          .first())
                hash_anterior = ultimo.hash_registro if ultimo else None
                nsr = get_next_nsr(empresa.id)
                hash_val = calcular_hash(
                    nsr, empresa.cnpj,
                    func_user.pis_nis or func_user.cpf or '',
                    ts_utc.isoformat(), TipoRegistro.ALTERACAO.value, hash_anterior
                )
                novo_registro = Registro(
                    nsr=nsr,
                    empresa_id=empresa.id,
                    user_id=func_user.id,
                    tipo=TipoRegistro.ALTERACAO,
                    timestamp_utc=ts_utc,
                    justificativa=ret.motivo,
                    solicitante_id=ret.solicitante_id,
                    aprovador_id=current_user.id,
                    hash_registro=hash_val,
                    hash_anterior=hash_anterior,
                )
                db.session.add(novo_registro)
        else:
            ret.status = StatusRetificacao.REJEITADA
            acao_audit = 'REJEITAR_RETIFICACAO'
            flash('Retificação rejeitada.', 'warning')

        log_action(
            acao_audit, 'retificacoes', ret.id,
            dados_antes={'status': status_antes},
            dados_depois={
                'status': ret.status.value,
                'observacao': form.observacao.data,
                'aprovador_id': current_user.id,
                'novo_timestamp': ret.novo_timestamp.isoformat() if ret.novo_timestamp else None,
            },
        )
        db.session.commit()

        # Notifica o solicitante; falha de envio nao bloqueia o fluxo
        try:
            solicitante = User.query.get(ret.solicitante_id)
            if solicitante and solicitante.email:
                send_notification(
                    to=solicitante.email,
                    subject=f'[E-Ponto] Retificacao {ret.status.value}',
                    template='retificacao_decidida',
                    solicitante=solicitante,
                    aprovador=current_user,
                    empresa=empresa,
                    retificacao=ret,
                    aprovada=(ret.status == StatusRetificacao.APROVADA),
                )
        except Exception as e:
            current_app.logger.warning(f'Falha ao enviar email de retificacao: {e}')

        return redirect(url_for('rh.retificacoes'))
    return render_template('rh/decidir_retificacao.html',
                           empresa=empresa, ret=ret, form=form)


@bp_rh.route('/auditoria')
@login_required
@role_required('rh', 'admin', 'super_admin')
def auditoria():
    """Lista o audit log da empresa com filtros (acao e usuario)."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    acao_filtro = request.args.get('acao')
    user_id_filtro = request.args.get('user_id', type=int)

    q = AuditLog.query.filter_by(empresa_id=empresa.id)
    if acao_filtro:
        q = q.filter_by(acao=acao_filtro)
    if user_id_filtro:
        q = q.filter_by(user_id=user_id_filtro)

    logs = q.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)

    # Acoes distintas para o filtro do template
    acoes_distintas = [
        a[0] for a in db.session.query(AuditLog.acao)
        .filter_by(empresa_id=empresa.id)
        .distinct().order_by(AuditLog.acao).all()
    ]

    funcionarios = (User.query
                    .join(RoleUser, RoleUser.user_id == User.id)
                    .filter(RoleUser.business_id == empresa.id)
                    .order_by(User.name)
                    .all())

    return render_template('rh/auditoria.html',
                           empresa=empresa,
                           logs=logs,
                           acoes=acoes_distintas,
                           funcionarios=funcionarios,
                           acao_filtro=acao_filtro,
                           user_id_filtro=user_id_filtro)


@bp_rh.route('/banco-horas')
@login_required
@role_required('rh', 'admin', 'super_admin')
def banco_horas():
    """Banco de horas: saldo mensal por funcionario."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    hoje = date.today()
    user_id = request.args.get('user_id', type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    mes = request.args.get('mes', hoje.month, type=int)

    funcionarios = (User.query
                    .join(RoleUser, RoleUser.user_id == User.id)
                    .filter(RoleUser.business_id == empresa.id)
                    .order_by(User.name)
                    .all())

    resultado = None
    funcionario_sel = None
    if user_id:
        funcionario_sel = User.query.get(user_id)
        jornada = get_jornada_funcionario(user_id, empresa.id)
        resultado = calcular_saldo_mes(user_id, empresa.id, ano, mes, jornada)

    return render_template('rh/banco_horas.html',
                           empresa=empresa,
                           funcionarios=funcionarios,
                           funcionario_sel=funcionario_sel,
                           resultado=resultado,
                           ano=ano,
                           mes=mes,
                           format_min=format_min)


@bp_rh.route('/banco-horas/excel')
@login_required
@role_required('rh', 'admin', 'super_admin')
def banco_horas_excel():
    """Exporta o banco de horas de um funcionario (mes) em Excel."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    hoje = date.today()
    user_id = request.args.get('user_id', type=int)
    ano = request.args.get('ano', hoje.year, type=int)
    mes = request.args.get('mes', hoje.month, type=int)
    if not user_id:
        flash('Selecione um funcionario para exportar.', 'warning')
        return redirect(url_for('rh.banco_horas'))

    funcionario = User.query.get_or_404(user_id)
    jornada = get_jornada_funcionario(user_id, empresa.id)
    resultado = calcular_saldo_mes(user_id, empresa.id, ano, mes, jornada)
    xlsx = gerar_banco_horas_xlsx(empresa, funcionario, resultado)

    return send_file(
        BytesIO(xlsx),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'banco_horas_{funcionario.name.replace(" ", "_")}_{ano}-{mes:02d}.xlsx'
    )


@bp_rh.route('/relatorios/frequencia.xlsx')
@login_required
@role_required('rh', 'admin', 'super_admin')
def download_frequencia_excel():
    """Exporta um resumo de frequencia/horas extras da equipe no mes."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    periodo = request.args.get('periodo', date.today().strftime('%Y-%m'))
    try:
        ano, mes = map(int, periodo.split('-'))
    except (ValueError, AttributeError):
        flash('Período inválido.', 'danger')
        return redirect(url_for('rh.relatorios'))

    funcionarios = (User.query
                    .join(RoleUser, RoleUser.user_id == User.id)
                    .filter(RoleUser.business_id == empresa.id)
                    .order_by(User.name)
                    .all())
    linhas = []
    for user in funcionarios:
        jornada = get_jornada_funcionario(user.id, empresa.id)
        resultado = calcular_saldo_mes(user.id, empresa.id, ano, mes, jornada)
        linhas.append((user, resultado))

    xlsx = gerar_frequencia_xlsx(empresa, linhas, ano, mes)
    return send_file(
        BytesIO(xlsx),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'frequencia_{empresa.cnpj}_{periodo}.xlsx'
    )


@bp_rh.route('/relatorios')
@login_required
@role_required('rh', 'admin', 'super_admin')
def relatorios():
    """Tela com os botoes de download dos relatorios (AFD / AEJ)."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    return render_template('rh/relatorios.html', empresa=empresa,
                           hoje=date.today().isoformat(),
                           primeiro_dia_mes=date.today().replace(day=1).isoformat(),
                           mes_atual=date.today().strftime('%Y-%m'))


@bp_rh.route('/relatorios/afd')
@login_required
@role_required('rh', 'admin', 'super_admin')
def download_afd():
    """Gera e baixa o AFD (Arquivo Fonte de Dados) no periodo pedido."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    data_inicio_str = request.args.get('inicio', date.today().replace(day=1).isoformat())
    data_fim_str = request.args.get('fim', date.today().isoformat())
    try:
        data_inicio = date.fromisoformat(data_inicio_str)
        data_fim = date.fromisoformat(data_fim_str)
    except ValueError:
        flash('Datas inválidas.', 'danger')
        return redirect(url_for('rh.relatorios'))

    # Registros do periodo ordenados por NSR (sequencial)
    registros = (Registro.query
                 .filter_by(empresa_id=empresa.id)
                 .filter(db.func.date(Registro.timestamp_utc) >= data_inicio)
                 .filter(db.func.date(Registro.timestamp_utc) <= data_fim)
                 .order_by(Registro.nsr)
                 .all())

    conteudo = gerar_afd(empresa, registros, data_inicio, data_fim)

    # AFD e texto ASCII
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
    """Gera e baixa o AEJ (Arquivo Eletronico de Jornada) do mes."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    # Periodo no formato "YYYY-MM"
    periodo = request.args.get('periodo', date.today().strftime('%Y-%m'))
    try:
        ano, mes = map(int, periodo.split('-'))
        data_inicio = date(ano, mes, 1)
        data_fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    except (ValueError, AttributeError):
        flash('Período inválido.', 'danger')
        return redirect(url_for('rh.relatorios'))

    # AEJ agrupa registros por funcionario
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
        # So inclui quem teve batidas no periodo
        if regs:
            funcionarios_registros.append((user, regs))

    conteudo = gerar_aej(empresa, funcionarios_registros, periodo)
    return send_file(
        BytesIO(conteudo.encode('ascii', errors='replace')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'AEJ_{empresa.cnpj}_{periodo}.txt'
    )
