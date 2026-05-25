# pyright: reportCallIssue=false
# =====================================================================
# views/ponto.py — Rotas para bater ponto e ver histórico
# ---------------------------------------------------------------------
# A diretiva "# pyright: reportCallIssue=false" silencia o aviso do
# Pylance para construtores de modelos SQLAlchemy (Registro(...)) —
# limitacao do Pylance ao ler Mapped[...] via Flask-SQLAlchemy.
# ---------------------------------------------------------------------
# É o "coração" funcional do sistema. Contém a lógica de:
#   - registrar uma batida com geofencing + hash em cadeia;
#   - listar o histórico paginado do funcionário;
#   - exibir e baixar o comprovante em PDF.
# =====================================================================

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session, send_file, abort)
from flask_login import login_required, current_user
from datetime import datetime, timezone
import io
from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.registro import Registro, TipoRegistro
from E_Ponto.models.local_trabalho import LocalTrabalho
from E_Ponto.utils.nsr import get_next_nsr           # gerador de NSR atômico
from E_Ponto.utils.hashing import calcular_hash      # SHA-256 dos campos
from E_Ponto.utils.audit import log_action           # helper de audit log
from E_Ponto.utils.geo import verificar_geofence     # checa lat/lon vs raio
from E_Ponto.utils.pdf import gerar_comprovante      # monta o PDF
from E_Ponto.forms.ponto import BaterPontoForm

bp_ponto = Blueprint('ponto', __name__, url_prefix='/ponto')


def _get_empresa():
    """Helper: pega a empresa ativa na sessão, ou None se nenhuma."""
    empresa_id = session.get('empresa_id')
    if not empresa_id:
        return None
    return Business.query.get(empresa_id)


@bp_ponto.route('/bater', methods=['GET', 'POST'])
@login_required
def bater():
    """Tela de bater ponto. POST cria o Registro e redireciona p/ comprovante."""
    empresa = _get_empresa()
    if not empresa:
        flash('Selecione uma empresa primeiro.', 'warning')
        return redirect(url_for('main.index'))

    # Lista de locais ativos para o <select>. Adiciona opção "Nao informado"
    # caso o funcionário esteja em campo sem local cadastrado.
    locais = LocalTrabalho.query.filter_by(empresa_id=empresa.id, ativo=True).all()
    form = BaterPontoForm()
    form.local_trabalho_id.choices = [(0, 'Nao informado')] + [(l.id, l.nome) for l in locais]

    if form.validate_on_submit():
        # Converte os HiddenField para float (vieram como string do JS).
        lat = float(form.latitude.data) if form.latitude.data else None
        lon = float(form.longitude.data) if form.longitude.data else None
        precisao = float(form.precisao.data) if form.precisao.data else None

        # 0 vira None — significa "Não informado".
        local_id = form.local_trabalho_id.data or None
        local = LocalTrabalho.query.get(local_id) if local_id else None

        # Geofencing: o ponto está dentro do raio cadastrado?
        # Se não, e o local foi informado, marca como suspeito.
        dentro, distancia = verificar_geofence(lat, lon, local)
        suspeito = not dentro and local is not None

        # Sempre grava em UTC. Conversão pra horário local fica no
        # template/relatório.
        now_utc = datetime.now(timezone.utc)

        # Pega o hash do último registro da empresa para encadear.
        # O encadeamento (hash de cada registro depende do anterior)
        # torna impossível alterar registros antigos sem refazer
        # todos os hashes seguintes — exigência REP-P.
        ultimo = (Registro.query
                  .filter_by(empresa_id=empresa.id)
                  .order_by(Registro.nsr.desc())
                  .first())
        hash_anterior = ultimo.hash_registro if ultimo else None

        # Gera próximo NSR de forma atômica (transação com lock).
        nsr = get_next_nsr(empresa.id)
        tipo = TipoRegistro(form.tipo.data)

        # Hash SHA-256 dos campos relevantes + hash anterior.
        hash_val = calcular_hash(
            nsr, empresa.cnpj,
            current_user.pis_nis or current_user.cpf or '',
            now_utc.isoformat(), tipo.value, hash_anterior
        )

        # Cria e persiste o Registro.
        reg = Registro(
            nsr=nsr,
            empresa_id=empresa.id,
            user_id=current_user.id,
            tipo=tipo,
            timestamp_utc=now_utc,
            latitude=lat,
            longitude=lon,
            precisao_metros=precisao,
            ip_address=request.remote_addr,    # IP do navegador
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

        # Feedback ao usuário via mensagens flash.
        flash(f'Ponto registrado! NSR: {nsr} | {now_utc.strftime("%H:%M:%S")} UTC', 'success')
        if suspeito:
            flash(f'Atencao: localizacao suspeita (distancia: {distancia:.0f}m do local).', 'warning')
        return redirect(url_for('ponto.comprovante', reg_id=reg.id))

    # GET: mostra a tela com batidas de hoje no lateral.
    hoje = datetime.now(timezone.utc).date()
    registros_hoje = (Registro.query
                      .filter_by(empresa_id=empresa.id, user_id=current_user.id)
                      # db.func.date() extrai só a parte da data do timestamp.
                      .filter(db.func.date(Registro.timestamp_utc) == hoje)
                      .order_by(Registro.timestamp_utc.desc())
                      .all())

    return render_template('ponto/bater.html', form=form, empresa=empresa,
                           registros_hoje=registros_hoje, locais=locais)


@bp_ponto.route('/historico')
@login_required
def historico():
    """Histórico paginado de batidas do usuário atual."""
    empresa = _get_empresa()
    if not empresa:
        return redirect(url_for('main.index'))

    # Pagina pela query string: /historico?page=2
    page = request.args.get('page', 1, type=int)
    registros = (Registro.query
                 .filter_by(empresa_id=empresa.id, user_id=current_user.id)
                 .order_by(Registro.timestamp_utc.desc())
                 # paginate retorna um objeto com .items, .pages, .has_next...
                 .paginate(page=page, per_page=30))
    return render_template('ponto/historico.html', registros=registros, empresa=empresa)


@bp_ponto.route('/comprovante/<int:reg_id>')
@login_required
def comprovante(reg_id):
    """Mostra o comprovante de um registro específico (HTML)."""
    empresa = _get_empresa()
    # get_or_404 dispara 404 se o registro não existir.
    reg = Registro.query.get_or_404(reg_id)

    # Autorização: só dono do ponto, RH, admin ou super_admin podem ver.
    user_roles = [r.name for r in current_user.roles]
    if reg.user_id != current_user.id and not any(r in user_roles for r in ['admin', 'rh', 'super_admin']):
        abort(403)
    return render_template('ponto/comprovante.html', reg=reg, empresa=empresa)


@bp_ponto.route('/comprovante/<int:reg_id>/pdf')
@login_required
def comprovante_pdf(reg_id):
    """Versão PDF do comprovante — download direto."""
    reg = Registro.query.get_or_404(reg_id)

    # Mesma verificação de permissão do HTML.
    user_roles = [r.name for r in current_user.roles]
    if reg.user_id != current_user.id and not any(r in user_roles for r in ['admin', 'rh', 'super_admin']):
        abort(403)

    # gerar_comprovante usa ReportLab e devolve bytes do PDF.
    pdf_bytes = gerar_comprovante(reg)
    # send_file faz o navegador baixar (as_attachment=True).
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'comprovante_nsr_{reg.nsr}.pdf'
    )
