"""
Teste de envio de PRODUÇÃO para SQL Server

Processa um arquivo Excel de Produção (ExportacaoProducao.xlsx) ou JSON,
parseia os dados e envia para a tabela EXPORTACAO_PRODUCAO no SQL Server.

Suporta:
- DRY_RUN para validar sem enviar
- Retry automático com backoff
- Logging estruturado em JSONL
- Rastreamento de linha do Excel

Uso:
    python tests/test_post_sql_producao.py                  # Usa arquivo Excel recente em downloads/
    python tests/test_post_sql_producao.py --file ./meu.xlsx # Arquivo Excel específico
    python tests/test_post_sql_producao.py --json file.json  # Arquivo JSON parseado
    python tests/test_post_sql_producao.py --dry-run         # Simula envio
    python tests/test_post_sql_producao.py --batch-size 10   # Batch customizado
"""

import sys
import os
from pathlib import Path
import argparse
import json
from datetime import datetime

# Garantir diretório raiz no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configurar parser
parser = argparse.ArgumentParser(
    description='Teste de envio de PRODUÇÃO para SQL Server',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Exemplos:
    # Usa arquivo Excel recente em downloads/
    python test_post_sql_producao.py
    
    # Arquivo Excel específico
    python test_post_sql_producao.py --file ../../downloads/ExportacaoProducao.xlsx
    
    # Simula envio (DRY_RUN)
    python test_post_sql_producao.py --dry-run
    
    # Batch customizado
    python test_post_sql_producao.py --batch-size 50
    
    # Arquivo JSON parseado
    python test_post_sql_producao.py --json ./parsed_producao.json
    """
)

parser.add_argument(
    '--file', '-f',
    help='Arquivo Excel (default: ExportacaoProducao.xlsx em downloads/)',
    default=None
)
parser.add_argument(
    '--json',
    help='Usar arquivo JSON parseado ao invés de Excel',
    default=None
)
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='DRY_RUN: valida sem enviar para SQL'
)
parser.add_argument(
    '--batch-size',
    type=int,
    help='Tamanho do batch (default: BATCH_SIZE do .env)',
    default=None
)
parser.add_argument(
    '--post-retries',
    type=int,
    help='Número de tentativas (default: POST_RETRIES do .env)',
    default=None
)
parser.add_argument(
    '--backoff-base',
    type=float,
    help='Fator base para backoff exponencial',
    default=None
)
parser.add_argument(
    '--verbose', '-v',
    action='store_true',
    help='Modo verbose com debug detalhado'
)

args = parser.parse_args()

# Configurar variáveis de ambiente
if args.dry_run:
    os.environ['DRY_RUN'] = 'true'
    print("🔒 DRY_RUN ATIVO - Nenhum dado será enviado para SQL")
if args.batch_size is not None:
    os.environ['BATCH_SIZE'] = str(args.batch_size)
if args.post_retries is not None:
    os.environ['POST_RETRIES'] = str(args.post_retries)
if args.backoff_base is not None:
    os.environ['BACKOFF_BASE'] = str(args.backoff_base)
if args.verbose:
    os.environ['LOG_LEVEL'] = 'DEBUG'

# Importar funções
from app import parse_export_producao, post_records_to_mssql, logger

print("\n" + "="*70)
print("🧪 TESTE: Envio de PRODUÇÃO para SQL Server")
print("="*70)

# Definir arquivo de entrada
if args.json:
    # Usar arquivo JSON parseado
    json_file = Path(args.json)
    if not json_file.exists():
        print(f"\n❌ Arquivo JSON não encontrado: {json_file}")
        sys.exit(1)
    print(f"\n📋 Carregando JSON parseado: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
    excel_file = "json"
else:
    # Usar arquivo Excel
    if args.file:
        excel_file = Path(args.file)
    else:
        # Procurar arquivo em downloads/
        downloads_dir = ROOT / 'downloads'
        if not downloads_dir.exists():
            print(f"\n❌ Diretório downloads/ não existe: {downloads_dir}")
            sys.exit(1)
        
        files = list(downloads_dir.glob('ExportacaoProducao*.xlsx'))
        if not files:
            print(f"\n❌ Nenhum arquivo 'ExportacaoProducao*.xlsx' encontrado em {downloads_dir}")
            print(f"   Rode primeiro o download ou forneça --file")
            sys.exit(1)
        
        # Usar arquivo mais recente
        excel_file = max(files, key=lambda p: p.stat().st_mtime)
        print(f"\n📥 Arquivo Excel encontrado (mais recente): {excel_file.name}")

    if isinstance(excel_file, str) and excel_file != "json":
        excel_file = Path(excel_file)
    
    if not excel_file.exists():
        print(f"\n❌ Arquivo não encontrado: {excel_file}")
        sys.exit(1)

    # Parsear arquivo Excel
    print(f"📖 Parseando arquivo: {excel_file}")
    try:
        records = parse_export_producao(str(excel_file))
        print(f"✅ Parse bem-sucedido: {len(records)} registros extraídos")
    except Exception as e:
        print(f"\n❌ Erro ao parsear arquivo:")
        print(f"   {type(e).__name__}: {e}")
        sys.exit(1)

# Validar records
if not records:
    print("\n⚠️  Nenhum registro para enviar")
    sys.exit(0)

print(f"\n📊 Resumo dos registros a enviar:")
print(f"   Total: {len(records)} registros")
print(f"   Batch Size: {os.getenv('BATCH_SIZE', 'default')}")
print(f"   DRY_RUN: {'SIM ✓' if os.getenv('DRY_RUN') == 'true' else 'NÃO'}")

# Mostrar amostra do primeiro registro
if records:
    print(f"\n📝 Amostra do primeiro registro:")
    first_record = records[0]
    for key in list(first_record.keys())[:5]:
        value = first_record[key]
        if isinstance(value, str) and len(value) > 50:
            value = value[:47] + "..."
        print(f"   {key}: {value}")
    if len(first_record) > 5:
        print(f"   ... ({len(first_record) - 5} campos adicionais)")

# Enviar para SQL Server
print(f"\n🚀 Iniciando envio para SQL Server...")
print(f"   Tabela: EXPORTACAO_PRODUCAO")
print(f"   Registros: {len(records)}")

try:
    inicio = datetime.now()
    result = post_records_to_mssql(
        records,
        table_name='producao',
        file_name='ExportacaoProducao.xlsx'
    )
    duracao = (datetime.now() - inicio).total_seconds()
    
    # Exibir resultado
    print(f"\n{'='*70}")
    print(f"✅ TESTE CONCLUÍDO")
    print(f"{'='*70}")
    
    if isinstance(result, dict):
        total = result.get('total', len(records))
        success = result.get('success', 0)
        failed = result.get('failed', 0)
        taxa_sucesso = (success / total * 100) if total > 0 else 0
        
        print(f"\n📊 RESULTADO:")
        print(f"   ✅ Inseridos: {success}")
        print(f"   ❌ Falhados: {failed}")
        print(f"   📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        print(f"   ⏱️  Duração: {duracao:.2f}s")
        
        if result.get('batches_total', 0) > 1:
            print(f"   📦 Batches: {result.get('batches_total', 0)} (até {os.getenv('BATCH_SIZE', 25)} registros cada)")
    
    print(f"\n📋 LOGS GERADOS:")
    print(f"   • logs/sent_records_producao.jsonl (registros enviados)")
    print(f"   • logs/robo_download.log (detalhes da execução)")
    
    if os.getenv('DRY_RUN') == 'true':
        print(f"\n🔒 MODO DRY_RUN: Nenhum dado foi realmente enviado")
    
    sys.exit(0)

except Exception as e:
    print(f"\n❌ ERRO AO ENVIAR:")
    print(f"   {type(e).__name__}: {e}")
    print(f"\n📋 Verifique:")
    print(f"   • Conexão com SQL Server")
    print(f"   • Credenciais em .env (DB_SERVER, DB_USERNAME, DB_PASSWORD)")
    print(f"   • Tabela EXPORTACAO_PRODUCAO existe no banco")
    sys.exit(1)
