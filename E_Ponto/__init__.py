# =====================================================================
# E_Ponto/__init__.py — Pacote raiz do projeto
# ---------------------------------------------------------------------
# Este arquivo torna o diretório `E_Ponto/` um pacote Python.
# Ele apenas re-exporta a função `create_app` definida em `app.py` (na
# raiz do projeto) para que outras partes do código possam importá-la
# como `from E_Ponto import create_app` ao invés de `from app import ...`.
#
# Usamos `import_module` em vez de `from app import create_app` para
# evitar conflito de nomes entre o módulo `app` (o arquivo) e variáveis
# locais chamadas `app` (a instância do Flask).
# =====================================================================

from importlib import import_module

# Importa o módulo `app.py` em runtime e pega a função create_app dele.
create_app = import_module("app").create_app
