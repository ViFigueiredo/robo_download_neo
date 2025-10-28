"""
Teste de download individual - Relatório de Atividades

Uso:
    python tests/test_download_atividades.py [--headless] [--timeout 60]

Exemplo:
    # Download com navegador visível
    python tests/test_download_atividades.py

    # Download em modo headless (sem UI)
    python tests/test_download_atividades.py --headless

    # Download com timeout customizado
    python tests/test_download_atividades.py --timeout 120
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Garantir que o diretório raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (
    iniciar_driver, acessar_pagina, login, abrir_sidebar,
    exportAtividades, logger
)
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv(os.path.join(ROOT, '.env'))

def test_download_atividades(headless=False, timeout=60):
    """
    Testa download individual do relatório de Atividades.
    
    Args:
        headless: Se True, executa sem UI visual
        timeout: Timeout em segundos para download
    """
    driver = None
    try:
        # Configurar variáveis temporárias para este teste
        os.environ['HEADLESS'] = 'true' if headless else 'false'
        os.environ['TIMEOUT_DOWNLOAD'] = str(timeout)
        
        logger.info("=" * 70)
        logger.info("🧪 TESTE: Download Individual - Atividades")
        logger.info("=" * 70)
        logger.info(f"HEADLESS: {headless} | TIMEOUT: {timeout}s")
        
        # Iniciar driver
        logger.info("[1/5] Iniciando navegador...")
        driver = iniciar_driver()
        
        # Acessar página
        url = os.getenv("SYS_URL")
        logger.info(f"[2/5] Acessando {url}...")
        acessar_pagina(driver, url)
        time.sleep(2)
        
        # Login
        logger.info("[3/5] Realizando login...")
        login(driver)
        time.sleep(2)
        
        # Abrir sidebar
        logger.info("[4/5] Abrindo sidebar...")
        abrir_sidebar(driver)
        time.sleep(1)
        
        # Download
        logger.info("[5/5] Iniciando download de Atividades...")
        exportAtividades(driver)
        time.sleep(2)
        
        logger.info("=" * 70)
        logger.info("✅ SUCESSO: Download de Atividades concluído!")
        logger.info("=" * 70)
        
        # Verificar arquivo baixado
        downloads_dir = os.path.join(ROOT, 'downloads')
        if os.path.exists(downloads_dir):
            arquivos = [f for f in os.listdir(downloads_dir) if f.endswith('.xlsx')]
            logger.info(f"📁 Arquivos em {downloads_dir}:")
            for arquivo in sorted(arquivos):
                tamanho = os.path.getsize(os.path.join(downloads_dir, arquivo)) / 1024
                logger.info(f"   📄 {arquivo} ({tamanho:.1f} KB)")
        
        return True
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ ERRO: Teste falhou!")
        logger.error(f"Detalhes: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Navegador fechado")
            except Exception as e:
                logger.warning(f"Erro ao fechar navegador: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Download individual: Relatório de Atividades",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python tests/test_download_atividades.py              # Download com UI visível
  python tests/test_download_atividades.py --headless   # Modo headless (sem UI)
  python tests/test_download_atividades.py --timeout 120 # Timeout de 120s
        """
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Executar em modo headless (sem UI visual)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout em segundos para download (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Executar teste
    success = test_download_atividades(
        headless=args.headless,
        timeout=args.timeout
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
