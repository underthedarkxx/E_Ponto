"""Formularios do RH: solicitar e decidir retificacoes de ponto."""

from flask_wtf import FlaskForm
from wtforms import TextAreaField, DateTimeLocalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional


class RetificacaoForm(FlaskForm):
    """Solicitacao de retificacao aberta pelo funcionario."""
    motivo = TextAreaField('Motivo', validators=[DataRequired()])
    novo_timestamp = DateTimeLocalField(
        'Nova Data/Hora', format='%Y-%m-%dT%H:%M', validators=[Optional()]
    )
    submit = SubmitField('Solicitar Retificacao')


class AprovarRetificacaoForm(FlaskForm):
    """Decisao do RH sobre uma retificacao."""
    acao = SelectField('Decisao', choices=[
        ('aprovar', 'Aprovar'),
        ('rejeitar', 'Rejeitar'),
    ])
    observacao = TextAreaField('Observacao', validators=[Optional()])
    submit = SubmitField('Confirmar')
