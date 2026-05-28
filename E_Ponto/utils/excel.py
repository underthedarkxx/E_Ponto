# =====================================================================
# utils/excel.py — Exportacao de relatorios em formato Excel (.xlsx)
# ---------------------------------------------------------------------
# Usa o Pandas (com o engine openpyxl) para montar planilhas a partir
# dos dados ja calculados em utils/banco_horas.py. Cada funcao retorna
# os BYTES do arquivo .xlsx, prontos para serem enviados via send_file.
#
# Sao tres relatorios, conforme prometido no escopo do projeto:
#   - Banco de horas (detalhado, por funcionario/mes)
#   - Frequencia da equipe (resumo, todos os funcionarios no mes)
#   - Horas extras da equipe (resumo focado em extras/atrasos/faltas)
# =====================================================================

from io import BytesIO

import pandas as pd

from E_Ponto.utils.banco_horas import format_min

_DIAS_PT = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
_MESES_PT = ['', 'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def _periodo_label(ano: int, mes: int) -> str:
    return f"{_MESES_PT[mes]}/{ano}"


def gerar_banco_horas_xlsx(empresa, funcionario, resultado) -> bytes:
    """
    Planilha detalhada do banco de horas de UM funcionario no mes.

    Duas abas:
      - "Resumo": totais do mes (trabalhado, esperado, saldo, extras,
        atrasos, faltas).
      - "Detalhamento": uma linha por dia do mes.
    """
    ano, mes = resultado['ano'], resultado['mes']

    # ---- Aba Resumo -------------------------------------------------
    resumo = pd.DataFrame([
        ('Empresa', empresa.trade_name),
        ('Funcionario', funcionario.name),
        ('Cargo', funcionario.cargo or '—'),
        ('Periodo', _periodo_label(ano, mes)),
        ('Horas trabalhadas', format_min(resultado['total_trabalhado_min'])),
        ('Horas esperadas', format_min(resultado['total_esperado_min'])),
        ('Saldo (banco de horas)', format_min(resultado['total_saldo_min'])),
        ('Horas extras', format_min(resultado['total_extra_min'])),
        ('Atrasos', format_min(resultado['total_atraso_min'])),
        ('Faltas (dias)', resultado['total_faltas']),
    ], columns=['Indicador', 'Valor'])

    # ---- Aba Detalhamento -------------------------------------------
    linhas = []
    for d in resultado['dias']:
        linhas.append({
            'Dia': d['dia'].strftime('%d/%m/%Y'),
            'Dia da Semana': _DIAS_PT[d['dia'].weekday()],
            'Trabalhado': format_min(d['trabalhado_min']),
            'Esperado': format_min(d['esperado_min']),
            'Saldo': format_min(d['saldo_min']),
            'Horas Extras': format_min(d['extra_min']),
            'Atraso': format_min(d['atraso_min']),
            'Falta': 'Sim' if d['falta'] else '',
        })
    detalhe = pd.DataFrame(linhas)

    return _to_bytes({'Resumo': resumo, 'Detalhamento': detalhe})


def gerar_frequencia_xlsx(empresa, linhas_funcionarios, ano: int, mes: int) -> bytes:
    """
    Resumo de frequencia/horas extras de TODA a equipe no mes.

    linhas_funcionarios: lista de tuplas (funcionario, resultado_mes),
    onde resultado_mes vem de calcular_saldo_mes.
    """
    dados = []
    for funcionario, resultado in linhas_funcionarios:
        dados.append({
            'Funcionario': funcionario.name,
            'Cargo': funcionario.cargo or '—',
            'Trabalhado': format_min(resultado['total_trabalhado_min']),
            'Esperado': format_min(resultado['total_esperado_min']),
            'Saldo': format_min(resultado['total_saldo_min']),
            'Horas Extras': format_min(resultado['total_extra_min']),
            'Atrasos': format_min(resultado['total_atraso_min']),
            'Faltas': resultado['total_faltas'],
        })
    df = pd.DataFrame(dados) if dados else pd.DataFrame(columns=[
        'Funcionario', 'Cargo', 'Trabalhado', 'Esperado', 'Saldo',
        'Horas Extras', 'Atrasos', 'Faltas',
    ])

    cabecalho = pd.DataFrame([
        ('Empresa', empresa.trade_name),
        ('Periodo', _periodo_label(ano, mes)),
        ('Funcionarios', len(dados)),
    ], columns=['Indicador', 'Valor'])

    return _to_bytes({'Resumo': cabecalho, 'Frequencia': df})


def _to_bytes(abas: dict) -> bytes:
    """Escreve um dict {nome_aba: DataFrame} num .xlsx e devolve os bytes."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for nome, df in abas.items():
            df.to_excel(writer, sheet_name=nome, index=False)
            # Auto-ajuste simples da largura das colunas.
            ws = writer.sheets[nome]
            for i, col in enumerate(df.columns, start=1):
                largura = max(
                    [len(str(col))] + [len(str(v)) for v in df[col].tolist()] or [10]
                )
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = largura + 2
    buf.seek(0)
    return buf.getvalue()
