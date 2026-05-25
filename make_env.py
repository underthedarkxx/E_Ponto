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

    # 3) Descobre o caminho do PYTHON DENTRO da venv. O layout muda por OS:
    #    - Windows: venv\Scripts\python.exe
    #    - Linux/Mac: venv/bin/python
    #    Usamos o python da venv (e não o pip.exe) por dois motivos:
    #      a) garante que os pacotes vão pra venv, não pro Python global;
    #      b) `python -m pip` é a única forma de ATUALIZAR o próprio pip
    #         no Windows — chamar `pip.exe install --upgrade pip` falha
    #         porque o pip.exe fica travado enquanto roda e não pode se
    #         sobrescrever. (`source .../activate` não é necessário:
    #         ativar a venv só afeta o shell; chamar pelo caminho basta.)
    if os.name == "nt":  # 'nt' == Windows
        python = VENV / "Scripts" / "python.exe"
    else:
        python = VENV / "bin" / "python"

    # 4) Atualiza o pip e instala os pacotes básicos.
    print("📦 Atualizando o pip...")
    # NÃO usamos check=True aqui de propósito: em várias máquinas Windows o
    # pip se recusa a se auto-atualizar (ele fica "travado" enquanto roda e
    # responde com "To modify pip, please run ... -m pip install --upgrade
    # pip"). Isso NÃO é fatal — o pip que veio com a venv já funciona. Antes,
    # com check=True, essa falha abortava o script e o `invoke` nunca era
    # instalado, por isso o `inv` ficava "não reconhecido" logo depois.
    upgrade = subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    if upgrade.returncode != 0:
        print("⚠️  Não consegui atualizar o pip — seguindo com a versão atual (ok).")

    print("🚀 Instalando Flask, Seaborn, Invoke e dependências...")
    # check=True aqui sim: se os pacotes básicos não instalarem, é erro real.
    subprocess.run([str(python), "-m", "pip", "install", "flask", "seaborn", "invoke"], check=True)

    # 4.5) Garante que exista um .env.dev.
    #      Os arquivos .env.* são ignorados pelo Git (.gitignore), então quem
    #      baixa o projeto pelo GitHub/ZIP NÃO recebe o .env.dev — e sem ele a
    #      app sobe sem SECRET_KEY e quebra com "no secret key was set".
    env_dev = Path(".env.dev")
    env_example = Path(".env.example")
    if not env_dev.exists() and env_example.exists():
        shutil.copy(env_example, env_dev)
        print("📝 Criei .env.dev a partir de .env.example (ajuste se precisar).")

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
