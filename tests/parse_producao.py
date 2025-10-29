"""
🧪 TESTE: Parse de ExportacaoProducao.xlsx para JSON
⚠️  IMPORTANTE: Este teste APENAS faz parse, sem inserção em banco
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Garantir que o diretório raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import parse_only

def main():
    """
    Parse de ExportacaoProducao.xlsx para JSON - SEM inserção em banco
    """
    # Localizar arquivo
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Primeiro tentar em downloads/ (novo local)
        project_downloads = os.path.join(ROOT, 'downloads', 'ExportacaoProducao.xlsx')
        user_download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        user_downloads = os.path.join(user_download_dir, 'ExportacaoProducao.xlsx')
        
        file_path = project_downloads if os.path.exists(project_downloads) else user_downloads

    if not os.path.exists(file_path):
        print(f"❌ Arquivo não encontrado: {file_path}")
        sys.exit(2)

    print(f"📖 Parseando arquivo: {file_path}")
    
    # APENAS PARSE - SEM BANCO
    records = parse_only(file_path)
    print(f"✅ Parsed {len(records)} records de ExportacaoProducao.xlsx")

    # Garantir pasta de saída
    out_dir = os.path.join(ROOT, 'tests', 'json')
    os.makedirs(out_dir, exist_ok=True)

    # Gerar nome com timestamp
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(out_dir, f'parsed_producao_{ts}.json')

    # Gravar TODOS os registros no JSON
    with open(out_file, 'w', encoding='utf-8') as fo:
        json.dump(records, fo, ensure_ascii=False, indent=2, default=str)

    print(f"💾 Saída gravada em: {out_file}")
    print(f"📊 Total: {len(records)} registros salvos em JSON")
    
    # Mostrar primeiros 3 registros para inspeção
    if records:
        print("\n=== Primeiros 3 registros ===")
        for i, r in enumerate(records[:3], 1):
            print(f"\n--- Registro {i} ---")
            for key, val in r.items():
                if val and key not in ['_line_number', '_file_name']:  # Ocultar metadados
                    print(f"  {key}: {val}")

if __name__ == '__main__':
    main()
