# =====================================================================
# utils/clt.py — Regras da CLT para jornada de trabalho
# ---------------------------------------------------------------------
# Centraliza as constantes e funções relacionadas à legislação
# trabalhista brasileira (CLT — Consolidação das Leis do Trabalho).
# São usadas pelo cálculo de horas trabalhadas, banco de horas e
# detecção de violações (intervalo interjornada, hora noturna, etc.).
# =====================================================================

from datetime import timedelta

# ---- Constantes legais ----------------------------------------------
# Art. 58 §1º da CLT: tolerância de até 5 minutos por batida.
TOLERANCIA_POR_BATIDA = timedelta(minutes=5)

# Intervalo intrajornada (almoço) para jornadas longas (>6h): mín. 1h.
INTERVALO_INTRAJORNADA_LONGO = timedelta(hours=1)
# Para jornadas de 4–6h: mínimo de 15 minutos.
INTERVALO_INTRAJORNADA_CURTO = timedelta(minutes=15)

# Art. 66 da CLT: descanso mínimo entre jornadas = 11h.
INTERVALO_INTERJORNADA = timedelta(hours=11)

# Adicional noturno: 22h às 5h (horário urbano).
HORA_NOTURNA_INICIO = 22
HORA_NOTURNA_FIM = 5


def calcular_horas_trabalhadas(entrada, saida, intervalo_minutos=60):
    """Returns timedelta of actual worked time, discounting break.

    Regra simplificada: se a jornada total ultrapassou 6 horas, abate
    o intervalo padrão (60 min). Para jornadas menores, não há
    desconto automático.
    """
    # Sem uma das pontas, não dá pra calcular.
    if not entrada or not saida:
        return timedelta(0)

    total = saida - entrada
    # total_seconds() pra fazer aritmética escalar.
    jornada_horas = total.total_seconds() / 3600
    if jornada_horas > 6:
        total -= timedelta(minutes=intervalo_minutos)

    # max() evita resultado negativo se houver inconsistência (ex.:
    # saída antes da entrada por algum bug nos dados).
    return max(total, timedelta(0))


def calcular_horas_extras(trabalhado, jornada_contratada_horas=8.0):
    """Returns timedelta of overtime."""
    contratada = timedelta(hours=jornada_contratada_horas)
    if trabalhado > contratada:
        return trabalhado - contratada
    return timedelta(0)


def verificar_intervalo_interjornada(saida_anterior, entrada_atual):
    """Returns True if minimum 11h inter-day rest was respected."""
    # Se faltar dado, retornamos True para não emitir alarme falso.
    if not saida_anterior or not entrada_atual:
        return True
    return (entrada_atual - saida_anterior) >= INTERVALO_INTERJORNADA
