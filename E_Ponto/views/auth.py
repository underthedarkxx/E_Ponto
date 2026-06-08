"""Autenticacao: login, 2FA (TOTP) e logout. URLs sob /auth/."""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import pyotp
import qrcode
import io
import base64
from urllib.parse import urlparse
from E_Ponto.models.user import User
from E_Ponto.forms.auth import LoginForm, VerifyTotpForm, SetupTotpForm

bp_auth = Blueprint('auth', __name__, url_prefix='/auth')
# Inicializado em views/__init__.py via bcrypt.init_app(app)
bcrypt = Bcrypt()


def _destino_seguro(destino):
    """Valida o parametro ?next= contra open redirect (CWE-601).

    Aceita apenas caminhos locais; recusa URLs absolutas e
    protocol-relative. Retorna None se o destino for inseguro.
    """
    if not destino:
        return None
    if destino.startswith('//') or '\\' in destino:
        return None
    parsed = urlparse(destino)
    if parsed.scheme or parsed.netloc:
        return None
    if not destino.startswith('/'):
        return None
    return destino


def _senha_confere(pw_hash, senha):
    """Compara senha x hash sem lancar excecao.

    O bcrypt aceita no maximo 72 bytes e lanca ValueError acima disso;
    tratamos qualquer entrada invalida/longa como "nao confere" para
    evitar um 500 na tela de login.
    """
    if not pw_hash or not senha:
        return False
    try:
        return bcrypt.check_password_hash(pw_hash, senha)
    except ValueError:
        return False


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Tela de login: GET mostra o form, POST processa as credenciais."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Email e case-insensitive
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and _senha_confere(user.password, form.password.data):
            if not user.is_active:
                flash('Conta desativada. Contate o administrador.', 'danger')
                return redirect(url_for('auth.login'))

            # Com 2FA, guarda o user_id e segue para a verificacao do codigo
            if user.two_factor_enabled:
                session['_2fa_user_id'] = user.id
                session['_2fa_remember'] = form.remember.data
                return redirect(url_for('auth.verify_2fa'))

            login_user(user, remember=form.remember.data)
            # Suporte ao ?next= (pagina protegida acessada antes do login)
            next_page = _destino_seguro(request.args.get('next'))
            return redirect(next_page or url_for('main.index'))

        # Mensagem generica para nao revelar se errou email ou senha
        flash('E-mail ou senha invalidos.', 'danger')

    return render_template('auth/login.html', form=form)


@bp_auth.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Segunda etapa do login: confere o codigo TOTP do autenticador."""
    user_id = session.get('_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    form = VerifyTotpForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.totp_secret)
        # verify tolera a janela anterior, cobrindo pequenos desvios de relogio
        if totp.verify(form.code.data):
            login_user(user, remember=session.pop('_2fa_remember', False))
            session.pop('_2fa_user_id', None)
            return redirect(url_for('main.index'))
        flash('Codigo invalido.', 'danger')
    return render_template('auth/verify_2fa.html', form=form)


@bp_auth.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Configura 2FA: gera o segredo, mostra o QR e confirma o primeiro codigo."""
    form = SetupTotpForm()

    # Primeira vez: gera um segredo Base32 aleatorio
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        from E_Ponto.ext.db import db
        db.session.commit()

    totp = pyotp.TOTP(current_user.totp_secret)
    uri = totp.provisioning_uri(current_user.email, issuer_name="E-Ponto")

    # Gera o QR em memoria e embute como base64 no HTML
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    if form.validate_on_submit():
        # Confere o primeiro codigo antes de ativar
        if totp.verify(form.code.data):
            current_user.two_factor_enabled = True
            from E_Ponto.ext.db import db
            db.session.commit()
            flash('2FA ativado com sucesso!', 'success')
            return redirect(url_for('main.index'))
        flash('Codigo invalido.', 'danger')

    return render_template('auth/setup_2fa.html', form=form, qr_b64=qr_b64)


@bp_auth.route('/logout')
@login_required
def logout():
    """Encerra a sessao do usuario."""
    logout_user()
    session.clear()
    flash('Voce saiu da sessao.', 'info')

    # logout_user() nao apaga o cookie "remember-me"; sem isso o
    # Flask-Login reautentica o usuario na proxima requisicao
    response = make_response(redirect(url_for('auth.login')))
    remember_cookie = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    response.delete_cookie(remember_cookie)
    return response
