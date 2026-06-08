"""Pacote raiz do projeto.

Re-exporta create_app (definida em app.py) para permitir
`from E_Ponto import create_app`. Usa import_module para evitar conflito
de nomes com o modulo `app`.
"""

from importlib import import_module

create_app = import_module("app").create_app
