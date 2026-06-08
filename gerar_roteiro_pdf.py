# =====================================================================
# gerar_roteiro_pdf.py — Gera o "roteiro_apresentacao.pdf"
# ---------------------------------------------------------------------
# Script independente da aplicacao Flask. Monta o ROTEIRO da
# apresentacao do E-Ponto, dividido em 3 partes (uma por integrante) e
# organizado na ordem dos 7 criterios tecnicos de avaliacao.
#
# Reaproveita o mesmo estilo visual de gerar_resumo_pdf.py (ReportLab).
# Uso:
#     cd E_Ponto
#     source venv/bin/activate
#     python gerar_roteiro_pdf.py
# Saida: roteiro_apresentacao.pdf na raiz do projeto.
# =====================================================================

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


OUTPUT = "roteiro_apresentacao.pdf"


def build_styles():
    """Estilos visuais reutilizaveis (mesma identidade do resumo)."""
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=22,
            textColor=colors.HexColor("#0d3b66"), spaceAfter=6, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=11,
            textColor=colors.HexColor("#555555"), spaceAfter=18, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontSize=15,
            textColor=colors.HexColor("#0d3b66"), spaceBefore=14, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=12,
            textColor=colors.HexColor("#1d4e89"), spaceBefore=10, spaceAfter=6,
        ),
        # Linha que indica quem fala / em que arquivo (cor de destaque).
        "meta": ParagraphStyle(
            "meta", parent=base["Normal"], fontSize=9.5, leading=13,
            textColor=colors.HexColor("#0a7d4d"), spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=10, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        # Fala do apresentador (citacao com leve recuo).
        "fala": ParagraphStyle(
            "fala", parent=base["Normal"], fontSize=10, leading=14,
            alignment=TA_JUSTIFY, leftIndent=12, rightIndent=6,
            textColor=colors.HexColor("#222222"),
            backColor=colors.HexColor("#f4f6f8"),
            borderPadding=6, spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontSize=10, leading=14,
            leftIndent=14, bulletIndent=2, spaceAfter=2,
        ),
    }
    return styles


def make_table(data, col_widths, header=True):
    """Tabela com estilo padrao (zebra + header azul)."""
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8dc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.white]),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d3b66")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    t.setStyle(TableStyle(style))
    return t


def bullets(items, style):
    """Lista de strings -> lista de Paragraphs com marcador."""
    return [Paragraph(f"&bull;&nbsp; {item}", style) for item in items]


def criterio(story, s, numero, titulo, quem, arquivos, fala, mostrar,
             impacto=None):
    """Helper que monta o bloco de UM criterio no roteiro."""
    story.append(Paragraph(f"Criterio {numero} - {titulo}", s["h2"]))
    story.append(Paragraph(
        f"<b>Quem fala:</b> {quem} &nbsp;|&nbsp; <b>Arquivos:</b> {arquivos}",
        s["meta"]
    ))
    story.append(Paragraph(f"<i>Fala:</i> &ldquo;{fala}&rdquo;", s["fala"]))
    if mostrar:
        story.append(Paragraph("<b>O que mostrar:</b>", s["body"]))
        story.extend(bullets(mostrar, s["bullet"]))
    if impacto:
        story.append(Paragraph(
            f"<b>Frase de impacto:</b> <i>{impacto}</i>", s["body"]
        ))
    story.append(Spacer(1, 6))


def build_story(styles):
    s = styles
    story = []

    # ============ CAPA ============
    story.append(Paragraph("E-Ponto - Roteiro de Apresentacao", s["title"]))
    story.append(Paragraph(
        "Controle de ponto digital em Flask (REP-P / Portaria MTP n. 671/2021)<br/>"
        "UVV - Programacao Avancada para Web<br/>"
        "Integrantes: Lucas Andre, Roberto Dias, Rychard Chaves",
        s["subtitle"]
    ))
    story.append(Paragraph(
        "Este roteiro divide a apresentacao em <b>3 partes</b> (uma por "
        "integrante) e percorre os <b>7 criterios tecnicos</b> da avaliacao na "
        "ordem oficial (1 a 7), indicando em cada ponto quem fala, qual arquivo "
        "abrir e o que destacar. Tempo sugerido: ~12 a 15 minutos + demonstracao "
        "ao vivo.",
        s["body"]
    ))

    # ============ DIVISAO EM 3 PARTES ============
    story.append(Paragraph("Divisao em 3 partes", s["h1"]))
    partes = [
        ["Parte", "Responsavel", "Tema", "Criterios"],
        ["1", "Lucas Andre", "Arquitetura e Organizacao",
         "1 (App Factory), 2 (Blueprints)"],
        ["2", "Roberto Dias", "Dados e Regras de Negocio",
         "3 (Formularios), 6 (Persistencia/ORM)"],
        ["3", "Rychard Chaves", "Interface, Testes e Qualidade",
         "4 (Templates), 5 (Testes), 7 (Qualidade)"],
    ]
    story.append(make_table(partes, [1.3 * cm, 3.2 * cm, 5.2 * cm, 6.8 * cm]))
    story.append(Paragraph(
        "A divisao e tematica (cada pessoa domina um bloco coerente), mas a "
        "apresentacao segue a ordem dos criterios 1 a 7, alternando os "
        "apresentadores conforme indicado abaixo.",
        s["body"]
    ))

    # ============ ABERTURA ============
    story.append(Paragraph("Abertura (~30s) - Lucas Andre", s["h2"]))
    story.append(Paragraph(
        "&ldquo;Boa noite. Somos o Grupo [X] e vamos apresentar o <b>E-Ponto</b>, "
        "uma plataforma web de controle de ponto digital para empresas de ate "
        "200 funcionarios. Diferente de um CRUD simples, o E-Ponto implementa as "
        "exigencias legais do REP-P da Portaria 671/2021: numero sequencial de "
        "registro, cadeia de hashes anti-fraude e geolocalizacao. Foi feito em "
        "<b>Flask</b>, e vamos mostrar como ele atende cada criterio "
        "tecnico.&rdquo;",
        s["fala"]
    ))

    story.append(PageBreak())

    # ============ PARTE 1 ============
    story.append(Paragraph("Parte 1 - Arquitetura e Organizacao (Lucas Andre)",
                           s["h1"]))

    criterio(
        story, s, 1, "Arquitetura Modular e Application Factory",
        "Lucas Andre", "app.py",
        "O coracao da arquitetura e o padrao Application Factory: em vez de "
        "criar o Flask no nivel do modulo, temos a funcao create_app(test_config). "
        "Isso permite criar instancias diferentes - uma para producao, outra para "
        "os testes com banco em memoria - e evita import circular entre extensoes "
        "e modelos.",
        [
            "A funcao create_app() e a ordem de inicializacao (app.py).",
            "Cada extensao segue a convencao init_app(app): config -> db + "
            "register_models() -> auth -> migrate -> mail -> wtf/limiter -> "
            "debugtoolbar -> views.",
            "CSRF e Rate-Limiter so ativam FORA do modo de teste (decisao "
            "consciente para nao atrapalhar os testes).",
            "register_models() garante que o SQLAlchemy enxergue todas as "
            "tabelas antes de qualquer operacao de schema.",
        ],
        impacto="A fabrica desacopla a montagem da aplicacao do seu uso - e o "
                "que torna possivel testar tudo isso de forma isolada.",
    )

    criterio(
        story, s, 2, "Organizacao em Modulos / Blueprints / Rotas",
        "Lucas Andre", "E_Ponto/ext/, E_Ponto/views/__init__.py",
        "A responsabilidade e separada por camadas e por dominio. O pacote "
        "E_Ponto/ tem ext/ (extensoes), models/ (dados), forms/ (validacao), "
        "views/ (rotas) e utils/ (regras de negocio). Sao 6 Blueprints, um por "
        "area do sistema.",
        [
            "Mostrar a estrutura de pastas (tree ou print).",
            "Os 6 Blueprints em views/__init__.py: auth (/auth), main (/), "
            "ponto (/ponto), admin (/admin), rh (/rh), funcionario "
            "(/funcionario).",
            "O views/__init__.py tambem centraliza os error handlers "
            "(403/404/500) e os filtros Jinja de fuso horario.",
        ],
        impacto="Se amanha o RH precisar de uma tela nova, sabemos exatamente "
                "onde mexer - views/rh.py - sem tocar no resto.",
    )

    story.append(PageBreak())

    # ============ PARTE 2 ============
    story.append(Paragraph(
        "Parte 2 - Dados e Regras de Negocio (Roberto Dias)", s["h1"]))

    criterio(
        story, s, 3, "Formularios e Validacao",
        "Roberto Dias", "E_Ponto/forms/, views/ponto.py",
        "Usamos Flask-WTF / WTForms para validacao no servidor - nunca confiamos "
        "so no navegador. Cada formulario e uma classe com seus validadores.",
        [
            "forms/ponto.py (BaterPontoForm): SelectField de tipo, "
            "latitude/longitude/precisao como HiddenField (preenchidos por JS), "
            "local_trabalho_id com coerce=int, justificativa com Length(max=255).",
            "Na view, form.validate_on_submit() so executa a logica se os dados "
            "forem validos (views/ponto.py).",
            "Em producao, o CSRF protege todos os POSTs; nos testes ele e "
            "desligado de proposito.",
        ],
        impacto="Validacao no servidor e seguranca; o front pode mentir, o "
                "backend nao deixa.",
    )

    criterio(
        story, s, 6, "Persistencia de Dados e ORM",
        "Roberto Dias", "E_Ponto/models/, ext/db.py, migrations/",
        "Persistencia com SQLAlchemy 2.x no estilo moderno Mapped/mapped_column. "
        "Sao 14 entidades, com SQLite em dev e PostgreSQL em producao - trocamos "
        "so pela variavel de ambiente.",
        [
            "Diagrama do modelo: User-RoleUser-Role (papeis multi-empresa), "
            "Business, LocalTrabalho, Jornada, EscalaFuncionario, Registro, "
            "Retificacao, BancoHoras, AuditLog, NsrSequencia.",
            "models/registro.py: TipoRegistro como Enum, timestamp_utc sempre em "
            "UTC, geolocalizacao Numeric(10,7), suspeito_geo.",
            "Cadeia de hash: hash_registro + hash_anterior (integridade "
            "anti-fraude); UniqueConstraint(empresa_id, nsr).",
            "relationship com foreign_keys explicito (3 FKs para users).",
            "Migrations com Flask-Migrate/Alembic - o schema e versionado, nao "
            "criado na mao.",
        ],
        impacto="O hash em cadeia significa que alterar uma batida antiga "
                "exigiria refazer todos os hashes seguintes - e a exigencia "
                "anti-adulteracao do REP-P, implementada de verdade.",
    )
    story.append(Paragraph(
        "<b>Demo sugerida (fluxo completo, views/ponto.py):</b> bater um ponto "
        "-> gera NSR atomico -> calcula hash -> checa geofence -> salva -> "
        "registra no AuditLog -> redireciona pro comprovante (PDF via ReportLab).",
        s["body"]
    ))

    story.append(PageBreak())

    # ============ PARTE 3 ============
    story.append(Paragraph(
        "Parte 3 - Interface, Testes e Qualidade (Rychard Chaves)", s["h1"]))

    criterio(
        story, s, 4, "Interface e Templates / Frontend",
        "Rychard Chaves", "templates/",
        "O frontend usa Jinja2 + Bootstrap 5, com heranca de templates. Tudo "
        "herda de templates/base.html, entao navbar, mensagens flash e "
        "responsividade sao centralizados.",
        [
            "Organizacao de templates/ por dominio: auth/, ponto/, rh/, admin/, "
            "funcionario/, errors/, emails/.",
            "base.html e como as telas estendem dele.",
            "Filtros customizados de fuso: {{ dt|localdt('%H:%M') }} (UTC -> "
            "horario local).",
            "Templates de e-mail (emails/retificacao_decidida) em HTML + texto.",
            "Paginas de erro proprias (403/404/500) que mantem o visual do "
            "sistema.",
        ],
        impacto="O funcionario bate ponto pelo celular - por isso a "
                "responsividade e testada, nao so assumida.",
    )

    criterio(
        story, s, 5, "Testes Automatizados",
        "Rychard Chaves", "tests/, tests/conftest.py",
        "Temos 76 testes automatizados com pytest, organizados por area. Nao e "
        "so 'a home abre' - testamos calculos de horas, seguranca e regras de "
        "negocio.",
        [
            "Suite: test_unitarios (19), test_invasao (11), test_acesso (7), "
            "test_auth (6), test_ponto/test_calculos (8) e outros - 76 no total.",
            "conftest.py: fixture app com SQLite em memoria (StaticPool); "
            "fixture org cria empresa completa (papeis, usuarios, jornada, "
            "local com geofence); fixtures login e criar_registro.",
            "TZ='UTC' fixo no topo -> calculos de hora deterministicos no CI.",
            "Rodar e simples: inv test.",
        ],
        impacto="Os testes de invasao verificam que um funcionario nao acessa o "
                "comprovante de outro - retorna 403.",
    )
    story.append(Paragraph(
        "<b>Demo sugerida:</b> rodar <b>inv test</b> ao vivo e mostrar os 76 "
        "testes passando em verde.",
        s["body"]
    ))

    criterio(
        story, s, 7, "Qualidade de Codigo, Organizacao e Boas Praticas",
        "Rychard Chaves", "pyproject.toml, .env.*, E_Ponto/utils/",
        "Fechando: o projeto segue boas praticas de engenharia de ponta a ponta.",
        [
            ".env por ambiente (dev/test/prod) + .example versionados, sem "
            "segredos: SECRET_KEY, banco e e-mail nunca ficam no codigo.",
            "pyproject.toml (PEP 621): dependencias separadas em dependencies, "
            "dev (black, flake8) e test (pytest, pytest-cov).",
            "Automacao com Invoke: inv run, inv test, inv lint, inv format, "
            "inv zip.",
            "Tratamento de erros: handlers 403/404/500 + db.session.rollback() "
            "no 500. Logging via app.logger.",
            "Seguranca: Bcrypt, 2FA (pyotp/qrcode), rate limiting, CSRF, "
            "AuditLog de acoes sensiveis.",
            "utils/ isola regras de negocio (clt, banco_horas, geo, nsr, "
            "hashing, afd/aej, pdf, excel) - views finas, logica testavel.",
            "Versionamento Git + .gitignore (venv, __pycache__, .db fora do "
            "repo). Ha um docs/RELATORIO_SEGURANCA.md.",
        ],
        impacto="Cada decisao tem um porque documentado em comentario - o "
                "codigo foi escrito para ser lido e mantido.",
    )

    story.append(PageBreak())

    # ============ ENCERRAMENTO ============
    story.append(Paragraph("Encerramento (~30s) - Roberto Dias", s["h1"]))
    story.append(Paragraph(
        "&ldquo;Em resumo: o E-Ponto e um sistema Flask com arquitetura de "
        "fabrica, 6 Blueprints, validacao no servidor, 14 entidades com ORM e "
        "migrations, 76 testes automatizados, interface responsiva e "
        "conformidade legal REP-P. Tudo isso esta no .zip entregue e detalhado no "
        "PDF de documentacao. Obrigado - abrimos para perguntas.&rdquo;",
        s["fala"]
    ))

    # ============ CHECKLIST DA ENTREGA ============
    story.append(Paragraph("Checklist da entrega obrigatoria", s["h1"]))
    story.extend(bullets([
        ".zip nomeado GrupoX_E-Ponto.zip (sem venv/ e __pycache__/).",
        "PDF de documentacao com: titulo + integrantes; descricao e "
        "funcionalidades; diagrama ER; trechos tecnicos comentados; explicacao "
        "da arquitetura (App Factory); tecnologias + justificativa; passo a "
        "passo de execucao; principais desafios.",
        "Desafios para citar: hash em cadeia, fuso horario UTC, geofencing, NSR "
        "atomico.",
        "Dica: ja existem analise_eponto.pdf e resumo_eponto.pdf na raiz - "
        "podem servir de base para o PDF de documentacao.",
    ], s["bullet"]))

    return story


def main():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Roteiro de Apresentacao E-Ponto",
        author="UVV - Programacao Avancada para Web",
    )
    styles = build_styles()
    story = build_story(styles)
    doc.build(story)
    print(f"[OK] PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
