# =====================================================================
# gerar_documentacao_pdf.py — Gera "documentacao_eponto.pdf"
# ---------------------------------------------------------------------
# Documento tecnico OBRIGATORIO da entrega (auditoria dos 7 criterios).
# Contem: titulo + integrantes, descricao/funcionalidades, diagrama do
# banco (ER textual + tabela de entidades), detalhamento tecnico com
# trechos de codigo reais, explicacao da arquitetura, tecnologias +
# justificativa, passo a passo de execucao e principais desafios.
#
# Script independente da aplicacao (so usa ReportLab). Reaproveita a
# identidade visual de gerar_resumo_pdf.py.
# Uso:
#     cd E_Ponto
#     source venv/bin/activate
#     python gerar_documentacao_pdf.py
# Saida: documentacao_eponto.pdf na raiz do projeto.
# =====================================================================

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


OUTPUT = "documentacao_eponto.pdf"


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=24,
            textColor=colors.HexColor("#0d3b66"), spaceAfter=4, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=11,
            textColor=colors.HexColor("#555555"), spaceAfter=14, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontSize=15,
            textColor=colors.HexColor("#0d3b66"), spaceBefore=14, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=12,
            textColor=colors.HexColor("#1d4e89"), spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=10, leading=14,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"], fontSize=10, leading=14,
            leftIndent=14, bulletIndent=2, spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code", parent=base["Code"], fontSize=8.2, leading=11,
            textColor=colors.HexColor("#1b1f23"),
            backColor=colors.HexColor("#f4f6f8"),
            borderColor=colors.HexColor("#d0d7de"), borderWidth=0.5,
            borderPadding=6, leftIndent=2, rightIndent=2, spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"], fontSize=8.5, leading=11,
            textColor=colors.HexColor("#666666"), alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "capa_meta": ParagraphStyle(
            "capa_meta", parent=base["Normal"], fontSize=11, leading=18,
            textColor=colors.HexColor("#333333"), spaceAfter=2,
        ),
    }


def make_table(data, col_widths, header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd8dc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
    return [Paragraph(f"&bull;&nbsp; {item}", style) for item in items]


def code(raw, style):
    """Transforma um bloco de codigo cru num Paragraph monoespacado.

    Escapa &, <, > (senao o ReportLab interpreta como markup), preserva
    indentacao com &nbsp; e quebra de linha com <br/>.
    """
    out_lines = []
    for line in raw.strip("\n").splitlines():
        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Preserva espacos a esquerda (indentacao).
        stripped = line.lstrip(" ")
        n_spaces = len(line) - len(stripped)
        line = ("&nbsp;" * n_spaces) + stripped
        out_lines.append(line)
    return Paragraph("<br/>".join(out_lines), style)


def build_story(s):
    story = []

    # ===================== CAPA =====================
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("E-Ponto", s["title"]))
    story.append(Paragraph(
        "Sistema Web de Registro Eletronico de Ponto (REP-P)", s["subtitle"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Documentacao Tecnica do Projeto", s["h1"]))
    story.append(Paragraph(
        "Conformidade com a Portaria MTP n. 671/2021", s["body"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("<b>Disciplina:</b> Programacao Avancada para Web",
                           s["capa_meta"]))
    story.append(Paragraph("<b>Instituicao:</b> Universidade Vila Velha (UVV) - 5o periodo",
                           s["capa_meta"]))
    story.append(Paragraph("<b>Produto:</b> E-Ponto", s["capa_meta"]))
    story.append(Paragraph("<b>Grupo:</b> Grupo 5", s["capa_meta"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("<b>Integrantes do grupo:</b>", s["capa_meta"]))
    story.extend(bullets([
        "Roberto Dias Furtado de Araujo - 202421518",
        "Rychard Chaves Brandao - 202417506",
        "Lucas Andre - 202422326",
    ], s["bullet"]))
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph(
        "Stack principal: Python 3.12 + Flask (Application Factory) + "
        "SQLAlchemy 2.x + Flask-Migrate + Flask-Login + Flask-WTF + "
        "Bootstrap 5 / Jinja2.",
        s["body"]
    ))

    story.append(PageBreak())

    # ===================== 1. DESCRICAO =====================
    story.append(Paragraph("1. Descricao geral do produto", s["h1"]))
    story.append(Paragraph(
        "O <b>E-Ponto</b> e uma plataforma web para registro eletronico de "
        "ponto, voltada a empresas de pequeno e medio porte (ate ~200 "
        "funcionarios). Diferente de um cadastro comum, ele implementa as "
        "exigencias legais brasileiras de um <b>REP-P</b> (Registro Eletronico "
        "de Ponto via Programa), descritas na Portaria MTP n. 671/2021: "
        "Numero Sequencial de Registro (NSR), cadeia de hashes para "
        "inviolabilidade e geracao dos arquivos oficiais AFD e AEJ. O sistema e "
        "<b>multi-empresa</b> (multi-tenant): um mesmo usuario pode ter papeis "
        "diferentes em empresas diferentes.",
        s["body"]
    ))

    story.append(Paragraph("Funcionalidades principais", s["h2"]))
    story.extend(bullets([
        "Autenticacao por e-mail e senha (hash Bcrypt) com <b>2FA opcional</b> "
        "(TOTP via pyotp + QR Code).",
        "Controle de acesso por papeis (RBAC): super_admin, admin, rh, "
        "funcionario - com escopo por empresa.",
        "Registro de ponto com 4 batidas (Entrada, Saida Almoco, Retorno "
        "Almoco, Saida Final), data/hora em UTC e <b>geolocalizacao</b>.",
        "<b>Geofencing</b>: cada batida e comparada ao raio do local de "
        "trabalho; fora do raio fica marcada como suspeita para revisao do RH.",
        "Comprovante de cada batida em tela e em <b>PDF</b> (ReportLab).",
        "Dashboard do funcionario: saldo de horas, banco de horas, atrasos, "
        "faltas e calendario do mes.",
        "Gestao de RH: listagem/filtros de registros, aprovacao de "
        "<b>retificacoes</b> (sem sobrescrever o historico) e relatorios.",
        "Exportacao de relatorios em <b>Excel (.xlsx)</b> (Pandas + openpyxl) e "
        "geracao dos arquivos legais <b>AFD</b> e <b>AEJ</b>.",
        "Trilha de <b>auditoria</b> (audit_logs) das acoes sensiveis e rate "
        "limiting nas rotas de login.",
    ], s["bullet"]))

    # ===================== 2. DIAGRAMA DO BANCO =====================
    story.append(Paragraph("2. Diagrama do banco de dados (modelo ER)", s["h1"]))
    story.append(Paragraph(
        "O schema possui <b>15 tabelas</b> (modeladas com SQLAlchemy 2.x e "
        "versionadas via Alembic/Flask-Migrate). O diagrama textual abaixo "
        "resume os relacionamentos centrais; a tabela seguinte lista todas as "
        "entidades.",
        s["body"]
    ))
    story.append(code(
        """
users 1---* roles_has_users *---1 roles        (RBAC: papel por empresa)
                  |  *                          business_id, level_id (opc.)
                  v  1
              businesses 1---* jornadas
                  |  1     1---* locais_trabalho
                  |  *
            escalas_funcionarios   (vincula user + jornada + local)
                  |
                  v
businesses 1---* registros *---1 users          (a batida de ponto)
              |        |  *---? locais_trabalho
              |        +---* retificacoes *---1 users (solicitante/aprovador)
              |
              +---1 nsr_sequencias               (contador NSR da empresa)
              +---* banco_horas *---1 users      (saldo mensal)
              +---* audit_logs                   (trilha de auditoria)

users 1---* address *---? cities                (endereco do funcionario)
""",
        s["code"]
    ))
    story.append(Paragraph(
        "Legenda: 1---* (um para muitos), *---1 (muitos para um), ? (opcional / "
        "FK anulavel).",
        s["caption"]
    ))

    tabelas = [
        ["Tabela", "Descricao", "Chaves / FKs principais"],
        ["users", "Usuario (CPF, PIS/NIS, senha bcrypt, totp_secret, cargo, "
         "data_admissao)", "PK id; email unico"],
        ["roles", "Papeis: super_admin, admin, rh, funcionario", "PK id; name unico"],
        ["levels", "Niveis organizacionais opcionais", "PK id"],
        ["roles_has_users", "Associativa RBAC (user x role x empresa)",
         "FK user_id, role_id, business_id, level_id; UQ(user,role,business)"],
        ["businesses", "Empresa empregadora (CNPJ, CEI/CAEPF, endereco REP-P)",
         "PK id; FK owner_user_id; cnpj unico"],
        ["address / cities", "Endereco do funcionario e cidades",
         "FK user_id, city_id"],
        ["locais_trabalho", "Locais fisicos com lat/lon + raio (geofence)",
         "PK id; FK empresa_id"],
        ["jornadas", "Jornada de trabalho (padrao, 12x36, 6x1, flexivel)",
         "PK id; FK empresa_id"],
        ["escalas_funcionarios", "Vinculo funcionario-jornada-local com datas",
         "FK user_id, empresa_id, jornada_id, local_trabalho_id"],
        ["registros", "Batida de ponto (nucleo do sistema)",
         "PK id; FK empresa_id, user_id, local_trabalho_id; UQ(empresa,nsr)"],
        ["nsr_sequencias", "Contador sequencial de NSR por empresa",
         "PK empresa_id"],
        ["retificacoes", "Pedido de correcao (PENDENTE/APROVADA/REJEITADA)",
         "FK registro_id, empresa_id, solicitante_id, aprovador_id"],
        ["banco_horas", "Saldo mensal (positivos/negativos/saldo)",
         "FK user_id, empresa_id; UQ(user,empresa,periodo)"],
        ["audit_logs", "Trilha de auditoria (dados_antes/dados_depois)",
         "FK empresa_id, user_id"],
    ]
    story.append(make_table(tabelas, [3.2 * cm, 7.3 * cm, 6.0 * cm]))

    story.append(PageBreak())

    # ===================== 3. ARQUITETURA =====================
    story.append(Paragraph("3. Arquitetura adotada", s["h1"]))
    story.append(Paragraph(
        "A aplicacao segue o padrao <b>Application Factory</b> do Flask: nao "
        "existe um objeto global de app, e sim a funcao <b>create_app()</b> que "
        "monta a instancia sob demanda. Isso evita imports circulares e permite "
        "criar uma instancia de teste isolada (banco em memoria) separada da de "
        "producao. Cada extensao expoe a mesma convencao <b>init_app(app)</b>.",
        s["body"]
    ))
    story.append(code(
        """
def create_app(test_config=None):
    app = Flask(__name__)
    init_config(app)                 # 1) le .env -> app.config
    if test_config:
        app.config.update(test_config)
    init_db(app); register_models()  # 2) SQLAlchemy + carrega 15 models
    init_auth(app)                   # 3) Flask-Login
    init_migrate(app)                # 4) Flask-Migrate / Alembic
    init_mail(app)                   # 4.5) Flask-Mail
    if not app.config.get("TESTING"):
        init_wtf(app)                # 5) CSRF (off em testes)
        init_limiter(app)            #    Rate limiting (off em testes)
    init_toolbar(app)                # 6) Debug Toolbar (dev)
    init_site(app)                   # 7) Registra os 6 blueprints
    return app
""",
        s["code"]
    ))
    story.append(Paragraph("app.py - funcao create_app() (resumida)", s["caption"]))
    story.append(Paragraph(
        "A organizacao em camadas separa responsabilidades de forma clara:",
        s["body"]
    ))
    story.append(code(
        """
E_Ponto/
  app.py            # factory create_app()
  tasks.py          # comandos Invoke (run/test/seed/migrate/zip)
  pyproject.toml    # dependencias (PEP 621)
  .env.{dev,test,prod}
  E_Ponto/
    ext/            # config, db, auth, wtf, limiter, migrate, mail, debugtoolbar
    models/         # 15 modelos SQLAlchemy
    views/          # 6 blueprints (auth, main, ponto, admin, rh, funcionario)
    forms/          # WTForms (validacao no servidor)
    utils/          # nsr, hashing, geo, clt, afd, aej, pdf, excel, decorators
  templates/        # Jinja2 + Bootstrap 5
  tests/            # 122 testes (pytest)
  migrations/       # versoes Alembic
""",
        s["code"]
    ))
    story.append(Paragraph(
        "A camada de rotas e dividida em <b>6 Blueprints</b>, um por dominio: "
        "<b>auth</b> (/auth - login, 2FA), <b>main</b> (/ - home e selecao de "
        "empresa), <b>ponto</b> (/ponto - bater, historico, comprovante), "
        "<b>funcionario</b> (/funcionario - dashboard), <b>rh</b> (/rh - "
        "registros, retificacoes, relatorios) e <b>admin</b> (/admin - usuarios, "
        "jornadas, locais). As regras de negocio ficam isoladas em utils/, "
        "mantendo as views finas e testaveis.",
        s["body"]
    ))

    story.append(PageBreak())

    # ===================== 4. DETALHAMENTO TECNICO =====================
    story.append(Paragraph(
        "4. Detalhamento tecnico das principais partes", s["h1"]))

    # 4.1 Models
    story.append(Paragraph("4.1 Modelagem (SQLAlchemy 2.x)", s["h2"]))
    story.append(Paragraph(
        "Os modelos usam o estilo moderno Mapped/mapped_column. A tabela "
        "<b>registros</b> e a mais rica: usa Enum (evita typos), guarda o "
        "timestamp sempre em UTC, geolocalizacao e os campos da cadeia de hash. "
        "Repare na UniqueConstraint que garante NSR unico por empresa.",
        s["body"]
    ))
    story.append(code(
        """
class TipoRegistro(enum.Enum):
    ENTRADA = "entrada"; SAIDA_ALMOCO = "saida_almoco"
    RETORNO_ALMOCO = "retorno_almoco"; SAIDA = "saida"
    INCLUSAO = "inclusao"; ALTERACAO = "alteracao"

class Registro(db.Model):
    __tablename__ = "registros"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nsr", name="uq_empresa_nsr"),
        {'extend_existing': True})
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    nsr: Mapped[int] = mapped_column(db.Integer, nullable=False)
    tipo: Mapped[TipoRegistro] = mapped_column(db.Enum(TipoRegistro))
    timestamp_utc: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    suspeito_geo: Mapped[bool] = mapped_column(db.Boolean, default=False)
    hash_registro: Mapped[str] = mapped_column(db.String(64), nullable=False)
    hash_anterior: Mapped[Optional[str]] = mapped_column(db.String(64))
""",
        s["code"]
    ))
    story.append(Paragraph("E_Ponto/models/registro.py (resumido)", s["caption"]))

    # 4.2 Formularios
    story.append(Paragraph("4.2 Formularios e validacao (Flask-WTF)", s["h2"]))
    story.append(Paragraph(
        "Toda entrada do usuario passa por validacao <b>no servidor</b>. O "
        "formulario de bater ponto recebe a geolocalizacao via campos ocultos "
        "(preenchidos por JavaScript) e a view so executa a logica apos "
        "form.validate_on_submit().",
        s["body"]
    ))
    story.append(code(
        """
class BaterPontoForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada'), ...])
    latitude = HiddenField('Latitude')   # preenchido por JS (Geolocation)
    longitude = HiddenField('Longitude')
    local_trabalho_id = SelectField('Local', coerce=int,
                                    validators=[Optional()])
    justificativa = TextAreaField('Justificativa',
                                  validators=[Optional(), Length(max=255)])
    submit = SubmitField('Registrar Ponto')
""",
        s["code"]
    ))
    story.append(Paragraph("E_Ponto/forms/ponto.py", s["caption"]))

    # 4.3 NSR + hash
    story.append(Paragraph(
        "4.3 Integridade: NSR atomico + cadeia de hash", s["h2"]))
    story.append(Paragraph(
        "Ao bater ponto, a view gera o proximo NSR de forma atomica (lock de "
        "linha) e calcula um SHA-256 encadeado ao hash do registro anterior. "
        "Assim, alterar uma batida antiga invalidaria todos os hashes "
        "seguintes - a exigencia anti-adulteracao do REP-P.",
        s["body"]
    ))
    story.append(code(
        """
def get_next_nsr(empresa_id: int) -> int:
    seq = (NsrSequencia.query.filter_by(empresa_id=empresa_id)
           .with_for_update().first())        # SELECT ... FOR UPDATE
    if seq is None:
        seq = NsrSequencia(empresa_id=empresa_id, ultimo_nsr=0)
        db.session.add(seq)
    seq.ultimo_nsr += 1
    db.session.flush()
    return seq.ultimo_nsr

def calcular_hash(nsr, cnpj, pis_cpf, timestamp_iso, tipo, hash_anterior):
    data = f"{nsr}|{cnpj}|{pis_cpf}|{timestamp_iso}|{tipo}|" \\
           f"{hash_anterior or 'GENESIS'}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
""",
        s["code"]
    ))
    story.append(Paragraph("E_Ponto/utils/nsr.py e utils/hashing.py", s["caption"]))

    # 4.4 Geofence
    story.append(Paragraph("4.4 Geofencing (formula de Haversine)", s["h2"]))
    story.append(code(
        """
def verificar_geofence(lat, lon, local_trabalho) -> tuple:
    if lat is None or lon is None or local_trabalho is None:
        return True, 0.0          # sem dados: nao da pra julgar
    dist = haversine(lat, lon, local_trabalho.latitude,
                     local_trabalho.longitude)
    return dist <= local_trabalho.raio_metros, dist
""",
        s["code"]
    ))
    story.append(Paragraph("E_Ponto/utils/geo.py", s["caption"]))

    # 4.5 Testes
    story.append(Paragraph("4.5 Testes automatizados (pytest)", s["h2"]))
    story.append(Paragraph(
        "Sao <b>122 testes</b> (76 funcoes, varias parametrizadas) cobrindo "
        "rotas, calculos, seguranca/autorizacao e regras de negocio. A fixture "
        "principal sobe a app em modo teste com "
        "<b>SQLite em memoria</b> isolado por teste, e o TZ e fixado em UTC para "
        "deixar os calculos de hora deterministicos no CI.",
        s["body"]
    ))
    story.append(code(
        """
@pytest.fixture
def app():
    app = create_app(test_config={
        "TESTING": True, "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",   # banco em memoria
        "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool, ...},
        "WTF_CSRF_ENABLED": False})
    ctx = app.app_context(); ctx.push()
    _db.create_all(); ctx.pop()
    yield app
    ... # drop_all no teardown
""",
        s["code"]
    ))
    testes = [
        ["Arquivo", "Foco", "Qtde"],
        ["test_acesso.py", "Controle de acesso por papel (parametrizado)", "53"],
        ["test_unitarios.py", "Funcoes puras (calculos, hash)", "19"],
        ["test_invasao.py", "Tentativas de invasao / autorizacao", "11"],
        ["test_ponto / test_calculos", "Fluxo de ponto e calculos de horas", "8"],
        ["test_auth.py", "Login e 2FA", "6"],
        ["demais (smoke, dashboard, rh, ...)", "Relatorios, retificacao, erros, etc.", "25"],
    ]
    story.append(make_table(testes, [5.5 * cm, 9.0 * cm, 2.0 * cm]))

    story.append(PageBreak())

    # ===================== 5. TECNOLOGIAS =====================
    story.append(Paragraph("5. Tecnologias utilizadas", s["h1"]))
    tech = [
        ["Tecnologia", "Para que serve"],
        ["Flask", "Microframework web; base da Application Factory e dos "
         "blueprints"],
        ["Flask-SQLAlchemy / SQLAlchemy 2.x", "ORM e modelagem das 15 entidades"],
        ["Flask-Migrate / Alembic", "Versionamento e migracao do schema"],
        ["Flask-Login", "Sessao de usuario, @login_required, current_user"],
        ["Flask-WTF / WTForms", "Formularios + validacao no servidor + CSRF"],
        ["Flask-Bcrypt", "Hash seguro de senhas"],
        ["pyotp + qrcode", "Autenticacao em 2 fatores (TOTP)"],
        ["Flask-Limiter", "Rate limiting nas rotas sensiveis (login)"],
        ["Flask-Mail", "Notificacao por e-mail (ex.: retificacao decidida)"],
        ["ReportLab", "Geracao de PDF (comprovante e esta documentacao)"],
        ["Pandas + openpyxl", "Exportacao de relatorios em Excel (.xlsx)"],
        ["Bootstrap 5 + Jinja2", "Interface responsiva e templates"],
        ["SQLite / PostgreSQL", "Banco em dev (SQLite) e producao (Postgres)"],
        ["pytest (+pytest-cov)", "Suite de testes automatizados"],
        ["Invoke", "Automacao de comandos (inv run/test/seed/...)"],
        ["black + flake8", "Formatacao e lint"],
    ]
    story.append(make_table(tech, [6.0 * cm, 10.5 * cm]))
    story.append(Paragraph(
        "<b>Justificativa:</b> o projeto usa <b>Flask</b> por ser o stack visto "
        "em aula e por casar bem com o padrao Application Factory + Blueprints. "
        "As bibliotecas do ecossistema (SQLAlchemy, WTF, Login, Migrate) sao "
        "maduras e integram-se nativamente, o que reduziu o codigo de "
        "infraestrutura e deixou o foco nas regras do REP-P. SQLite acelera o "
        "desenvolvimento e os testes; PostgreSQL entra em producao apenas "
        "trocando a variavel DATABASE_URL.",
        s["body"]
    ))

    # ===================== 6. COMO RODAR =====================
    story.append(Paragraph("6. Como rodar o projeto (passo a passo)", s["h1"]))
    story.append(code(
        """
# 1) Clonar e entrar na pasta
git clone https://github.com/underthedarkxx/E_Ponto.git
cd E_Ponto

# 2) Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate            # Windows: venv\\Scripts\\activate

# 3) Instalar dependencias (modo editavel + dev/test)
inv install                         # ou: pip install -e ".[dev,test]"

# 4) Configurar variaveis de ambiente
cp .env.example .env.dev
cp .env.example .env.test
python -c "import secrets; print(secrets.token_urlsafe(48))"  # SECRET_KEY

# 5) Criar o banco e popular dados iniciais
inv initdb                          # cria as tabelas
inv seed                            # papeis + super_admin + funcionario demo

# 6) Rodar o servidor de desenvolvimento
inv run                             # http://127.0.0.1:5000

# 7) Rodar os testes
inv test
""",
        s["code"]
    ))
    story.append(Paragraph(
        "Usuarios criados pelo <b>inv seed</b>: admin@eponto.com / admin123 "
        "(super_admin) e joao@eponto.com / joao123 (funcionario). Demais "
        "comandos uteis: <b>inv lint</b> (flake8), <b>inv format</b> (black), "
        "<b>inv migrate -m \"...\"</b> / <b>inv upgrade</b> (migracoes) e "
        "<b>inv zip</b> (empacota o projeto sem venv/cache).",
        s["body"]
    ))

    story.append(PageBreak())

    # ===================== 7. DESAFIOS =====================
    story.append(Paragraph(
        "7. Principais desafios e como foram resolvidos", s["h1"]))

    desafios = [
        ("Inviolabilidade dos registros (exigencia legal)",
         "O REP-P exige que registros nao possam ser adulterados. Resolvemos com "
         "uma cadeia de hashes SHA-256: cada batida inclui o hash da anterior, "
         "entao alterar uma antiga invalida todas as seguintes. Um utilitario "
         "(verificar_integridade) percorre a cadeia e aponta onde quebrou."),
        ("NSR unico sob concorrencia",
         "Duas batidas simultaneas poderiam receber o mesmo NSR. Usamos "
         "with_for_update() (SELECT ... FOR UPDATE) para travar a linha do "
         "contador ate o commit, garantindo numeros sequenciais sem colisao em "
         "Postgres; o controle e centralizado em get_next_nsr()."),
        ("Fuso horario e horario de verao",
         "Misturar fusos causava erros de calculo de atraso/horas. Padronizamos "
         "gravar tudo em UTC (timestamp_utc) e converter para o horario local "
         "apenas na exibicao, via filtros Jinja (localdt). Nos testes, o TZ e "
         "fixado em UTC para resultados deterministicos."),
        ("Validar localizacao do funcionario (geofence)",
         "Precisavamos saber se a batida ocorreu no local certo. Implementamos a "
         "formula de Haversine para medir a distancia entre o GPS do navegador e "
         "o local cadastrado; fora do raio, a batida e aceita mas marcada como "
         "suspeita para o RH revisar (em vez de bloquear)."),
        ("Testes isolados e rapidos",
         "Testes que compartilham banco geram falsos positivos. Cada teste sobe "
         "uma app propria com SQLite em memoria (StaticPool) criada e destruida "
         "na fixture, com CSRF e rate-limit desligados no modo TESTING."),
        ("Correcao de ponto sem apagar historico",
         "Corrigir um ponto nao pode sobrescrever o original (auditoria). "
         "Criamos a entidade Retificacao com fluxo de aprovacao do RH "
         "(PENDENTE/APROVADA/REJEITADA); a correcao gera novo registro do tipo "
         "ALTERACAO/INCLUSAO, preservando a trilha."),
    ]
    for titulo, texto in desafios:
        story.append(Paragraph(f"<b>{titulo}</b>", s["h2"]))
        story.append(Paragraph(texto, s["body"]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "Em sintese, o E-Ponto e um REP-P web multi-empresa em Flask que combina "
        "arquitetura modular (factory + blueprints), persistencia com ORM e "
        "migracoes, validacao no servidor, interface responsiva, 122 testes "
        "automatizados e conformidade legal - cobrindo os sete criterios "
        "tecnicos da avaliacao.",
        s["body"]
    ))

    return story


def main():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Documentacao Tecnica E-Ponto - Grupo 5",
        author="Roberto Dias Furtado de Araujo, Rychard Chaves Brandao, Lucas Andre - UVV",
    )
    s = build_styles()
    doc.build(build_story(s))
    print(f"[OK] PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
