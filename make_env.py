# =====================================================================
# make_env.py — Recria o ambiente virtual do zero
# ---------------------------------------------------------------------
# Script utilitário (não é parte da app Flask). Apaga a pasta `venv/`
# atual, cria uma nova, ativa e instala alguns pacotes básicos.
#
# Útil quando o ambiente "quebrou" (dependências confusas, pip
# corrompido, etc.). NÃO instala as deps do projeto inteiro — para
# isso use `inv install` depois.
# =====================================================================

import os

# Script bash que será escrito num arquivo temporário e executado.
# Mantemos o script aqui dentro como string para deixar o `make_env.py`
# autocontido (não depende de um .sh externo).
bash_script = '''#!/bin/bash

echo "🗑️ Apagando o ambiente virtual antigo..."
rm -rf venv

echo "🌱 Criando um novo ambiente virtual do zero..."
python3 -m venv venv

echo "🔄 Ativando o ambiente..."
# Obs.: este `source` afeta apenas o subshell do bash; o Python que
# chamou este script não fica com a venv ativada. Para usar a venv no
# terminal depois, rode você mesmo: `source venv/bin/activate`.
source venv/bin/activate

echo "📦 Atualizando o pip..."
python3 -m pip install --upgrade pip

echo "🚀 Instalando Flask, Seaborn, Invoke e dependências..."
pip install flask seaborn invoke

echo "✅ Ambiente recriado e pacotes instalados com sucesso!"
'''

# Salva o script em um arquivo temporário.
with open("temp_script.sh", "w") as f:
    f.write(bash_script)

# Executa o script usando o bash. os.system bloqueia até o bash
# terminar — uma alternativa mais segura seria `subprocess.run`.
os.system("bash temp_script.sh")

# Remove o script temporário para não deixar lixo na pasta.
os.remove("temp_script.sh")
