import sys
import os
from pathlib import Path
import argparse
import json

# Garantir diretório raiz no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

parser = argparse.ArgumentParser(description='Test de envio de STATUS para a API a partir de arquivo JSON.')
parser.add_argument('--file', '-f', help='Caminho para o arquivo JSON com registros (default: latest parsed_status_*.json)', default=None)
parser.add_argument('--dry-run', action='store_true', help='Ativa modo dry-run (não envia, apenas registra)')
parser.add_argument('--batch-size', type=int, help='Tamanho do batch para envio', default=None)
parser.add_argument('--post-retries', type=int, help='Número de tentativas para post', default=None)
parser.add_argument('--backoff-base', type=float, help='Fator base para backoff exponencial', default=None)
parser.add_argument('--url', help='Override da URL_TABELA_ATIVIDADES_STATUS', default=None)
parser.add_argument('--token', help='Override do BEARER_TOKEN', default=None)
args = parser.parse_args()

# Configurar variáveis de ambiente antes de importar app
if args.dry_run:
    os.environ['DRY_RUN'] = 'true'
if args.batch_size is not None:
    os.environ['BATCH_SIZE'] = str(args.batch_size)
if args.post_retries is not None:
    os.environ['POST_RETRIES'] = str(args.post_retries)
if args.backoff_base is not None:
    os.environ['BACKOFF_BASE'] = str(args.backoff_base)
if args.token is not None:
    os.environ['BEARER_TOKEN'] = args.token

# Agora importamos a função do módulo app
from app import post_records_to_nocodb, registrar_resumo_envio

# Descobrir arquivo JSON se não foi informado
if args.file:
    file_path = Path(args.file)
else:
    json_dir = ROOT / 'tests' / 'json'
    if not json_dir.exists():
        print(f"Diretório {json_dir} não existe. Rode primeiro test_parse_status.py")
        sys.exit(2)
    files = list(json_dir.glob('parsed_status_*.json'))
    if not files:
        print(f"Nenhum arquivo parsed_status_*.json encontrado em {json_dir}. Rode test_parse_status.py primeiro.")
        sys.exit(2)
    # Escolher o arquivo mais recentemente modificado
    file_path = max(files, key=lambda p: p.stat().st_mtime)
    print(f"Usando arquivo mais recente: {file_path}")

if not file_path.exists():
    print(f"Arquivo não encontrado: {file_path}")
    sys.exit(2)

# Carregar registros
with open(file_path, 'r', encoding='utf-8') as f:
    records = json.load(f)

print(f"Carregados {len(records)} registros de {file_path}")

# Determinar URL da tabela
table_url = args.url or os.getenv('URL_TABELA_ATIVIDADES_STATUS')
if not table_url:
    print("ERRO: URL_TABELA_ATIVIDADES_STATUS não configurada no .env e não fornecida via --url")
    sys.exit(1)

print(f"Enviando para: {table_url}")

# Chamar a função de envio do app
import time
try:
    inicio = time.time()
    result = post_records_to_nocodb(records, table_url=table_url, table_name='atividades_status')
    duracao = time.time() - inicio
    print('\nEnvio (ou simulação) finalizado. Verifique logs/sent_records_atividades_status.jsonl e robo_download.log')
    if isinstance(result, dict):
        print('Resumo:')
        print(json.dumps(result, indent=2, ensure_ascii=False))
        registrar_resumo_envio('atividades_status', str(file_path), result, duracao)
        print(f'Resumo gravado em logs/envios_resumo.jsonl')
except Exception as e:
    print(f'Erro ao executar post_records_to_nocodb: {e}')
    raise
