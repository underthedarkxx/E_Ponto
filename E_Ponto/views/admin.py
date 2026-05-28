# pyright: reportCallIssue=false
# =====================================================================
# views/admin.py — Painel do administrador
# ---------------------------------------------------------------------
# A diretiva "# pyright: reportCallIssue=false" no topo silencia o
# aviso do Pylance para construtores de modelos SQLAlchemy (ex.:
# User(name=..., email=...)), Role(name=...), RoleUser(...)) — limitacao
# do Pylance ao ler Mapped[...] via Flask-SQLAlchemy.
# ---------------------------------------------------------------------
# Rotas para o admin gerenciar:
#   - usuários (vincular pessoas à empresa);
#   - locais de trabalho (endereços com geofence);
#   - jornadas (tipos de horário de trabalho).
#
# Todas as rotas são protegidas por @role_required('admin', 'super_admin').
# =====================================================================

from flask import (Blueprint, render_template, redirect, url_for, flash,
                   session, current_app)
from flask_login import login_required
from flask_bcrypt import generate_password_hash
from werkzeug.utils import secure_filename
import secrets  # gera senhas/temporais criptograficamente seguras
import os
from datetime import date

from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.user import User
from E_Ponto.models.role import Role
from E_Ponto.models.role_user import RoleUser
from E_Ponto.models.local_trabalho import LocalTrabalho
from E_Ponto.models.jornada import Jornada
from E_Ponto.models.escala import EscalaFuncionario
from E_Ponto.utils.decorators import role_required
from E_Ponto.utils.audit import log_action
from E_Ponto.forms.admin import UsuarioForm, LocalTrabalhoForm, JornadaForm


def _salvar_foto(file_storage) -> str | None:
    """Salva a foto enviada em static/uploads/avatars e retorna o caminho
    relativo a /static (ou None se nada foi enviado)."""
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return None
    # Nome seguro + sufixo aleatório para evitar colisões/sobrescrita.
    nome = secure_filename(file_storage.filename)
    base, ext = os.path.splitext(nome)
    nome_final = f"{base}_{secrets.token_hex(4)}{ext.lower()}"
    pasta_rel = os.path.join('uploads', 'avatars')
    pasta_abs = os.path.join(current_app.static_folder, pasta_rel)
    os.makedirs(pasta_abs, exist_ok=True)
    file_storage.save(os.path.join(pasta_abs, nome_final))
    # Caminho relativo usado em url_for('static', filename=...).
    return os.path.join(pasta_rel, nome_final).replace('\\', '/')


bp_admin = Blueprint('admin', __name__, url_prefix='/admin')


def _empresa():
    """Mesmo helper de views/ponto.py — recupera a empresa da sessão."""
    empresa_id = session.get('empresa_id')
    return Business.query.get(empresa_id) if empresa_id else None


@bp_admin.route('/')
@login_required
@role_required('admin', 'super_admin')
def dashboard():
    """Dashboard do admin: KPIs principais da empresa selecionada."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    # Contadores que aparecem nos "cards" da dashboard.
    total_users = RoleUser.query.filter_by(business_id=empresa.id).count()
    total_locais = LocalTrabalho.query.filter_by(empresa_id=empresa.id, ativo=True).count()
    total_jornadas = Jornada.query.filter_by(empresa_id=empresa.id, ativo=True).count()
    return render_template('admin/dashboard.html', empresa=empresa,
                           total_users=total_users, total_locais=total_locais,
                           total_jornadas=total_jornadas)


@bp_admin.route('/usuarios')
@login_required
@role_required('admin', 'super_admin')
def usuarios():
    """Lista todos os usuários vinculados à empresa."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    # Filtra por business_id e ordena pelo nome do usuário.
    assocs = (RoleUser.query
              .filter_by(business_id=empresa.id)
              .join(User, User.id == RoleUser.user_id)
              .order_by(User.name)
              .all())
    return render_template('admin/usuarios.html', empresa=empresa, assocs=assocs)


@bp_admin.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def novo_usuario():
    """Cria um usuário OU vincula um já existente à empresa atual."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    form = UsuarioForm()
    # Popula o <select> de jornadas com as jornadas ativas da empresa.
    # 0 = "sem jornada definida".
    jornadas = Jornada.query.filter_by(empresa_id=empresa.id, ativo=True).order_by(Jornada.nome).all()
    form.jornada_id.choices = [(0, 'Sem jornada definida')] + [(j.id, j.nome) for j in jornadas]

    if form.validate_on_submit():
        email = form.email.data.lower()
        # Foto enviada (se houver) — salva no static e guarda o caminho.
        foto_path = _salvar_foto(form.photo.data)
        # Tenta achar usuário com esse email — pode já existir em outra empresa.
        user = User.query.filter_by(email=email).first()
        senha_temp = None
        if not user:
            # Não existe: cria com senha temporária aleatória.
            # secrets.token_urlsafe é seguro para uso em produção.
            senha_temp = secrets.token_urlsafe(10)
            user = User(
                name=form.name.data,
                email=email,
                cpf=form.cpf.data or None,
                pis_nis=form.pis_nis.data or None,
                phone=form.phone.data or None,
                cargo=form.cargo.data or None,
                photo=foto_path,
                # Data de admissão: usa a do formulário ou, se vazia, hoje.
                data_admissao=form.data_admissao.data or date.today(),
                # generate_password_hash retorna bytes — .decode() vira str.
                password=generate_password_hash(senha_temp).decode(),
                is_active=form.is_active.data,
            )
            db.session.add(user)
            # flush() escreve no banco mas não commita — assim já
            # temos user.id para usar abaixo.
            db.session.flush()
        else:
            # Usuário já existe: atualiza cargo/foto/admissão se vieram.
            if form.cargo.data:
                user.cargo = form.cargo.data
            if foto_path:
                user.photo = foto_path
            if form.data_admissao.data:
                user.data_admissao = form.data_admissao.data

        # Garante que o Role existe (criação preguiçosa).
        role = Role.query.filter_by(name=form.role.data).first()
        if not role:
            role = Role(name=form.role.data)
            db.session.add(role)
            db.session.flush()

        # Evita criar duplicata: só insere a associação se ainda não existe.
        existing = RoleUser.query.filter_by(
            user_id=user.id, business_id=empresa.id, role_id=role.id
        ).first()
        if not existing:
            assoc = RoleUser(user_id=user.id, business_id=empresa.id, role_id=role.id)
            db.session.add(assoc)

        # Vincula a jornada via Escala (horário contratual do funcionário).
        # Fecha escalas ativas anteriores e abre uma nova vigente a partir de hoje.
        if form.jornada_id.data:
            EscalaFuncionario.query.filter_by(
                user_id=user.id, empresa_id=empresa.id, ativo=True
            ).update({'ativo': False, 'data_fim': date.today()})
            db.session.add(EscalaFuncionario(
                user_id=user.id,
                empresa_id=empresa.id,
                jornada_id=form.jornada_id.data,
                data_inicio=date.today(),
                ativo=True,
            ))

        log_action(
            'CRIAR_USUARIO', 'users', user.id,
            dados_depois={
                'name': user.name,
                'email': user.email,
                'role': form.role.data,
                'cargo': user.cargo,
                'jornada_id': form.jornada_id.data or None,
                'novo': senha_temp is not None,
            },
        )
        db.session.commit()

        # Mostra a senha temporária para o admin repassar ao usuário.
        if senha_temp:
            flash(f'Usuário {user.name} criado. Senha temporária: {senha_temp}', 'info')
        else:
            flash(f'Usuário {user.name} vinculado à empresa.', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/novo_usuario.html', form=form, empresa=empresa)


@bp_admin.route('/locais')
@login_required
@role_required('admin', 'super_admin')
def locais():
    """Lista os locais de trabalho da empresa."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    locais_list = LocalTrabalho.query.filter_by(empresa_id=empresa.id).order_by(LocalTrabalho.nome).all()
    return render_template('admin/locais.html', empresa=empresa, locais=locais_list)


@bp_admin.route('/locais/novo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def novo_local():
    """Cadastra um novo local de trabalho."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    form = LocalTrabalhoForm()
    if form.validate_on_submit():
        local = LocalTrabalho(
            empresa_id=empresa.id,
            nome=form.nome.data,
            logradouro=form.logradouro.data or None,
            numero=form.numero.data or None,
            cidade=form.cidade.data or None,
            uf=form.uf.data or None,
            cep=form.cep.data or None,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            # Se o usuário não preencheu, usa 200m de padrão.
            raio_metros=form.raio_metros.data or 200,
        )
        db.session.add(local)
        db.session.flush()
        log_action(
            'CRIAR_LOCAL', 'locais_trabalho', local.id,
            dados_depois={
                'nome': local.nome,
                'cidade': local.cidade,
                'raio_metros': local.raio_metros,
            },
        )
        db.session.commit()
        flash('Local de trabalho cadastrado.', 'success')
        return redirect(url_for('admin.locais'))
    return render_template('admin/novo_local.html', form=form, empresa=empresa)


@bp_admin.route('/locais/<int:local_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def editar_local(local_id):
    """Edita um local de trabalho existente."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    # first_or_404 + filtro por empresa: garante que o admin só edita
    # locais da PRÓPRIA empresa (evita acesso a id de outra empresa).
    local = LocalTrabalho.query.filter_by(id=local_id, empresa_id=empresa.id).first_or_404()
    # obj=local pré-preenche o formulário com os valores atuais.
    form = LocalTrabalhoForm(obj=local)
    if form.validate_on_submit():
        local.nome = form.nome.data
        local.logradouro = form.logradouro.data or None
        local.numero = form.numero.data or None
        local.cidade = form.cidade.data or None
        local.uf = form.uf.data or None
        local.cep = form.cep.data or None
        local.latitude = form.latitude.data
        local.longitude = form.longitude.data
        local.raio_metros = form.raio_metros.data or 200
        log_action(
            'EDITAR_LOCAL', 'locais_trabalho', local.id,
            dados_depois={
                'nome': local.nome,
                'cidade': local.cidade,
                'raio_metros': local.raio_metros,
            },
        )
        db.session.commit()
        flash('Local de trabalho atualizado.', 'success')
        return redirect(url_for('admin.locais'))
    return render_template('admin/novo_local.html', form=form, empresa=empresa, local=local)


@bp_admin.route('/locais/<int:local_id>/toggle', methods=['POST'])
@login_required
@role_required('admin', 'super_admin')
def toggle_local(local_id):
    """Ativa/desativa um local (soft-delete): preserva o histórico de
    pontos que apontam para ele e permite reativar depois."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    local = LocalTrabalho.query.filter_by(id=local_id, empresa_id=empresa.id).first_or_404()
    local.ativo = not local.ativo
    log_action(
        'TOGGLE_LOCAL', 'locais_trabalho', local.id,
        dados_depois={'ativo': local.ativo},
    )
    db.session.commit()
    flash('Local %s.' % ('reativado' if local.ativo else 'desativado'), 'success')
    return redirect(url_for('admin.locais'))


@bp_admin.route('/jornadas')
@login_required
@role_required('admin', 'super_admin')
def jornadas():
    """Lista as jornadas cadastradas."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    jornadas_list = Jornada.query.filter_by(empresa_id=empresa.id).order_by(Jornada.nome).all()
    return render_template('admin/jornadas.html', empresa=empresa, jornadas=jornadas_list)


@bp_admin.route('/jornadas/nova', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'super_admin')
def nova_jornada():
    """Cadastra uma nova jornada de trabalho."""
    empresa = _empresa()
    if not empresa:
        return redirect(url_for('main.index'))
    form = JornadaForm()
    if form.validate_on_submit():
        j = Jornada(
            empresa_id=empresa.id,
            nome=form.nome.data,
            tipo=form.tipo.data,
            carga_horaria_semanal=form.carga_horaria_semanal.data,
            horario_entrada=form.horario_entrada.data,
            horario_saida=form.horario_saida.data,
            intervalo_minutos=form.intervalo_minutos.data or 60,
            tolerancia_minutos=form.tolerancia_minutos.data or 5,
        )
        db.session.add(j)
        db.session.flush()
        log_action(
            'CRIAR_JORNADA', 'jornadas', j.id,
            dados_depois={
                'nome': j.nome,
                'tipo': j.tipo,
                'carga_horaria_semanal': j.carga_horaria_semanal,
            },
        )
        db.session.commit()
        flash('Jornada cadastrada.', 'success')
        return redirect(url_for('admin.jornadas'))
    return render_template('admin/nova_jornada.html', form=form, empresa=empresa)
