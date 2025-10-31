#!/usr/bin/env python3
"""
ROBO DOWNLOAD NEO - Wrapper de Configuração
Gerencia arquivo .env automaticamente
Executado automaticamente pelo .exe empacotado
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def setup_env():
    """Configura variáveis de ambiente automaticamente"""
    
    # Caminho do diretório onde o .exe está rodando
    base_dir = Path(sys.argv[0]).parent if hasattr(sys, 'frozen') else Path(__file__).parent.parent
    
    env_file = base_dir / '.env'
    env_template = base_dir / '.env.template'
    
    # Se .env não existe
    if not env_file.exists():
        # Se template existe, copiar para .env
        if env_template.exists():
            print("Arquivo .env não encontrado!")
            print(f"Criando a partir do template: {env_template}")
            
            with open(env_template, 'r', encoding='utf-8') as f_template:
                content = f_template.read()
            
            with open(env_file, 'w', encoding='utf-8') as f_env:
                f_env.write(content)
            
            print(f"✓ Arquivo .env criado em: {env_file}")
            print("\n" + "="*70)
            print("CONFIGURAÇÃO NECESSÁRIA")
            print("="*70)
            print("\nEdite o arquivo .env com suas credenciais:")
            print(f"  - Abra: {env_file}")
            print("  - Edite com suas credenciais:")
            print("    * SYS_USERNAME, SYS_PASSWORD, SYS_SECRET_OTP")
            print("    * DB_SERVER, DB_USERNAME, DB_PASSWORD")
            print("  - Salve o arquivo")
            print("  - Execute o programa novamente")
            print("\n" + "="*70 + "\n")
            return False
        else:
            print("ERRO: Arquivo .env.template não encontrado!")
            print(f"Diretório esperado: {base_dir}")
            return False
    
    # Carregar .env
    load_dotenv(env_file, override=True)
    
    # Validar credenciais básicas
    required_vars = [
        'SYS_USERNAME',
        'SYS_PASSWORD',
        'DB_SERVER',
        'DB_USERNAME',
        'DB_PASSWORD',
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("AVISO: Variáveis de ambiente não configuradas!")
        print(f"Variáveis faltando: {', '.join(missing_vars)}")
        print(f"\nEdite o arquivo .env: {env_file}")
        return False
    
    return True

def create_folders():
    """Cria pastas necessárias se não existirem"""
    base_dir = Path(sys.argv[0]).parent if hasattr(sys, 'frozen') else Path(__file__).parent.parent
    
    folders = ['downloads', 'logs', 'bases']
    
    for folder in folders:
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("ROBO DOWNLOAD NEO - Inicializando")
    print("="*70 + "\n")
    
    # Criar pastas
    print("[1/3] Criando pastas necessárias...")
    create_folders()
    print("      ✓ Pastas OK\n")
    
    # Configurar .env
    print("[2/3] Configurando variáveis de ambiente...")
    if not setup_env():
        print("      ✗ Configuração incompleta")
        print("\n" + "="*70)
        input("Pressione ENTER para fechar...")
        return
    print("      ✓ Variáveis carregadas\n")
    
    # Importar e executar app.py
    print("[3/3] Iniciando aplicação...\n")
    print("="*70 + "\n")
    
    try:
        import app
        # Se app.py tem função main, chamar
        if hasattr(app, 'main'):
            app.main()
        else:
            # Caso contrário, o app.py deve ser auto-executável
            pass
    except Exception as e:
        print(f"\n✗ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para fechar...")

if __name__ == '__main__':
    main()
