# Relatório de Testes de Segurança — E-Ponto

**Projeto:** E-Ponto — Sistema de Controle de Ponto Digital (REP-P / Portaria MTP nº 671/2021)
**Disciplina:** Programação Avançada para Web — UVV
**Data:** 28/05/2026
**Tipo:** Avaliação de segurança autorizada do próprio sistema (caixa-branca)

---

## 1. Objetivo e escopo

Verificar, de forma automatizada, se o E-Ponto resiste às principais classes
de ataque a aplicações web e se os controles de segurança funcionam como
esperado. O escopo cobriu autenticação, autorização (controle de acesso),
validação de entrada, integridade dos registros de ponto e proteção contra
abuso das rotas.

Todos os testes são **automatizados** (pytest) e ficam em `tests/test_invasao.py`
(segurança) e `tests/test_unitarios.py` (integridade/lógica). Rodam com:

```bash
inv test
```

---

## 2. Metodologia

Abordagem **caixa-branca**: com acesso ao código-fonte, mapeamos os pontos
sensíveis (login, rotas protegidas, parâmetros de busca, geração de registros)
e escrevemos testes que simulam o comportamento de um atacante, comparando o
resultado obtido com o **comportamento seguro esperado**. Cada classe de
ataque virou um ou mais testes que falham se a proteção for removida.

Classes avaliadas (alinhadas ao OWASP Top 10): injeção (SQLi), Cross-Site
Scripting (XSS), quebra de controle de acesso (IDOR / escalada de privilégio /
navegação forçada), redirecionamento aberto (CWE-601), CSRF e integridade dos
dados.

---

## 3. Resumo executivo

| Severidade | Qtde |
|------------|------|
| 🔴 Alta | 0 (1 encontrada e **corrigida**) |
| 🟠 Média | 0 |
| 🟢 Baixa / informativa | 0 |

Foi encontrada **1 vulnerabilidade** (Open Redirect, severidade média) durante
os testes, **corrigida na mesma rodada**. Após a correção, todos os controles
de segurança passaram a ser validados automaticamente (122 testes no total,
sendo 11 de invasão e 19 unitários).

---

## 4. Vulnerabilidade encontrada e corrigida

### 4.1. Open Redirect no login (CWE-601) — Média

**Onde:** `E_Ponto/views/auth.py`, rota `/auth/login`, tratamento do
parâmetro `?next=`.

**Descrição:** após o login bem-sucedido, o sistema redirecionava o usuário
para o valor de `?next=` sem validar o destino. Um atacante poderia enviar um
link como `https://eponto/auth/login?next=https://site-falso.com`; a vítima
faria login no sistema real e, em seguida, seria levada a um site externo
controlado pelo atacante (vetor de **phishing**/roubo de credenciais).

**Código vulnerável (antes):**
```python
next_page = request.args.get('next')
return redirect(next_page or url_for('main.index'))
```

**Correção aplicada:** validação que só aceita caminhos **locais** (relativos
ao próprio site), recusando URLs absolutas (`https://...`) e protocol-relative
(`//...`):
```python
def _destino_seguro(destino):
    if not destino:
        return None
    if destino.startswith('//') or '\\' in destino:
        return None
    parsed = urlparse(destino)
    if parsed.scheme or parsed.netloc:   # tem http(s):// ou domínio → externo
        return None
    if not destino.startswith('/'):
        return None
    return destino
# ...
next_page = _destino_seguro(request.args.get('next'))
return redirect(next_page or url_for('main.index'))
```

**Testes que comprovam a correção** (`tests/test_invasao.py`):
`test_open_redirect_externo_bloqueado`,
`test_open_redirect_protocol_relative_bloqueado`,
`test_next_local_e_respeitado`.

---

## 5. Controles de segurança verificados (sem falhas)

| Ataque simulado | Resultado | Teste |
|-----------------|-----------|-------|
| **SQL Injection** no login (`' OR '1'='1`) | Não autentica, sem erro de SQL | `test_sql_injection_no_login_nao_autentica` |
| **SQL Injection** nos filtros do RH | Neutralizado pelo ORM (sem 500, tabela intacta) | `test_sql_injection_em_filtro_nao_quebra` |
| **XSS armazenado** (nome com `<script>`) | Escapado no HTML (autoescape Jinja) | `test_xss_no_nome_e_escapado` |
| **IDOR** — comprovante de outro usuário | Bloqueado (403) | `test_idor_comprovante_de_outro_usuario` |
| **IDOR** — retificar registro alheio | Bloqueado, nada criado | `test_idor_retificacao_de_registro_alheio` |
| **Escalada de privilégio** — funcionário cria admin | Bloqueado (403), usuário não criado | `test_escalada_funcionario_nao_cria_usuario` |
| **Navegação forçada** — anônimo bate ponto | Redirecionado ao login, nada criado | `test_navegacao_forcada_anonimo_nao_bate_ponto` |
| **CSRF** — POST sem token | Rejeitado (400) | `test_csrf_bloqueia_post_sem_token` |
| **Acesso por alteração de URL** (anônimo/funcionário/RH) | 302→login ou 403 conforme o papel | `tests/test_acesso.py` (51 casos) |
| **DoS no login** — senha > 72 bytes (limite bcrypt) | Tratado como inválida, sem 500 | `test_senha_gigante_nao_derruba_login` |

---

## 6. Integridade dos registros (REP-P)

A Portaria 671/2021 exige prova de que os registros de ponto não foram
adulterados. O sistema usa uma **cadeia de hashes SHA-256** (cada registro
inclui o hash do anterior). Os testes unitários comprovam:

- O hash é **determinístico** e muda se **qualquer** campo for alterado
  (`test_hash_muda_com_qualquer_campo`).
- A verificação de integridade **detecta adulteração**: alterar o horário de
  um registro sem refazer o hash quebra a cadeia e é apontado
  (`test_integridade_detecta_adulteracao`).

Complementarmente, o **NSR** (Número Sequencial de Registro) é único por
empresa (restrição no banco) e a geolocalização suspeita é apenas sinalizada
— a batida nunca é bloqueada, conforme a legislação trabalhista.

---

## 7. Defesas já presentes no sistema

- **Senhas com hash bcrypt** (`flask-bcrypt`) — nunca armazenadas em texto puro.
- **Controle de acesso por papel** (`@role_required`) em todas as rotas de
  admin/RH; verificação de propriedade do recurso por empresa.
- **Proteção CSRF** global (`Flask-WTF CSRFProtect`) em produção.
- **Rate limiting** (`Flask-Limiter`) nas rotas sensíveis.
- **2FA opcional** (TOTP) no login.
- **Comparação de senha em tempo constante** (bcrypt) contra *timing attacks*.
- **Mensagem de login genérica** ("E-mail ou senha inválidos") — não revela se
  o e-mail existe.
- **Armazenamento de timestamps em UTC** e **IP de origem** de cada batida
  para auditoria.

---

## 8. Cobertura de testes

Total da suíte: **122 testes automatizados**, dos quais:

- **11** testes de invasão/segurança (`tests/test_invasao.py`);
- **19** testes unitários de lógica/integridade (`tests/test_unitarios.py`);
- demais: controle de acesso, autenticação, ponto, cálculos, relatórios,
  retificação, dashboards, páginas de erro e responsividade.

---

## 9. Conclusão

O E-Ponto demonstrou-se **resiliente** às principais classes de ataque a
aplicações web. A única vulnerabilidade encontrada (Open Redirect) foi
**corrigida e coberta por testes de regressão**. Os controles de autenticação,
autorização, validação de entrada e integridade dos registros funcionam como
esperado e estão protegidos por testes automatizados, que impedem regressões
futuras.
