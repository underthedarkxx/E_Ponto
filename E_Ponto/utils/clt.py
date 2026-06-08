"""Constantes e regras da CLT para jornada de trabalho.

Usadas no calculo de horas trabalhadas, banco de horas e deteccao de
violacoes (intervalos, hora noturna, etc.).
"""

from datetime import timedelta

# Art. 58 §1: tolerancia de ate 5 minutos por batida
TOLERANCIA_POR_BATIDA = timedelta(minutes=5)

# Intervalo intrajornada (almoco): >6h exige 1h; 4–6h exige 15 min
INTERVALO_INTRAJORNADA_LONGO = timedelta(hours=1)
INTERVALO_INTRAJORNADA_CURTO = timedelta(minutes=15)

# Art. 66: descanso minimo entre jornadas = 11h
INTERVALO_INTERJORNADA = timedelta(hours=11)

# Adicional noturno: 22h as 5h (horario urbano)
HORA_NOTURNA_INICIO = 22
HORA_NOTURNA_FIM = 5


def calcular_horas_trabalhadas(entrada, saida, intervalo_minutos=60):
    """Retorna o tempo trabalhado (timedelta), abatendo o intervalo.

    Simplificacao: jornadas acima de 6h descontam o intervalo padrao.
    """
    if not entrada or not saida:
        return timedelta(0)

    total = saida - entrada
    jornada_horas = total.total_seconds() / 3600
    if jornada_horas > 6:
        total -= timedelta(minutes=intervalo_minutos)

    # Evita resultado negativo em caso de dados inconsistentes
    return max(total, timedelta(0))


def calcular_horas_extras(trabalhado, jornada_contratada_horas=8.0):
    """Retorna as horas extras (timedelta) alem da jornada contratada."""
    contratada = timedelta(hours=jornada_contratada_horas)
    if trabalhado > contratada:
        return trabalhado - contratada
    return timedelta(0)


def verificar_intervalo_interjornada(saida_anterior, entrada_atual):
    """True se o descanso minimo de 11h entre jornadas foi respeitado."""
    # Sem dados, retorna True para nao gerar alarme falso
    if not saida_anterior or not entrada_atual:
        return True
    return (entrada_atual - saida_anterior) >= INTERVALO_INTERJORNADA
