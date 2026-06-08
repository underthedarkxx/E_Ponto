"""Formularios da area administrativa: usuarios, locais e jornadas."""

from datetime import date

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, SelectField, BooleanField, SubmitField,
                     DecimalField, IntegerField, TimeField, DateField)
from wtforms.validators import DataRequired, Optional, Length, Email


# UFs brasileiras para o <select> de endereco ('' = nenhum selecionado)
_UF_CHOICES = [('', '--')] + [(s, s) for s in [
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR',
    'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO',
]]


class UsuarioForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    email = StringField('E-mail', validators=[DataRequired(), Email(check_deliverability=False)])
    cpf = StringField('CPF', validators=[Optional(), Length(max=15)])
    pis_nis = StringField('PIS/NIS', validators=[Optional(), Length(max=15)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=15)])
    cargo = StringField('Cargo', validators=[Optional(), Length(max=80)])
    # A contagem de ponto comeca a partir da data de admissao;
    # se vazia, a view assume o dia do cadastro
    data_admissao = DateField('Data de admissão', validators=[Optional()],
                              default=date.today)
    role = SelectField('Papel', choices=[
        ('funcionario', 'Funcionario'),
        ('rh', 'RH'),
        ('admin', 'Administrador'),
    ])
    # 0 = sem jornada definida; choices preenchidos na view
    jornada_id = SelectField('Jornada (horário contratual)', coerce=int,
                             validators=[Optional()])
    photo = FileField('Foto (opcional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG ou PNG.'),
    ])
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class LocalTrabalhoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    logradouro = StringField('Logradouro', validators=[Optional(), Length(max=120)])
    numero = StringField('Numero', validators=[Optional(), Length(max=10)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=60)])
    uf = SelectField('UF', choices=_UF_CHOICES, validators=[Optional()])
    cep = StringField('CEP', validators=[Optional(), Length(max=10)])
    # places=7: precisao GPS de ~1 cm
    latitude = DecimalField('Latitude', places=7, validators=[Optional()])
    longitude = DecimalField('Longitude', places=7, validators=[Optional()])
    raio_metros = IntegerField('Raio (metros)', default=200)
    submit = SubmitField('Salvar')


class JornadaForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(max=60)])
    tipo = SelectField('Tipo', choices=[
        ('padrao', 'Padrao (8h/dia)'),
        ('12x36', '12x36'),
        ('6x1', '6x1'),
        ('flexivel', 'Flexivel'),
    ])
    carga_horaria_semanal = DecimalField('Carga Horaria Semanal (h)', places=2, default=44)
    horario_entrada = TimeField('Horario de Entrada', validators=[Optional()])
    horario_saida = TimeField('Horario de Saida', validators=[Optional()])
    intervalo_minutos = IntegerField('Intervalo (minutos)', default=60)
    # Tolerancia permitida pelo art. 58 da CLT
    tolerancia_minutos = IntegerField('Tolerancia (minutos, CLT art.58)', default=5)
    submit = SubmitField('Salvar')
