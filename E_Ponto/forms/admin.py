# =====================================================================
# forms/admin.py — Formulários da área administrativa
# ---------------------------------------------------------------------
# Usados pelo admin para cadastrar usuários, locais de trabalho e
# jornadas. Cada classe vira um <form> HTML quando renderizada no
# template (admin/novo_*.html, admin/usuarios.html, etc.).
# =====================================================================

from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, BooleanField, SubmitField,
                     DecimalField, IntegerField, TimeField)
from wtforms.validators import DataRequired, Optional, Length, Email


# Lista de UFs (estados brasileiros) usada no <select> de endereço.
# Começa com ('', '--') para representar "nenhum selecionado".
_UF_CHOICES = [('', '--')] + [(s, s) for s in [
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR',
    'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
]]


# --- Cadastro/edição de Usuário --------------------------------------
class UsuarioForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    # Optional() = não falha se vazio (mas se preenchido, valida).
    email = StringField('E-mail', validators=[DataRequired(), Email(check_deliverability=False)])
    cpf = StringField('CPF', validators=[Optional(), Length(max=15)])
    pis_nis = StringField('PIS/NIS', validators=[Optional(), Length(max=15)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    # Lista pré-definida de papéis. O valor (lado esquerdo da tupla)
    # é o que vai pro banco; o label (direita) é o que aparece no HTML.
    role = SelectField('Papel', choices=[
        ('funcionario', 'Funcionario'),
        ('rh', 'RH'),
        ('admin', 'Administrador'),
    ])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


# --- Cadastro/edição de Local de Trabalho ----------------------------
class LocalTrabalhoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    logradouro = StringField('Logradouro', validators=[Optional(), Length(max=120)])
    numero = StringField('Numero', validators=[Optional(), Length(max=10)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=60)])
    uf = SelectField('UF', choices=_UF_CHOICES, validators=[Optional()])
    cep = StringField('CEP', validators=[Optional(), Length(max=10)])
    # DecimalField(places=7) = casas decimais para guardar coordenadas
    # GPS (lat/long) com precisão de ~1 cm.
    latitude = DecimalField('Latitude', places=7, validators=[Optional()])
    longitude = DecimalField('Longitude', places=7, validators=[Optional()])
    # Raio de tolerância — padrão 200m.
    raio_metros = IntegerField('Raio (metros)', default=200)
    submit = SubmitField('Salvar')


# --- Cadastro/edição de Jornada de Trabalho --------------------------
class JornadaForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=60)])
    tipo = SelectField('Tipo', choices=[
        ('padrao', 'Padrao (8h/dia)'),
        ('12x36', '12x36'),
        ('6x1', '6x1'),
        ('flexivel', 'Flexivel'),
    ])
    carga_horaria_semanal = DecimalField('Carga Horaria Semanal (h)', places=2, default=44)
    # TimeField gera <input type="time"> (seletor de hora HTML5).
    horario_entrada = TimeField('Horario de Entrada', validators=[Optional()])
    horario_saida = TimeField('Horario de Saida', validators=[Optional()])
    # Tempo de almoço.
    intervalo_minutos = IntegerField('Intervalo (minutos)', default=60)
    # Tolerância de 5 minutos permitida pelo art. 58 da CLT.
    tolerancia_minutos = IntegerField('Tolerancia (minutos, CLT art.58)', default=5)
    submit = SubmitField('Salvar')
