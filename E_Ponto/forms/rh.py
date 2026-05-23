# =====================================================================
# forms/rh.py — Formulários do RH
# ---------------------------------------------------------------------
# RetificacaoForm: usado pelo FUNCIONÁRIO para abrir um pedido de
#                  correção de ponto.
# AprovarRetificacaoForm: usado pelo RH para aprovar/rejeitar o pedido.
# =====================================================================

from flask_wtf import FlaskForm
from wtforms import TextAreaField, DateTimeLocalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional


# --- Solicitar retificação (funcionário) -----------------------------
class RetificacaoForm(FlaskForm):
    # Explicação obrigatória do erro.
    motivo = TextAreaField('Motivo', validators=[DataRequired()])
    # DateTimeLocalField renderiza <input type="datetime-local">.
    # O formato bate com o que o navegador envia: "2025-11-04T08:30".
    novo_timestamp = DateTimeLocalField(
        'Nova Data/Hora', format='%Y-%m-%dT%H:%M', validators=[Optional()]
    )
    submit = SubmitField('Solicitar Retificacao')


# --- Decidir retificação (RH) ----------------------------------------
class AprovarRetificacaoForm(FlaskForm):
    acao = SelectField('Decisao', choices=[
        ('aprovar', 'Aprovar'),
        ('rejeitar', 'Rejeitar'),
    ])
    # Comentário opcional que vai pro AuditLog.
    observacao = TextAreaField('Observacao', validators=[Optional()])
    submit = SubmitField('Confirmar')
