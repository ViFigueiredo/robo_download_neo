import sys
import os
from pathlib import Path

# Garantir que o diretório raiz do projeto esteja no sys.path quando o teste for executado
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import parse_export_producao

def main():
    # Permite passar o caminho do arquivo como argumento, caso contrário tenta na pasta Downloads
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        user_download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        file_path = os.path.join(user_download_dir, 'Exportacao Status.xlsx')

    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        print(f"Uso: python {sys.argv[0]} [caminho_para_ExportacaoStatus.xlsx]")
        sys.exit(2)

    print(f"Parseando arquivo: {file_path}")
    records = parse_export_producao(file_path)
    print(f"Parsed {len(records)} records de ExportacaoStatus.xlsx")

    # Garantir pasta de saída
    out_dir = os.path.join(ROOT, 'tests', 'json')
    os.makedirs(out_dir, exist_ok=True)

    # Gerar nome com timestamp
    from datetime import datetime
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = os.path.join(out_dir, f'parsed_status_{ts}.json')

    # Gravar todos os registros no JSON
    import json
    with open(out_file, 'w', encoding='utf-8') as fo:
        json.dump(records, fo, ensure_ascii=False, indent=2, default=str)

    print(f"Saída gravada em: {out_file}")
    
    # Mostrar primeiros 3 registros para inspeção
    print("\n=== Primeiros 3 registros ===")
    for i, r in enumerate(records[:3], 1):
        print(f"\n--- Registro {i} ---")
        for key, val in r.items():
            if val:  # só mostrar campos preenchidos
                print(f"  {key}: {val}")

if __name__ == '__main__':
    main()
