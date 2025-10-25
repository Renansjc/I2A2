#!/usr/bin/env python3
"""
Script de configuração para o Agente EDA
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"{description} - Sucesso!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description} - Erro!")
        print(f"Erro: {e.stderr}")
        return False

def main():
    print("Configurando ambiente para o Agente EDA")
    print("=" * 50)
    
    # Verificar se Python está instalado
    if not run_command("python --version", "Verificando Python"):
        print("Python nao encontrado. Instale Python primeiro!")
        return
    
    # Criar ambiente virtual
    if not run_command("python -m venv venv", "Criando ambiente virtual"):
        return
    
    # Ativar ambiente virtual (Windows)
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
    else:  # Linux/Mac
        activate_cmd = "source venv/bin/activate"
    
    print(f"\nPara ativar o ambiente virtual, execute:")
    print(f"   {activate_cmd}")
    
    # Instalar dependências
    pip_cmd = "venv\\Scripts\\pip" if os.name == 'nt' else "venv/bin/pip"
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Instalando dependências"):
        return
    
    print("\nConfiguracao concluida!")
    print("\nProximos passos:")
    print("1. Ative o ambiente virtual:")
    print(f"   {activate_cmd}")
    print("2. Configure sua chave da OpenAI no arquivo 'config.env'")
    print("3. Execute o app:")
    print("   streamlit run app.py")

if __name__ == "__main__":
    main()
