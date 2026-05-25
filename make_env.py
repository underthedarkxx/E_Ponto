# =====================================================================
# make_env.py — Recria o ambiente virtual do zero (multiplataforma)
# ---------------------------------------------------------------------
# Script utilitário (não é parte da app Flask). Apaga a pasta `venv/`
# atual, cria uma nova e instala alguns pacotes básicos.
#
# Útil quando o ambiente "quebrou" (dependências confusas, pip
# corrompido, etc.). NÃO instala as deps do projeto inteiro — para
# isso use `inv install` depois.
#
# Esta versão usa só Python (módulos `venv` e `subprocess`), sem
# depender de `bash`. Por isso funciona igual em Windows, Linux e Mac.
# =====================================================================

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

# Pasta da venv, relativa ao diretório onde o script é executado.
VENV = Path("venv")


def main():
    # 1) Apaga a venv antiga, se existir.
    #    shutil.rmtree é o equivalente multiplataforma de `rm -rf`.
    if VENV.exists():
        print("🗑️  Apagando o ambiente virtual antigo...")
        shutil.rmtree(VENV)

    # 2) Cria a nova venv já com pip instalado dentro dela.
    #    venv.create substitui `python3 -m venv venv` sem depender de
    #    qual é o nome do executável do Python no sistema.
    print("🌱 Criando um novo ambiente virtual do zero...")
    venv.create(VENV, with_pip=True)

    # 3) Descobre o caminho do pip DENTRO da venv. O layout muda por OS:
    #    - Windows: venv\Scripts\pip.exe
    #    - Linux/Mac: venv/bin/pip
    #    Usar o pip da venv garante que os pacotes vão pra venv, e não
    #    pro Python global. (Não usamos `source .../activate`: ativar a
    #    venv só afeta o shell; chamar o pip pelo caminho tem o mesmo
    #    efeito e funciona em qualquer sistema.)
    if os.name == "nt":  # 'nt' == Windows
        pip = VENV / "Scripts" / "pip.exe"
    else:
        pip = VENV / "bin" / "pip"

    # 4) Atualiza o pip e instala os pacotes básicos.
    #    check=True faz o script parar com erro se algum comando falhar.
    print("📦 Atualizando o pip...")
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)

    print("🚀 Instalando Flask, Seaborn, Invoke e dependências...")
    subprocess.run([str(pip), "install", "flask", "seaborn", "invoke"], check=True)

    # 5) Mostra como ativar a venv, com o comando certo para cada OS.
    if os.name == "nt":
        ativar = r"venv\Scripts\activate"
    else:
        ativar = "source venv/bin/activate"

    print("✅ Ambiente recriado e pacotes instalados com sucesso!")
    print(f"👉 Para usar a venv no terminal, rode: {ativar}")


if __name__ == "__main__":
    # sys.exit propaga o código de erro de um subprocess que falhou.
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"❌ Falhou um comando do pip (código {e.returncode}).")
        sys.exit(e.returncode)
