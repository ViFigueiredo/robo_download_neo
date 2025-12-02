"""
Módulo para configurar logging com rotação de arquivos e múltiplos handlers.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def configurar_logging():
    """Configura o sistema de logging com rotação."""
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    max_size_mb = int(os.getenv("LOG_MAX_SIZE_MB", "10"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Criar diretório de logs se não existir
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remover handlers existentes para evitar duplicatas
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formato de log
    formato = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo com rotação
    if max_size_mb > 0:
        tamanho_bytes = max_size_mb * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(
            'robo_download.log',
            maxBytes=tamanho_bytes,
            backupCount=backup_count
        )
    else:
        # Se max_size_mb == 0, usar arquivo sem limite
        file_handler = logging.FileHandler('robo_download.log')
    
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formato)
    logger.addHandler(file_handler)
    
    # Handler para console (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formato)
    logger.addHandler(console_handler)
    
    logger.info("="*80)
    logger.info("Sistema de logging configurado")
    logger.info(f"Nível: {log_level}, Tamanho máximo: {max_size_mb}MB, Backups: {backup_count}")
    logger.info("="*80)
    
    return logger
