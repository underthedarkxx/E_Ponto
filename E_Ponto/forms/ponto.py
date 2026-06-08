"""Formulario para bater ponto.

Os campos latitude/longitude/precisao sao HiddenField preenchidos por
JavaScript via API Geolocation do navegador.
"""

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional, Length


class BaterPontoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[
        ('entrada', 'Entrada'),
        ('saida_almoco', 'Saida para Almoco'),
        ('retorno_almoco', 'Retorno do Almoco'),
        ('saida', 'Saida Final'),
    ])
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    precisao = HiddenField('Precisao')
    local_trabalho_id = SelectField('Local de Trabalho', coerce=int, validators=[Optional()])
    # Preenchida quando a batida ocorre fora do raio
    justificativa = TextAreaField('Justificativa (opcional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Registrar Ponto')
