# =====================================================================
# gerar_resumo_pdf.py — Gera o PDF "resumo_eponto.pdf" do projeto
# ---------------------------------------------------------------------
# Script independente da aplicação Flask. Quando executado, monta um
# documento PDF com o resumo técnico de todo o sistema E-Ponto
# (stack, modelo de dados, blueprints, utilitários, segurança).
#
# Não acessa o banco de dados — só usa ReportLab para construir o PDF
# a partir das strings/listas definidas aqui no próprio arquivo.
# =====================================================================

"""
Gera um PDF com o resumo detalhado do sistema E-Ponto.
Uso:
    cd ProjetoE_Ponto
    source venv/bin/activate
    python gerar_resumo_pdf.py
Saida: resumo_eponto.pdf na raiz do projeto.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


# Nome do arquivo de saída (gerado na pasta onde o script for rodado).
OUTPUT = "resumo_eponto.pdf"


def build_styles():
    """Cria um dicionário de estilos visuais para reuso nos Paragraphs.

    ParagraphStyle herda de um base (Title, Heading1, Normal, etc.) e
    sobrescreve só o que queremos mudar (fonte, cor, espaçamento).
    """
    base = getSampleStyleSheet()
    styles = {
        # Título da capa.
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=22,
            textColor=colors.HexColor("#0d3b66"), spaceAfter=6, alignment=TA_LEFT,
        ),
        # Subtítulo logo abaixo do título.
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=11,
            textColor=colors.HexColor("#555555"), spaceAfter=18, alignment=TA_LEFT,
        ),
        # Cabeçalho de seção (1. Stack, 2. Modelo, etc.).
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontSize=15,
            textColor=colors.HexColor("#0d3b66"), spaceBefore=14, spaceAfter=8,
        ),
        # Subcabeçalho (2.1, 2.2 etc.).
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=12,
            textColor=colors.HexColor("#1d4e89"), spaceBefore=10, spaceAfter=6,
        ),
        # Parágrafo corrido com justificado.
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=10, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        # Item de lista (precisa do indent à esquerda).
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontSize=10, leading=14,
            leftIndent=14, bulletIndent=2, spaceAfter=2,
        ),
        # Bloco de código (fundo cinza, fonte mono).
        "code": ParagraphStyle(
            "code", parent=base["Code"], fontSize=9, leading=12,
            textColor=colors.HexColor("#222222"),
            backColor=colors.HexColor("#f4f6f8"),
            borderPadding=6, leftIndent=4, rightIndent=4, spaceAfter=8,
        ),
    }
    return styles


def make_table(data, col_widths, header=True):
    """Helper que cria uma Table do ReportLab com estilo padrão.

    `data` é lista de listas (linhas x colunas); primeira linha é
    o cabeçalho se `header=True`.
    """
    # repeatRows=1: se a tabela quebrar de página, repete o header.
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)

    # Estilo base aplicado a TODA a tabela.
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8dc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        # Zebra: linhas alternadas com cor de fundo diferente.
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.white]),
    ]
    # Adiciona destaque visual ao cabeçalho (azul + branco + negrito).
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d3b66")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


def bullets(items, style):
    """Converte uma lista de strings em uma lista de Paragraphs
    formatados como bullets (com o caractere &bull; e um espaço &nbsp;)."""
    return [Paragraph(f"&bull;&nbsp; {item}", style) for item in items]


def build_story(styles):
    """Constrói a `story` — sequência de elementos que vão ser
    desenhados no PDF, na ordem em que aparecem aqui.

    No ReportLab, a "story" é literalmente uma lista de fluxos
    (Paragraph, Table, Spacer, PageBreak...) que o doc.build() consome.
    """
    s = styles
    story = []

    # ============ CAPA / TITULO ============
    story.append(Paragraph("Sistema E-Ponto", s["title"]))
    story.append(Paragraph(
        "Resumo tecnico do projeto - Flask + REP-P (Portaria MTP n. 671/2021)<br/>"
        "UVV - Programacao Avancada para Web",
        s["subtitle"]
    ))

    # Parágrafo introdutório descrevendo o sistema.
    story.append(Paragraph(
        "Aplicacao web em Flask para registro eletronico de ponto, projetada para "
        "atender as exigencias legais brasileiras de um REP-P (Registro Eletronico "
        "de Ponto via Programa). Implementa NSR sequencial, cadeia de hashes SHA-256, "
        "geolocalizacao com geofence, exportacao de AFD/AEJ, comprovante em PDF, "
        "autenticacao 2FA TOTP e RBAC multi-tenant.",
        s["body"]
    ))

    # ============ 1. STACK ============
    story.append(Paragraph("1. Stack e estrutura geral", s["h1"]))

    story.append(Paragraph("Dependencias principais", s["h2"]))
    # extend() em vez de append() porque bullets() devolve uma lista.
    story.extend(bullets([
        "Flask + Flask-SQLAlchemy + Flask-Migrate (banco e migracoes)",
        "Flask-Login + Flask-Bcrypt + pyotp + qrcode (autenticacao + 2FA TOTP)",
        "Flask-WTF (CSRF + formularios)",
        "Flask-Limiter (rate limiting)",
        "ReportLab (geracao do comprovante e deste proprio PDF)",
        "psycopg2-binary (suporte a PostgreSQL em producao)",
    ], s["bullet"]))

    story.append(Paragraph("Estrutura de pastas", s["h2"]))
    # Tag <br/> e &nbsp; do ReportLab funcionam como em HTML — útil
    # para preservar identação dentro de um Paragraph estilo "code".
    story.append(Paragraph(
        "ProjetoE_Ponto/<br/>"
        "&nbsp;&nbsp;app.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# factory: create_app()<br/>"
        "&nbsp;&nbsp;tasks.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# invoke tasks (install/run/test/seed/zip)<br/>"
        "&nbsp;&nbsp;pyproject.toml<br/>"
        "&nbsp;&nbsp;.env.{dev,test,prod}<br/>"
        "&nbsp;&nbsp;E_Ponto/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;ext/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# config, db, auth, wtf, limiter, migrate, debugtoolbar<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;models/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 14 modelos SQLAlchemy<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;views/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 6 blueprints<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;forms/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# WTForms<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;utils/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# nsr, hashing, geo, clt, afd, aej, pdf, decorators<br/>"
        "&nbsp;&nbsp;templates/&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Jinja2 + Bootstrap 5",
        s["code"]
    ))

    story.append(Paragraph(
        "A factory <b>create_app()</b> inicializa em ordem: config -> db -> "
        "register_models -> auth -> migrate -> wtf/limiter (se nao TESTING) -> "
        "debugtoolbar -> blueprints.",
        s["body"]
    ))

    # ============ 2. MODELO DE DADOS ============
    story.append(Paragraph("2. Modelo de dados (14 tabelas)", s["h1"]))
    # Tabela resumo do schema. Cada item é uma linha [coluna1, coluna2].
    modelos = [
        ["Tabela", "Funcao"],
        ["users", "Usuario (CPF, PIS/NIS, totp_secret, two_factor_enabled)"],
        ["roles", "Papeis: super_admin, admin, rh, funcionario"],
        ["roles_has_users", "M:N com escopo por empresa (unique user+role+business)"],
        ["businesses", "Empresa empregadora (CNPJ + endereco REP-P)"],
        ["levels", "Niveis opcionais anexados ao RoleUser"],
        ["addresses / cities", "Endereco do funcionario"],
        ["locais_trabalho", "Locais fisicos com lat/lon + raio para geofence"],
        ["jornadas", "Tipos de jornada (padrao, 12x36, 6x1, flexivel)"],
        ["escalas_funcionarios", "Vinculo funcionario - jornada - local com datas"],
        ["registros", "Batidas de ponto (nucleo do sistema)"],
        ["nsr_sequencias", "Sequencial NSR por empresa"],
        ["retificacoes", "Pedidos de correcao (PENDENTE/APROVADA/REJEITADA)"],
        ["banco_horas", "Saldo mensal (positivos, negativos, saldo)"],
        ["audit_logs", "Trilha de auditoria generica (dados_antes/depois)"],
    ]
    # Larguras em centímetros: 4.5cm para tabela, 12cm para função.
    story.append(make_table(modelos, [4.5 * cm, 12 * cm]))

    story.append(Paragraph("Destaques da tabela <b>registros</b>", s["h2"]))
    story.extend(bullets([
        "<b>nsr</b> unico por empresa (UniqueConstraint empresa_id+nsr)",
        "<b>timestamp_utc</b>, latitude, longitude, precisao_metros, ip_address",
        "<b>suspeito_geo</b> (boolean - fora do raio do local)",
        "<b>hash_registro</b> e <b>hash_anterior</b> formando cadeia SHA-256 "
        "(similar a blockchain) - inviolabilidade",
        "<b>tipo</b>: ENTRADA / SAIDA / INCLUSAO / ALTERACAO",
    ], s["bullet"]))

    # PageBreak força quebra de página — útil para separar grandes seções.
    story.append(PageBreak())

    # ============ 3. BLUEPRINTS ============
    story.append(Paragraph("3. Os 6 blueprints (camada de rotas)", s["h1"]))

    # Cada item: (titulo do blueprint, lista de rotas+descrição).
    bps = [
        ("auth (views/auth.py)", [
            "/auth/login - bcrypt; se 2FA, redireciona para verify-2fa",
            "/auth/verify-2fa - codigo TOTP de 6 digitos",
            "/auth/setup-2fa - gera secret pyotp + QR Code base64",
            "/auth/logout",
        ]),
        ("main (views/main.py)", [
            "/ /index - lista empresas do usuario; salva empresa_id na sessao",
            "/empresa/&lt;id&gt;/selecionar - troca de empresa ativa",
        ]),
        ("ponto (views/ponto.py) - nucleo funcional", [
            "/ponto/bater - pega ultimo hash -> NSR atomico (FOR UPDATE) -> "
            "SHA-256 -> grava com geolocalizacao + flag suspeito",
            "/ponto/historico - paginacao 30/pag",
            "/ponto/comprovante/&lt;id&gt; - visualizacao HTML",
            "/ponto/comprovante/&lt;id&gt;/pdf - PDF via ReportLab",
        ]),
        ("funcionario (views/funcionario.py)", [
            "/funcionario/ - dashboard pessoal (batidas do dia + retificacoes)",
            "/funcionario/retificar/&lt;reg_id&gt; - abre solicitacao de correcao",
        ]),
        ("rh (views/rh.py) - protegido por role_required(rh, admin, super_admin)", [
            "/rh/ - totais (pendentes, batidas do dia, suspeitos)",
            "/rh/registros - todas as batidas com filtros por usuario/data",
            "/rh/retificacoes + /decidir/&lt;id&gt; - aprovar/rejeitar",
            "/rh/relatorios/afd - gera AFD (Portaria 671/2021)",
            "/rh/relatorios/aej - gera AEJ (Arquivo Eletronico de Jornada)",
        ]),
        ("admin (views/admin.py) - role_required(admin, super_admin)", [
            "/admin/ - dashboard com contadores",
            "/admin/usuarios + /novo - cria usuario com senha temporaria",
            "/admin/locais + /novo - cadastra local com lat/lon/raio",
            "/admin/jornadas + /nova - cadastra jornada (padrao, 12x36, 6x1, flexivel)",
        ]),
    ]
    for titulo, rotas in bps:
        story.append(Paragraph(titulo, s["h2"]))
        story.extend(bullets(rotas, s["bullet"]))

    story.append(PageBreak())

    # ============ 4. UTILITARIOS ============
    story.append(Paragraph("4. Utilitarios - inteligencia do REP-P", s["h1"]))
    utils = [
        ["Arquivo", "O que faz"],
        ["utils/nsr.py",
         "get_next_nsr(empresa_id) - incrementa NSR com with_for_update()"],
        ["utils/hashing.py",
         "SHA-256 sobre nsr|cnpj|pis_cpf|timestamp|tipo|hash_anterior + "
         "verificar_integridade()"],
        ["utils/geo.py",
         "Formula de Haversine + verificar_geofence(lat, lon, local)"],
        ["utils/clt.py",
         "Horas trabalhadas, horas extras, interjornada 11h, tolerancia 5min "
         "(CLT art.58)"],
        ["utils/afd.py",
         "Layout AFD: tipo 1 (header), tipo 3 (batidas), tipo 9 (trailer) "
         "em ASCII com pad fixo"],
        ["utils/aej.py",
         "AEJ mensal por funcionario agrupando marcacoes por dia "
         "(ate 6 marcacoes)"],
        ["utils/pdf.py",
         "Comprovante PDF: empregador, CNPJ, NSR, data/hora, geo, hash"],
        ["utils/decorators.py",
         "@role_required(*roles) e @empresa_required"],
    ]
    story.append(make_table(utils, [4 * cm, 12.5 * cm]))

    # ============ 5. SEGURANCA ============
    story.append(Paragraph("5. Seguranca implementada", s["h1"]))
    seguranca = [
        "<b>2FA TOTP</b> (pyotp + qrcode) opcional por usuario",
        "<b>Bcrypt</b> para senhas",
        "<b>CSRF</b> via Flask-WTF (desabilitado em TESTING)",
        "<b>Rate limiting</b> (Flask-Limiter, 200/dia + 50/hora por IP)",
        "<b>Cadeia de hashes SHA-256</b> - alterar um ponto invalida todos os seguintes",
        "<b>NSR atomico</b> com row-level lock (SELECT ... FOR UPDATE)",
        "<b>Geofence</b> com flag suspeito_geo quando fora do raio",
        "<b>Auditoria</b> (audit_logs) com dados_antes/dados_depois",
        "<b>RBAC</b> multi-tenant (papel por empresa via RoleUser)",
        "<b>IP do request</b> registrado em cada batida",
    ]
    story.extend(bullets(seguranca, s["bullet"]))

    # ============ 6. AMBIENTES E TASKS ============
    story.append(Paragraph("6. Ambientes e tasks (invoke)", s["h1"]))
    tasks = [
        ["Comando", "Acao"],
        ["inv install", 'pip install -e ".[dev,test]"'],
        ["inv run", "carrega .env.dev + flask run (SQLite eponto_dev.db)"],
        ["inv test", ".env.test + pytest"],
        ["inv prod", ".env.prod"],
        ["inv initdb", "db.create_all()"],
        ["inv seed",
         "cria roles, super_admin (admin@eponto.com / admin123), "
         "empresa demo, joao@eponto.com / joao123"],
        ["inv lint", "flake8"],
        ["inv format", "black ."],
        ["inv zip", "empacota excluindo venv/__pycache__/.git"],
    ]
    story.append(make_table(tasks, [3.5 * cm, 13 * cm]))

    # ============ 7. CONFORMIDADE LEGAL ============
    story.append(Paragraph(
        "7. Conformidade legal (Portaria MTP 671/2021)", s["h1"]
    ))
    conformidade = [
        "NSR sequencial por empregador",
        "Hash de integridade encadeado",
        "Geracao de AFD e AEJ no layout oficial",
        "Comprovante imediato em PDF",
        "Dados do empregador (CNPJ, CEI/CAEPF, endereco)",
        "Dados do trabalhador (PIS/NIS, CPF)",
        "Timestamp UTC com timezone",
        "Tipos de registro (entrada/saida/inclusao/alteracao)",
        "Retificacao com aprovacao do RH (nao sobrescreve historico)",
    ]
    story.extend(bullets(conformidade, s["bullet"]))

    # ============ RESUMO ============
    story.append(Paragraph("Resumo em uma frase", s["h1"]))
    story.append(Paragraph(
        "E um <b>REP-P web multi-tenant</b>: funcionarios batem ponto pelo "
        "navegador com geolocalizacao, cada batida vira um Registro imutavel "
        "com NSR e hash SHA-256 encadeado, o RH revisa retificacoes e exporta "
        "os arquivos AFD/AEJ no formato exigido pela Portaria 671/2021, tudo "
        "organizado em blueprints e protegido por login + 2FA TOTP + RBAC por "
        "empresa.",
        s["body"]
    ))

    return story


def main():
    """Ponto de entrada: monta o documento e escreve no disco."""
    # SimpleDocTemplate cuida da paginação e das margens.
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        # Metadados que aparecem nas "propriedades" do PDF.
        title="Resumo E-Ponto", author="UVV - Programacao Avancada para Web",
    )
    styles = build_styles()
    story = build_story(styles)
    # build() consome a story e escreve o arquivo de saída.
    doc.build(story)
    print(f"[OK] PDF gerado: {OUTPUT}")


# Padrão Python: só roda main() quando o arquivo é executado direto
# (não quando importado por outro módulo).
if __name__ == "__main__":
    main()
