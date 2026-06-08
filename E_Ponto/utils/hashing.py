"""Hash em cadeia para garantir a integridade dos registros (REP-P).

Cada Registro guarda um SHA-256 calculado a partir dos seus campos mais
o hash do registro anterior. Alterar um registro antigo exigiria
recalcular toda a cadeia, o que verificar_integridade detecta.
"""

import hashlib


def calcular_hash(nsr, cnpj, pis_cpf, timestamp_iso, tipo, hash_anterior):
    """Calcula o SHA-256 de um registro encadeando o hash anterior.

    O separador '|' evita ambiguidade entre campos; 'GENESIS' marca o
    primeiro registro (sem anterior).
    """
    data = f"{nsr}|{cnpj}|{pis_cpf}|{timestamp_iso}|{tipo}|{hash_anterior or 'GENESIS'}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def verificar_integridade(registros):
    """Verifica a cadeia de hashes de registros ordenados por NSR.

    Retorna lista de (registro, ok: bool). Recalcula o hash esperado de
    cada registro; usa o hash armazenado do anterior para identificar
    onde a cadeia quebrou.
    """
    results = []
    prev_hash = None
    for reg in registros:
        esperado = calcular_hash(
            reg.nsr,
            reg.empresa.cnpj,
            reg.user.pis_nis or reg.user.cpf or '',
            reg.timestamp_utc.isoformat(),
            reg.tipo.value,
            prev_hash
        )
        ok = reg.hash_registro == esperado
        results.append((reg, ok))
        prev_hash = reg.hash_registro
    return results
