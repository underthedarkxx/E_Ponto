# =====================================================================
# utils/geo.py — Cálculo de distância e validação de geofence
# ---------------------------------------------------------------------
# Quando o funcionário bate ponto, recebemos lat/long do navegador.
# Aqui calculamos a distância para o local cadastrado e decidimos
# se a batida está "dentro do raio" (válida) ou "fora" (suspeita).
# =====================================================================

import math


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Returns distance in meters between two GPS coordinates.

    Fórmula de Haversine: calcula a distância "em arco" entre dois
    pontos numa esfera, aproximando a Terra por uma esfera de raio
    R = 6371000 m (raio médio). Erro tipicamente < 0,5%.
    """
    R = 6371000  # raio da Terra em metros
    # math.radians converte de graus pra radianos (que sin/cos pedem).
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    # Núcleo da fórmula. `a` é a metade do quadrado do "ângulo central".
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    # 2 * atan2(...) recupera o ângulo, multiplicado pelo raio dá a distância.
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def verificar_geofence(lat, lon, local_trabalho) -> tuple:
    """
    Returns (dentro_do_raio: bool, distancia_metros: float).

    Política: se faltar alguma informação (lat/lon do usuário ou
    do local), tratamos como "dentro" (True) — não temos como
    afirmar que está fora. O front-end pode bloquear o envio se
    quiser ser mais estrito.
    """
    # Sem coordenadas do usuário: não tem como julgar.
    if lat is None or lon is None or local_trabalho is None:
        return True, 0.0
    # Local cadastrado mas sem coordenadas: idem.
    if local_trabalho.latitude is None or local_trabalho.longitude is None:
        return True, 0.0

    dist = haversine(lat, lon, local_trabalho.latitude, local_trabalho.longitude)
    # Dentro do raio configurado (padrão 200m)?
    return dist <= local_trabalho.raio_metros, dist
