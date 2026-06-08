"""Calculo de distancia (Haversine) e validacao de geofence das batidas."""

import math


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distancia em metros entre duas coordenadas GPS (formula de Haversine)."""
    R = 6371000  # raio medio da Terra em metros
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def verificar_geofence(lat, lon, local_trabalho) -> tuple:
    """Retorna (dentro_do_raio: bool, distancia_metros: float).

    Sem coordenadas (do usuario ou do local), trata como dentro (True),
    pois nao ha como afirmar que esta fora.
    """
    if lat is None or lon is None or local_trabalho is None:
        return True, 0.0
    if local_trabalho.latitude is None or local_trabalho.longitude is None:
        return True, 0.0

    dist = haversine(lat, lon, local_trabalho.latitude, local_trabalho.longitude)
    return dist <= local_trabalho.raio_metros, dist
