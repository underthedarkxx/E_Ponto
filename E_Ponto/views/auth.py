# =====================================================================
# views/auth.py — Autenticação (login, 2FA, logout)
# ---------------------------------------------------------------------
# Trata todo o fluxo de login: verificação de senha (bcrypt), opcional
# segundo fator TOTP (Authenticator) e logout. Todas as URLs aqui
# começam com /auth/.
# =====================================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import pyotp        # gera e verifica códigos TOTP (RFC 6238)
import qrcode       # gera o QR Code que é escaneado pelo app autenticador
import io
import base64
from E_Ponto.models.user import User
from E_Ponto.forms.auth import LoginForm, VerifyTotpForm, SetupTotpForm

# Blueprint com prefixo /auth (todas as URLs ficam /auth/<rota>).
bp_auth = Blueprint('auth', __name__, url_prefix='/auth')
# Bcrypt é inicializado em views/__init__.py via bcrypt.init_app(app).
bcrypt = Bcrypt()


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """Tela de login. GET mostra o form, POST processa as credenciais."""
    # Se já está autenticado, não tem por que mostrar a tela de login.
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    # validate_on_submit retorna True apenas em POST + dados válidos.
    if form.validate_on_submit():
        # Email é case-insensitive — sempre comparamos em lowercase.
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # Confere se o usuário existe, tem senha cadastrada e se o hash
        # bate com a senha digitada (bcrypt.check_password_hash faz a
        # comparação em tempo constante para evitar timing attacks).
        if user and user.password and bcrypt.check_password_hash(user.password, form.password.data):
            # Conta desativada não pode entrar.
            if not user.is_active:
                flash('Conta desativada. Contate o administrador.', 'danger')
                return redirect(url_for('auth.login'))

            # Se 2FA está ligado, NÃO loga ainda — guarda o user_id na
            # sessão e manda para a tela de verificação do código.
            if user.two_factor_enabled:
                session['_2fa_user_id'] = user.id
                session['_2fa_remember'] = form.remember.data
                return redirect(url_for('auth.verify_2fa'))

            # Sem 2FA: efetua login normalmente.
            login_user(user, remember=form.remember.data)
            # Suporte ao parâmetro ?next= (quando o usuário tentou
            # acessar uma página protegida antes de logar).
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        # Credencial inválida — mensagem genérica para não revelar se
        # foi o email ou a senha que estava errado.
        flash('E-mail ou senha invalidos.', 'danger')

    return render_template('auth/login.html', form=form)


@bp_auth.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Segunda etapa do login: confere o código TOTP do autenticador."""
    # Sem user_id na sessão, ninguém deveria estar nesta rota.
    user_id = session.get('_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    form = VerifyTotpForm()
    if form.validate_on_submit():
        # Recria o objeto TOTP a partir do segredo salvo no usuário.
        totp = pyotp.TOTP(user.totp_secret)
        # `verify` aceita códigos da janela atual (e da imediatamente
        # anterior, por padrão), tolerando pequenos atrasos de relógio.
        if totp.verify(form.code.data):
            # Loga e limpa o estado temporário da sessão.
            login_user(user, remember=session.pop('_2fa_remember', False))
            session.pop('_2fa_user_id', None)
            return redirect(url_for('main.index'))
        flash('Codigo invalido.', 'danger')
    return render_template('auth/verify_2fa.html', form=form)


@bp_auth.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Configura 2FA: gera segredo, mostra QR e confirma o primeiro código."""
    form = SetupTotpForm()

    # Se for a primeira vez, gera um segredo Base32 aleatório.
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        from E_Ponto.ext.db import db
        db.session.commit()

    # `provisioning_uri` retorna a string padrão (otpauth://...) que
    # o app Authenticator entende.
    totp = pyotp.TOTP(current_user.totp_secret)
    uri = totp.provisioning_uri(current_user.email, issuer_name="E-Ponto")

    # Gera a imagem QR em memória e converte para base64 — assim a
    # imagem pode ser embutida direto no HTML, sem rota de download.
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    if form.validate_on_submit():
        # Confere o primeiro código antes de ativar definitivamente.
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
    """Encerra a sessão do usuário."""
    logout_user()       # Remove o user_id do cookie de sessão.
    session.clear()     # Limpa qualquer outro dado guardado (empresa_id, etc.).
    flash('Voce saiu da sessao.', 'info')

    # IMPORTANTE: logout_user() nao apaga o cookie "remember-me" sozinho
    # quando o usuario logou com "lembrar de mim". Sem apagar esse cookie,
    # o Flask-Login reautentica o usuario na proxima requisicao e ele
    # volta pra home automaticamente (parecendo que o logout nao funcionou).
    response = make_response(redirect(url_for('auth.login')))
    remember_cookie = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    response.delete_cookie(remember_cookie)
    return response
