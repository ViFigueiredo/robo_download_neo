"""
Gerar bases/sql_map.json automaticamente a partir da estrutura real do SQL Server
Conecta ao banco, verifica as tabelas EXPORTACAO_* e suas colunas
"""
import pyodbc
import json
import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

print("="*80)
print("🔍 Gerando sql_map.json automaticamente")
print("="*80)

try:
    connection_string = f'Driver={{{DB_DRIVER}}};Server={DB_SERVER};Database={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD}'
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Listar todas as tabelas EXPORTACAO_*
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME LIKE 'EXPORTACAO_%'
        ORDER BY TABLE_NAME
    """)
    
    tabelas = cursor.fetchall()
    
    if not tabelas:
        print("❌ Nenhuma tabela EXPORTACAO_* encontrada no banco!")
        exit(1)
    
    # Mapear arquivo Excel para tabela SQL
    # Estes são os padrões esperados baseado no fluxo
    mapeamento_arquivos = {
        'Exportacao Status.xlsx': 'EXPORTACAO_STATUS',
        'ExportacaoStatus.xlsx': 'EXPORTACAO_STATUS',
        'Exportacao Atividade.xlsx': 'EXPORTACAO_ATIVIDADE',
        'Exportacao Atividades.xlsx': 'EXPORTACAO_ATIVIDADE',
        'ExportacaoAtividade.xlsx': 'EXPORTACAO_ATIVIDADE',
        'ExportacaoProducao.xlsx': 'EXPORTACAO_PRODUCAO',
    }
    
    sql_map = {}
    
    # Para cada tabela, extrair suas colunas
    for tabela_tuple in tabelas:
        table_name = tabela_tuple[0]
        
        print(f"\n📋 Processando tabela: {table_name}")
        
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        colunas = [row[0] for row in cursor.fetchall()]
        print(f"   ✅ {len(colunas)} colunas encontradas")
        
        # Encontrar os arquivos que mapeiam para esta tabela
        arquivos_para_tabela = [arq for arq, tbl in mapeamento_arquivos.items() if tbl == table_name]
        
        # Adicionar ao mapa SQL
        for arquivo in arquivos_para_tabela:
            sql_map[arquivo] = {
                'tabela': table_name,
                'colunas': colunas
            }
            print(f"   ➡️  {arquivo} → {table_name}")
    
    # Salvar em bases/sql_map.json
    bases_dir = os.path.join(os.path.dirname(__file__), 'bases')
    os.makedirs(bases_dir, exist_ok=True)
    
    sql_map_file = os.path.join(bases_dir, 'sql_map.json')
    
    with open(sql_map_file, 'w', encoding='utf-8') as f:
        json.dump(sql_map, f, ensure_ascii=False, indent=4)
    
    print("\n" + "="*80)
    print(f"✅ Arquivo gerado com sucesso: {sql_map_file}")
    print("="*80)
    
    # Mostrar conteúdo
    print("\n📊 Conteúdo do sql_map.json:")
    print("-"*80)
    for arquivo, config in sql_map.items():
        tabela = config['tabela']
        colunas_count = len(config['colunas'])
        print(f"\n{arquivo}")
        print(f"  Tabela: {tabela}")
        print(f"  Colunas ({colunas_count}): {', '.join(config['colunas'][:5])}...")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Erro ao gerar sql_map.json: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ Próximo passo: usar este arquivo em app.py para inserir registros")
