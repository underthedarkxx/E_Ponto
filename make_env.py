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

    print("🚀 Instalando Invoke e dotenv (pré-requisitos do `inv install`)...")
    # check=True aqui sim: se estes não instalarem, é erro real.
    # O `dotenv` é obrigatório porque o tasks.py faz `from dotenv import
    # load_dotenv` no topo — ou seja, o `invoke` importa o dotenv ao carregar
    # as tarefas. Sem ele, o PRÓPRIO `inv install` quebra na importação antes
    # de instalar as dependências do projeto. Por isso a ordem é:
    #   1) make_env.py  -> deixa invoke + dotenv prontos
    #   2) inv install  -> instala o resto (Flask, SQLAlchemy, etc. do pyproject)
    subprocess.run([str(python), "-m", "pip", "install", "invoke", "dotenv"], check=True)

    # 4.5) Garante que existam os arquivos .env.{dev,test,prod}.
    #      Os .env.* reais são ignorados pelo Git (.gitignore), então quem
    #      baixa o projeto pelo GitHub/ZIP NÃO os recebe — só os *.example.
    #      Sem .env.dev a app sobe sem SECRET_KEY e quebra ("no secret key
    #      was set"); sem .env.test / .env.prod, o `inv test` e o `inv prod`
    #      quebram com FileNotFoundError ao carregar o ambiente.
    #      Mapa: arquivo final -> arquivo de exemplo de origem.
    env_pairs = {
        ".env.dev": ".env.example",
        ".env.test": ".env.test.example",
        ".env.prod": ".env.prod.example",
    }
    for destino, exemplo in env_pairs.items():
        destino_p = Path(destino)
        exemplo_p = Path(exemplo)
        if not destino_p.exists() and exemplo_p.exists():
            shutil.copy(exemplo_p, destino_p)
            print(f"📝 Criei {destino} a partir de {exemplo} (ajuste se precisar).")

    # 5) Mostra como ativar a venv, com o comando certo para cada OS.
    if os.name == "nt":
        ativar = r"venv\Scripts\activate"
    else:
        ativar = "source venv/bin/activate"

    print("✅ Ambiente recriado com invoke + dotenv prontos!")
    print(f"👉 1) Ative a venv:        {ativar}")
    print("👉 2) Instale o projeto:   inv install")
    print("👉 3) Rode a aplicação:    inv run")


if __name__ == "__main__":
    # sys.exit propaga o código de erro de um subprocess que falhou.
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"❌ Falhou um comando do pip (código {e.returncode}).")
        sys.exit(e.returncode)
