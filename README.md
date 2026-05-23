# E-Ponto

Sistema web de **registro eletrônico de ponto** desenvolvido como projeto da
disciplina de Programação Avançada para Web (UVV — 5º período).

Construído com **Flask** seguindo o padrão *Application Factory*, com
SQLAlchemy 2.x, Flask-Login, Flask-Migrate, Flask-WTF e Flask-Limiter.

---

## Funcionalidades

- Cadastro de empresas, funcionários e RH
- Registro de pontos (entrada/saída)
- Geração de relatórios em PDF (AFD, AEJ — formatos da Portaria 671 do MTE)
- Cálculo de banco de horas e jornadas (CLT)
- Autenticação com 2FA (TOTP via `pyotp`)
- Controle de acesso baseado em papéis (super_admin, admin, rh, funcionario)
- Rate limiting nas rotas sensíveis (login)

---

## Pré-requisitos

- **Python 3.9+** (testado em 3.12)
- **pip** atualizado
- (Opcional) Git

---

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/underthedarkxx/E_Ponto.git
cd E_Ponto
```

### 2. Criar e ativar o ambiente virtual

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (cmd):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

> Se o PowerShell reclamar de permissão, rode antes:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 3. Instalar as dependências (modo editável + dev/test)

```bash
pip install -e ".[dev,test]"
```

Ou, usando o atalho do Invoke:

```bash
inv install
```

### 4. Configurar as variáveis de ambiente

Copie o template e preencha:

```bash
cp .env.example .env.dev
cp .env.example .env.test
cp .env.example .env.prod
```

Gere uma `SECRET_KEY` aleatória para cada ambiente:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> ⚠️ **Nunca** commite os arquivos `.env.*` reais — eles estão no `.gitignore`.

### 5. Criar o banco de dados e popular com dados iniciais

```bash
inv initdb     # cria as tabelas
inv seed       # cria papéis, super_admin e usuário de teste
```

Usuários criados pelo `inv seed`:

| Email | Senha | Papel |
|---|---|---|
| `admin@eponto.com` | `admin123` | super_admin |
| `joao@eponto.com` | `joao123` | funcionario |

---

## Executando

### Servidor de desenvolvimento

```bash
inv run
```

A aplicação fica disponível em `http://127.0.0.1:5000`.

### Modo produção (local)

```bash
inv prod
```

Em produção real, use um servidor WSGI como **gunicorn** ou **uWSGI** no
lugar do `flask run`.

### Testes

```bash
inv test
```

### Lint e formatação

```bash
inv lint      # flake8
inv format    # black
```

---

## Estrutura do projeto

```
E_Ponto/
├── app.py                  # Application factory (create_app)
├── tasks.py                # Comandos do Invoke (inv run, inv test, ...)
├── pyproject.toml          # Metadados e dependências do pacote
├── .env.example            # Template das variáveis de ambiente
│
├── E_Ponto/                # Pacote principal
│   ├── ext/                # Extensões Flask (db, auth, config, ...)
│   ├── models/             # Modelos SQLAlchemy
│   ├── views/              # Blueprints (rotas)
│   ├── forms/              # Formulários WTForms
│   └── utils/              # Helpers (PDF, CLT, geo, hashing, ...)
│
├── templates/              # Templates Jinja2
└── instance/               # Banco SQLite local (não versionado)
```

### Modelo de dados resumido

```
User ──< RoleUser >── Role
          │
       Business
          │
        Level
```

O `RoleUser` (`roles_has_users`) liga um usuário a um papel dentro
de uma empresa e nível organizacional.

---

## Comandos do Invoke

| Comando | O que faz |
|---|---|
| `inv install` | Instala o projeto em modo editável com deps de dev/test |
| `inv uninstall` | Remove o pacote |
| `inv run` | Sobe o servidor Flask de desenvolvimento |
| `inv prod` | Roda em modo produção |
| `inv test` | Executa a suíte de testes (pytest) |
| `inv initdb` | Cria todas as tabelas no banco |
| `inv seed` | Insere papéis, super_admin e funcionário demo |
| `inv lint` | Roda flake8 |
| `inv format` | Roda black |
| `inv zip` | Empacota o projeto em um zip (sem venv/cache) |

---

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `FLASK_APP` | Módulo da aplicação (sempre `app.py`) |
| `FLASK_ENV` | `development`, `testing` ou `production` |
| `FLASK_DEBUG` | `1` ativa o modo debug (apenas em dev) |
| `SECRET_KEY` | Chave usada por sessões e CSRF (mínimo 32 chars) |
| `DATABASE_URL` | URI do SQLAlchemy (ex.: `sqlite:///instance/eponto.db`) |
| `RATELIMIT_STORAGE_URI` | Backend do Flask-Limiter (`memory://` em dev) |
| `MAIL_*` | Configuração de e-mail (opcional) |

---

## Licença

Distribuído sob a licença **MIT**. Veja [LICENSE](LICENSE).

---

## Autor

**Wanderson Santana** — wanderson.santana@uvv.br
