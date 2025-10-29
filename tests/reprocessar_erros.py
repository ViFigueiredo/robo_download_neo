"""
🔄 Script de Reprocessamento de Erros
Lê erro_records_*.jsonl e re-insere registros no SQL Server
Trata truncamento de campos automaticamente
"""

import json
import os
import sys
import pyodbc
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reprocessar_erros.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Para Windows - suportar UTF-8 no console
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Carregar variáveis de ambiente
load_dotenv()

DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

# Carregar sql_map.json
with open('bases/sql_map.json', 'r', encoding='utf-8') as f:
    sql_map = json.load(f)

# Mapear tabela -> limite de caracteres dos campos
FIELD_LIMITS = {
    'EXPORTACAO_STATUS': {
        'NUMERO': 255,
        'ENTROU': 255,
        'ETAPA': 255,
        'PRAZO': 255,
        'SLA_HORAS': 255,
        'TEMPO': 255,
        'USUARIO_ENTRADA': 255,
        'SAIU': 255,
        'USUARIO_SAIDA': 255,
        'MOVIMENTACAO': 255,  # ⚠️ Era 255, você aumentou
        'TAG_ATIVIDADE': 255,
    },
    'EXPORTACAO_ATIVIDADE': {
        # Adicionar limites específicos se necessário
    },
    'EXPORTACAO_PRODUCAO': {
        # Adicionar limites específicos se necessário
    }
}


def truncar_valor(valor, limite):
    """Trunca string se exceder limite"""
    if isinstance(valor, str) and len(valor) > limite:
        return valor[:limite]
    return valor


def processar_error_file(error_file_path):
    """Processa um arquivo error_records_*.jsonl"""
    if not os.path.exists(error_file_path):
        logger.warning(f"Arquivo não encontrado: {error_file_path}")
        return 0, 0, 0
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Processando: {error_file_path}")
    logger.info(f"{'='*70}\n")
    
    # Determinar tabela pelo nome do arquivo
    # error_records_status.jsonl -> EXPORTACAO_STATUS
    file_base = Path(error_file_path).stem  # 'error_records_status'
    file_suffix = file_base.replace('error_records_', '')  # 'status'
    
    # Mapear sufixo para tabela
    sufixo_para_tabela = {
        'status': 'EXPORTACAO_STATUS',
        'atividades': 'EXPORTACAO_ATIVIDADE',
        'producao': 'EXPORTACAO_PRODUCAO',
    }
    
    table_name = sufixo_para_tabela.get(file_suffix)
    if not table_name:
        logger.error(f"Nao consegui mapear tabela para: {file_suffix}")
        return 0, 0, 0
    
    logger.info(f"Tabela alvo: {table_name}\n")
    
    success_count = 0
    duplicate_count = 0
    error_count = 0
    
    # Conectar ao SQL Server
    try:
        connection_string = f'Driver={{{DB_DRIVER}}};Server={DB_SERVER};Database={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD}'
        connection = pyodbc.connect(connection_string, timeout=30)
        cursor = connection.cursor()
        logger.info(f"Conectado ao SQL Server: {DB_SERVER}/{DB_DATABASE}\n")
    except Exception as e:
        logger.error(f"Erro ao conectar: {e}")
        return 0, 0, 0
    
    # Obter colunas válidas da tabela SQL
    try:
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        valid_columns = set(row[0] for row in cursor.fetchall())
        logger.info(f"Colunas validas na tabela: {', '.join(sorted(valid_columns))}\n")
    except Exception as e:
        logger.error(f"Erro ao obter colunas: {e}")
        return 0, 0, 0
    
    # Ler arquivo de erros
    try:
        with open(error_file_path, 'r', encoding='utf-8') as f:
            error_records = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Erro ao ler arquivo: {e}")
        return 0, 0, 0
    
    logger.info(f"Total de registros para reprocessar: {len(error_records)}\n")
    
    # Processar cada registro
    for i, error_entry in enumerate(error_records, 1):
        record = error_entry.get('record', {})
        source = error_entry.get('source', {})
        line_number = source.get('line', '?')
        file_name = source.get('file', '?')
        
        # 🔧 NOVO: Filtrar apenas colunas que existem na tabela SQL
        colunas_validas = [col for col in record.keys() if col in valid_columns]
        
        if not colunas_validas:
            error_count += 1
            logger.error(
                f"[{i}/{len(error_records)}] Nenhuma coluna valida: {file_name} linha {line_number}"
            )
            continue
        
        # Truncar campos que excedem limite
        for field in colunas_validas:
            if field in record:
                original = record[field]
                record[field] = truncar_valor(record[field], FIELD_LIMITS.get(table_name, {}).get(field, 255))
                if original != record[field]:
                    logger.debug(
                        f"  Campo '{field}' truncado de {len(original)} para {len(record[field])} chars "
                        f"(Linha {line_number} de {file_name})"
                    )
        
        # Preparar inserção (apenas colunas válidas)
        valores = [record[col] for col in colunas_validas]
        columns_str = ', '.join(f'[{col}]' for col in colunas_validas)
        placeholders = ', '.join(['?' for _ in colunas_validas])
        insert_stmt = f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({placeholders})"
        
        try:
            cursor.execute(insert_stmt, valores)
            success_count += 1
            logger.info(
                f"[{i}/{len(error_records)}] Inserido: {file_name} linha {line_number}"
            )
        
        except pyodbc.IntegrityError as ie:
            error_msg = str(ie)
            if 'PRIMARY KEY' in error_msg or 'UNIQUE' in error_msg:
                duplicate_count += 1
                logger.debug(
                    f"[{i}/{len(error_records)}] DUPLICATA: {file_name} linha {line_number} "
                    f"(ja inserida em execucao anterior)"
                )
            else:
                error_count += 1
                logger.error(
                    f"[{i}/{len(error_records)}] Erro de integridade: {file_name} linha {line_number}\n"
                    f"   {error_msg[:150]}"
                )
        
        except Exception as e:
            error_count += 1
            logger.error(
                f"[{i}/{len(error_records)}] Erro geral: {file_name} linha {line_number}\n"
                f"   {type(e).__name__}: {str(e)[:150]}"
            )
    
    # Commit
    try:
        connection.commit()
        logger.info(f"\nCommit realizado com sucesso")
    except Exception as e:
        logger.error(f"\nErro ao fazer commit: {e}")
        connection.rollback()
    
    cursor.close()
    connection.close()
    
    return success_count, duplicate_count, error_count


def main():
    """Processa todos os arquivos error_records_*.jsonl"""
    logger.info(f"\n REPROCESSAMENTO DE ERROS")
    logger.info(f"    Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Procurar todos os error_records_*.jsonl
    error_files = list(Path('logs').glob('error_records_*.jsonl'))
    
    if not error_files:
        logger.warning("Nenhum arquivo error_records_*.jsonl encontrado")
        return
    
    logger.info(f"Encontrados {len(error_files)} arquivo(s) de erro:\n")
    for f in error_files:
        logger.info(f"   • {f.name}")
    logger.info("")
    
    total_success = 0
    total_duplicate = 0
    total_error = 0
    
    # Processar cada arquivo
    for error_file in sorted(error_files):
        success, duplicate, error = processar_error_file(str(error_file))
        total_success += success
        total_duplicate += duplicate
        total_error += error
    
    # Resumo final
    logger.info(f"\n{'='*70}")
    logger.info(f" RESUMO FINAL")
    logger.info(f"{'='*70}")
    logger.info(f"Inseridos com sucesso: {total_success}")
    logger.info(f" Duplicatas ignoradas: {total_duplicate}")
    logger.info(f" Erros: {total_error}")
    logger.info(f" Taxa de sucesso: {(total_success / (total_success + total_error) * 100):.1f}%" 
                if (total_success + total_error) > 0 else "N/A")
    logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏸️  Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ ERRO NÃO TRATADO: {e}", exc_info=True)
        sys.exit(1)
