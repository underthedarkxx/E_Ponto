# =====================================================================
# utils/hashing.py — Hash em cadeia para integridade dos registros
# ---------------------------------------------------------------------
# A Portaria 671/2021 (REP-P) exige um mecanismo que prove que os
# registros não foram alterados depois de gravados. Para isso usamos
# uma "hash chain" (blockchain simplificada):
#   - Cada Registro guarda um SHA-256 calculado a partir dos seus
#     campos + o hash do registro anterior.
#   - Para falsificar um único registro antigo, seria preciso recalcular
#     todos os hashes posteriores. O Auditor consegue detectar isso
#     percorrendo a cadeia (verificar_integridade).
# =====================================================================

import hashlib


def calcular_hash(nsr, cnpj, pis_cpf, timestamp_iso, tipo, hash_anterior):
    """SHA-256 hash chain for REP-P integrity.

    O `|` separa os campos para evitar ambiguidade (ex.: "12" + "34"
    vira "1234", mas "12|34" não pode ser confundido com "1|234").
    Quando não há hash anterior (primeiro registro), usamos "GENESIS"
    como sentinela explícito.
    """
    data = f"{nsr}|{cnpj}|{pis_cpf}|{timestamp_iso}|{tipo}|{hash_anterior or 'GENESIS'}"
    # encode('utf-8') -> bytes; hexdigest() -> string hex de 64 caracteres.
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def verificar_integridade(registros):
    """
    Verify hash chain integrity for a list of records ordered by NSR.
    Returns list of (registro, ok: bool).

    Estratégia: recalcular o hash esperado de cada registro usando os
    campos atuais + o hash do anterior. Se algum não bater, alguma
    coisa foi alterada (no campo ou no campo `hash_registro`).
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
        # Compara o hash armazenado com o recalculado.
        ok = reg.hash_registro == esperado
        results.append((reg, ok))
        # Para o próximo: usamos o hash armazenado (não o esperado).
        # Assim conseguimos identificar onde a cadeia quebrou.
        prev_hash = reg.hash_registro
    return results
