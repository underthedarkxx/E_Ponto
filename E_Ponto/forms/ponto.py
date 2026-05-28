# =====================================================================
# forms/ponto.py — Formulário para bater ponto
# ---------------------------------------------------------------------
# Quando o funcionário aperta "Registrar Ponto", os campos abaixo
# vão num POST para a rota /ponto/bater. Os campos latitude/longitude
# são preenchidos por JavaScript usando a API Geolocation do navegador
# (por isso são HiddenField — invisíveis ao usuário).
# =====================================================================

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional, Length


class BaterPontoForm(FlaskForm):
    # Tipo da batida (corresponde aos valores de TipoRegistro).
    tipo = SelectField('Tipo', choices=[
        ('entrada', 'Entrada'),
        ('saida_almoco', 'Saida para Almoco'),
        ('retorno_almoco', 'Retorno do Almoco'),
        ('saida', 'Saida Final'),
    ])
    # Campos preenchidos automaticamente pelo JavaScript após pegar
    # a geolocalização do navegador.
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    # Precisão (em metros) reportada pelo GPS.
    precisao = HiddenField('Precisao')
    # Local onde o funcionário está batendo. coerce=int garante que
    # o valor recebido como string vire int antes da validação.
    local_trabalho_id = SelectField('Local de Trabalho', coerce=int, validators=[Optional()])
    # Quando o funcionário bate fora do raio, escreve aqui o motivo
    # (ex.: "Reunião em campo na obra X").
    justificativa = TextAreaField('Justificativa (opcional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Registrar Ponto')
