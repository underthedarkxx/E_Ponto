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

from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required
from flask_bcrypt import generate_password_hash
import secrets  # gera senhas/temporais criptograficamente seguras

from E_Ponto.ext.db import db
from E_Ponto.models.business import Business
from E_Ponto.models.user import User
from E_Ponto.models.role import Role
from E_Ponto.models.role_user import RoleUser
from E_Ponto.models.local_trabalho import LocalTrabalho
from E_Ponto.models.jornada import Jornada
from E_Ponto.utils.decorators import role_required
from E_Ponto.utils.audit import log_action
from E_Ponto.forms.admin import UsuarioForm, LocalTrabalhoForm, JornadaForm

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
    if form.validate_on_submit():
        email = form.email.data.lower()
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
                # generate_password_hash retorna bytes — .decode() vira str.
                password=generate_password_hash(senha_temp).decode(),
                is_active=form.is_active.data,
            )
            db.session.add(user)
            # flush() escreve no banco mas não commita — assim já
            # temos user.id para usar abaixo.
            db.session.flush()

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
        log_action(
            'CRIAR_USUARIO', 'users', user.id,
            dados_depois={
                'name': user.name,
                'email': user.email,
                'role': form.role.data,
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
