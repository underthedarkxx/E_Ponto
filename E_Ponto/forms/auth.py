"""Formularios de autenticacao (login e 2FA)."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email(check_deliverability=False)])
    # Sem maximo de propisito: senhas acima do limite do bcrypt (72 bytes)
    # sao tratadas como credencial invalida na view, sem revelar nada
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    remember = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')


class VerifyTotpForm(FlaskForm):
    code = StringField('Codigo 2FA', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verificar')


class SetupTotpForm(FlaskForm):
    code = StringField('Codigo de verificacao', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Ativar 2FA')
