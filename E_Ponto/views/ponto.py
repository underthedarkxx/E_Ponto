# pyright: reportCallIssue=false
"""Rotas para bater ponto e ver historico.

Nucleo funcional do sistema: registra batidas com geofencing e hash em
cadeia, lista o historico paginado e gera o comprovante em PDF.
"""

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session, send_file, abort)
from flask_login import login_required, current_user
from datetime import datetime, timezone
import io
from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.registro import Registro, TipoRegistro
from E_Ponto.models.local_trabalho import LocalTrabalho
from E_Ponto.utils.nsr import get_next_nsr
from E_Ponto.utils.hashing import calcular_hash
from E_Ponto.utils.audit import log_action
from E_Ponto.utils.geo import verificar_geofence
from E_Ponto.utils.pdf import gerar_comprovante
from E_Ponto.utils.tz import to_local
from E_Ponto.forms.ponto import BaterPontoForm

bp_ponto = Blueprint('ponto', __name__, url_prefix='/ponto')


def _get_empresa():
    """Empresa ativa na sessao, ou None."""
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return None
    return Business.query.get(empresa_id)


@bp_ponto.route('/bater', methods=['GET', 'POST'])
@login_required
def bater():
    """Tela de bater ponto; POST cria o Registro e redireciona ao comprovante."""
    empresa = _get_empresa()
    if not empresa:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('main.index'))

    # Locais ativos para o <select> ('Nao informado' cobre trabalho em campo)
    locais = LocalTrabalho.query.filter_by(empresa_id=empresa.id, ativo=True).all()
    form = BaterPontoForm()
    form.local_trabalho_id.choices = [(0, 'Nao informado')] + [(l.id, l.nome) for l in locais]

    if form.validate_on_submit():
        # HiddenField vem como string do JS
        lat = float(form.latitude.data) if form.latitude.data else None
        lon = float(form.longitude.data) if form.longitude.data else None
        precisao = float(form.precisao.data) if form.precisao.data else None

        local_id = form.local_trabalho_id.data or None  # 0 -> None
        local = LocalTrabalho.query.get(local_id) if local_id else None

        # Geofencing: marca suspeito se fora do raio e com local informado
        dentro, distancia = verificar_geofence(lat, lon, local)
        suspeito = not dentro and local is not None

        now_utc = datetime.now(timezone.utc)

        # Encadeia com o hash do ultimo registro da empresa (exigencia REP-P)
        ultimo = (Registro.query
                  .filter_by(empresa_id=empresa.id)
                  .order_by(Registro.nsr.desc())
                  .first())
        hash_anterior = ultimo.hash_registro if ultimo else None

        # NSR atomico (transacao com lock)
        nsr = get_next_nsr(empresa.id)
        tipo = TipoRegistro(form.tipo.data)

        hash_val = calcular_hash(
            nsr, empresa.cnpj,
            current_user.pis_nis or current_user.cpf or '',
            now_utc.isoformat(), tipo.value, hash_anterior
        )

        reg = Registro(
            nsr=nsr,
            empresa_id=empresa.id,
            user_id=current_user.id,
            tipo=tipo,
            timestamp_utc=now_utc,
            latitude=lat,
            longitude=lon,
            precisao_metros=precisao,
            ip_address=request.remote_addr,
            suspeito_geo=suspeito,
            local_trabalho_id=local_id,
            justificativa=form.justificativa.data or None,
            hash_registro=hash_val,
            hash_anterior=hash_anterior,
        )
        db.session.add(reg)
        db.session.flush()  # garante reg.id antes do audit
        log_action(
            'CRIAR_REGISTRO', 'registros', reg.id,
            dados_depois={
                'nsr': nsr,
                'tipo': tipo.value,
                'timestamp_utc': now_utc.isoformat(),
                'suspeito_geo': suspeito,
                'local_trabalho_id': local_id,
            },
        )
        db.session.commit()

        hora_local = to_local(now_utc).strftime("%H:%M:%S")
        flash(f'Ponto registrado! NSR: {nsr} | {hora_local}', 'success')
        if suspeito:
            flash(f'Atencao: localizacao suspeita (distancia: {distancia:.0f}m do local).', 'warning')
        return redirect(url_for('ponto.comprovante', reg_id=reg.id))

    # GET: tela com as batidas de hoje
    hoje = datetime.now(timezone.utc).date()
    registros_hoje = (Registro.query
                      .filter_by(empresa_id=empresa.id, user_id=current_user.id)
                      .filter(db.func.date(Registro.timestamp_utc) == hoje)
                      .order_by(Registro.timestamp_utc.desc())
                      .all())

    return render_template('ponto/bater.html', form=form, empresa=empresa,
                           registros_hoje=registros_hoje, locais=locais)


@bp_ponto.route('/historico')
@login_required
def historico():
    """Historico paginado de batidas do usuario atual."""
    empresa = _get_empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    registros = (Registro.query
                 .filter_by(empresa_id=empresa.id, user_id=current_user.id)
                 .order_by(Registro.timestamp_utc.desc())
                 .paginate(page=page, per_page=30))
    return render_template('ponto/historico.html', registros=registros, empresa=empresa)


@bp_ponto.route('/comprovante/<int:reg_id>')
@login_required
def comprovante(reg_id):
    """Mostra o comprovante de um registro (HTML)."""
    empresa = _get_empresa()
    reg = Registro.query.get_or_404(reg_id)

    # Apenas dono do ponto, RH, admin ou super_admin podem ver
    user_roles = [r.name for r in current_user.roles]
    if reg.user_id != current_user.id and not any(r in user_roles for r in ['admin', 'rh', 'super_admin']):
        abort(403)
    return render_template('ponto/comprovante.html', reg=reg, empresa=empresa)


@bp_ponto.route('/comprovante/<int:reg_id>/pdf')
@login_required
def comprovante_pdf(reg_id):
    """Versao PDF do comprovante (download direto)."""
    reg = Registro.query.get_or_404(reg_id)

    user_roles = [r.name for r in current_user.roles]
    if reg.user_id != current_user.id and not any(r in user_roles for r in ['admin', 'rh', 'super_admin']):
        abort(403)

    pdf_bytes = gerar_comprovante(reg)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'comprovante_nsr_{reg.nsr}.pdf'
    )
