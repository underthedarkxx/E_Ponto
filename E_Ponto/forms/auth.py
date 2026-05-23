# =====================================================================
# forms/auth.py — Formulários de autenticação
# ---------------------------------------------------------------------
# Formulários WTForms são classes que descrevem campos HTML e suas
# regras de validação. O Flask-WTF herda de Form e adiciona proteção
# CSRF automática. As mensagens de erro e a renderização vêm dos
# templates Jinja2 em templates/auth/.
# =====================================================================

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length


# --- Tela de login ----------------------------------------------------
class LoginForm(FlaskForm):
    # DataRequired: campo não pode ficar vazio.
    # Email: precisa ter formato user@dominio.
    # check_deliverability=False evita consulta DNS (acelera testes).
    email = StringField('E-mail', validators=[DataRequired(), Email(check_deliverability=False)])
    # PasswordField renderiza <input type="password"> (oculta texto).
    # Length(min=6): senha precisa ter pelo menos 6 caracteres.
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    # Checkbox "lembrar-me" — quando marcado, Flask-Login estende a
    # duração do cookie de sessão.
    remember = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')


# --- Tela "verificar código 2FA" depois de logar ---------------------
class VerifyTotpForm(FlaskForm):
    # Códigos TOTP têm exatamente 6 dígitos.
    code = StringField('Codigo 2FA', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verificar')


# --- Tela "ativar 2FA": usuário escaneia QR e confirma o código ------
class SetupTotpForm(FlaskForm):
    code = StringField('Codigo de verificacao', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Ativar 2FA')
