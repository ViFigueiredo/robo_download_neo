#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar colunas das tabelas"""

import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

db_server = os.getenv('DB_SERVER')
db_database = os.getenv('DB_DATABASE')
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')

conn_string = (
    f'Driver={{{db_driver}}};'
    f'Server={db_server};'
    f'Database={db_database};'
    f'UID={db_username};'
    f'PWD={db_password};'
    f'Encrypt=no;TrustServerCertificate=no;Connection Timeout=30;'
)

conn = pyodbc.connect(conn_string)
cursor = conn.cursor()

for tabela in ['EXPORTACAO_PRODUCAO', 'EXPORTACAO_ATIVIDADE', 'EXPORTACAO_STATUS']:
    print(f"\n📋 COLUNAS REAIS NA TABELA {tabela}:\n")
    
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME='{tabela}' 
        ORDER BY ORDINAL_POSITION
    """)
    
    cols = []
    for col_name, data_type in cursor.fetchall():
        print(f"  {col_name:40} ({data_type})")
        cols.append(col_name)
    
    print(f"\n  JSON format:")
    print(f'  "colunas": [')
    for col in cols:
        print(f'      "{col}",')
    print(f'  ]')

cursor.close()
conn.close()
