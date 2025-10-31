#!/usr/bin/env python3
"""
ROBO DOWNLOAD NEO - Configuração Embutida
Carrega credenciais do .env (compatível com desenvolvimento e produção)
Executado automaticamente antes de app.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def get_embedded_config():
    """
    Carrega configuração do .env
    Tenta múltiplos locais:
    1. .env no diretório atual
    2. .env no diretório raiz do projeto
    3. Variáveis de ambiente existentes
    """
    
    # Tentar carregar .env em múltiplos locais
    env_paths = [
        Path.cwd() / '.env',  # Diretório de execução
        Path(__file__).parent.parent / '.env',  # Raiz do projeto (se executado de scripts/)
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            print(f"[CONFIG] Carregando .env de: {env_path}", file=sys.stderr)
            load_dotenv(env_path)
            env_loaded = True
            break
    
    if not env_loaded:
        print("[CONFIG] ⚠️  Nenhum arquivo .env encontrado. Usando variáveis de ambiente existentes.", file=sys.stderr)
    
    # Tentar ler do .env ou variáveis de ambiente
    EMBEDDED_CONFIG = {
        # Sistema Alvo
        'SYS_URL': os.getenv('SYS_URL', 'https://neo.solucoes.plus/login'),
        'SYS_USERNAME': os.getenv('SYS_USERNAME', ''),
        'SYS_PASSWORD': os.getenv('SYS_PASSWORD', ''),
        'SYS_SECRET_OTP': os.getenv('SYS_SECRET_OTP', ''),
        
        # Destino
        'DESTINO_FINAL_DIR': os.getenv('DESTINO_FINAL_DIR', 'Y:'),
        
        # Browser
        'BROWSER': os.getenv('BROWSER', 'chrome'),
        'HEADLESS': os.getenv('HEADLESS', 'true'),
        
        # Download
        'RETRIES_DOWNLOAD': os.getenv('RETRIES_DOWNLOAD', '3'),
        'TIMEOUT_DOWNLOAD': os.getenv('TIMEOUT_DOWNLOAD', '60'),
        'OTP_URL': os.getenv('OTP_URL', 'http://192.168.11.86:8001/generate_otp'),
        
        # Banco de Dados
        'DB_SERVER': os.getenv('DB_SERVER', ''),
        'DB_DATABASE': os.getenv('DB_DATABASE', ''),
        'DB_USERNAME': os.getenv('DB_USERNAME', ''),
        'DB_PASSWORD': os.getenv('DB_PASSWORD', ''),
        'DB_DRIVER': os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
        
        # Configurações
        'DRY_RUN': os.getenv('DRY_RUN', 'false'),
        'BATCH_SIZE': os.getenv('BATCH_SIZE', '1000'),
        'POST_RETRIES': os.getenv('POST_RETRIES', '3'),
        'BACKOFF_BASE': os.getenv('BACKOFF_BASE', '1.5'),
    }
    
    return EMBEDDED_CONFIG

def setup_embedded_config():
    """Carrega configuração do .env e aplica ao os.environ"""
    
    print("[CONFIG] Carregando configuração...", file=sys.stderr)
    
    # Obter configuração do .env
    config = get_embedded_config()
    
    # Definir todas as variáveis de ambiente
    for key, value in config.items():
        os.environ[key] = value
        if key not in ['SYS_PASSWORD', 'DB_PASSWORD', 'SYS_SECRET_OTP']:
            print(f"[CONFIG] {key}={value}", file=sys.stderr)
        else:
            print(f"[CONFIG] {key}=***[OCULTO]***", file=sys.stderr)
    
    print("[CONFIG] ✅ Todas as configurações carregadas com sucesso!", file=sys.stderr)

if __name__ == '__main__':
    # Aplicar configuração
    setup_embedded_config()
    
    # Criar pastas necessárias se não existirem
    if hasattr(sys, 'frozen'):
        # Executando como .exe compilado
        base_dir = Path(sys.executable).parent
    else:
        # Executando como script Python
        base_dir = Path(__file__).parent.parent
    
    for folder in ['downloads', 'logs', 'bases']:
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)
    
    print(f"[INIT] ✅ Pastas criadas/verificadas em: {base_dir}", file=sys.stderr)
    print(f"[INIT] Iniciando app.py...", file=sys.stderr)
    
    # Executar app.py
    sys.path.insert(0, str(base_dir))
    import app
