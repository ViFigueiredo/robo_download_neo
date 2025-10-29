"""
Listar TODAS as tabelas do banco e suas colunas
"""
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv('DB_SERVER')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

try:
    connection_string = f'Driver={{{DB_DRIVER}}};Server={DB_SERVER};Database={DB_DATABASE};UID={DB_USERNAME};PWD={DB_PASSWORD}'
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # Listar TODAS as tabelas
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    tabelas = cursor.fetchall()
    
    print("="*80)
    print("TODAS AS TABELAS NO BANCO")
    print("="*80)
    for tabela in tabelas:
        print(f"  - {tabela[0]}")
    
    # Para cada tabela EXPORTACAO_*, mostrar as colunas
    print("\n" + "="*80)
    print("ESTRUTURA DAS TABELAS EXPORTACAO_*")
    print("="*80)
    
    for tabela in tabelas:
        table_name = tabela[0]
        if 'EXPORTACAO' in table_name:
            print(f"\n📋 {table_name}:")
            print("-" * 80)
            
            cursor.execute(f"""
                SELECT 
                    COLUMN_NAME, 
                    DATA_TYPE, 
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """)
            
            cols = cursor.fetchall()
            for col in cols:
                col_name, data_type, char_max, is_nullable = col
                size_info = f"({char_max})" if char_max else ""
                nullable = "NULL" if is_nullable == 'YES' else "NOT NULL"
                print(f"  {col_name:30} {data_type:15} {size_info:10} {nullable}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
