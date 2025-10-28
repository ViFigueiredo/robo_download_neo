#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de Conexão com SQL Server

Este script valida a conectividade com o SQL Server
usando as credenciais configuradas no .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
if not Path('.env').exists():
    print('❌ Arquivo .env não encontrado!')
    sys.exit(1)

load_dotenv('.env', override=True)

# Validar variáveis obrigatórias
required_vars = ['DB_SERVER', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD', 'DB_DRIVER']
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    print(f"❌ Variáveis obrigatórias faltando: {', '.join(missing)}")
    sys.exit(1)

try:
    import pyodbc
except ImportError:
    print("❌ pyodbc não instalado. Execute: pip install pyodbc")
    sys.exit(1)

def test_mssql_connection():
    """Testa conexão com SQL Server"""
    print("\n" + "="*60)
    print("🧪 TESTE DE CONEXÃO COM SQL SERVER")
    print("="*60 + "\n")
    
    # Ler credenciais
    db_server = os.getenv('DB_SERVER')
    db_database = os.getenv('DB_DATABASE')
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
    
    print(f"📍 Servidor: {db_server}")
    print(f"📍 Banco: {db_database}")
    print(f"📍 Usuário: {db_username}")
    print(f"📍 Driver: {db_driver}")
    print()
    
    try:
        # Construir string de conexão
        conn_string = (
            f'Driver={{{db_driver}}};'
            f'Server={db_server};'
            f'Database={db_database};'
            f'UID={db_username};'
            f'PWD={db_password};'
            f'Encrypt=no;TrustServerCertificate=no;Connection Timeout=30;'
        )
        
        print("🔌 Conectando ao SQL Server...")
        connection = pyodbc.connect(conn_string)
        print("✅ Conexão estabelecida com sucesso!\n")
        
        # Testar query
        cursor = connection.cursor()
        
        print("🔍 Obtendo versão do SQL Server...")
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"✅ {version}\n")
        
        # Listar tabelas
        print("📋 Tabelas esperadas:")
        expected_tables = [
            'EXPORTACAO_PRODUCAO',
            'EXPORTACAO_ATIVIDADE',
            'EXPORTACAO_STATUS'
        ]
        
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        for table in expected_tables:
            if table in existing_tables:
                print(f"  ✅ {table} - EXISTE")
                
                # Contar colunas
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{table}'
                """)
                col_count = cursor.fetchone()[0]
                print(f"     └─ {col_count} colunas")
            else:
                print(f"  ⚠️  {table} - NÃO ENCONTRADA")
        
        # Verificar espaço em disco
        print("\n💾 Espaço em disco do banco:")
        cursor.execute("""
            SELECT 
                name,
                size * 8.0 / 1024 AS size_mb
            FROM sys.master_files
            WHERE database_id = DB_ID()
        """)
        
        for name, size_mb in cursor.fetchall():
            print(f"  {name}: {size_mb:.2f} MB")
        
        # Registro de teste
        print("\n📝 Tentando inserir registro de teste...")
        try:
            test_record = {
                'GRUPO': 'TESTE',
                'FILA': 'TESTE_' + __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'),
                'NUMERO ATIVIDADE': '00000',
                'PEDIDO VINCULO': '',
                'COTAÇÃO': '',
                'ATIVIDADE ORIGEM': '',
                'CODIGO PORTABILIDADE': '',
                'LOGIN OPERADORA': '',
                'NOME CLIENTE': 'TESTE CONEXÃO',
                'CPF/CNPJ': '00000000000000',
                'PF OU PJ': 'PF',
                'CIDADE CLIENTE': '',
                'ESTADO': '',
                'DDD': '',
                'PROPRIETÁRIO DO PEDIDO': '',
                'TAGS USUARIO PEDIDO': '',
                'ADM DO PEDIDO': '',
                'CONSULTOR NA OPERADORA': '',
                'EQUIPE': '',
                'ETAPA PEDIDO': '',
                'CATEGORIA': '',
                'SUB-CATEGORIA': '',
                'CADASTRO': '',
                'ATUALIZACAO': '',
                'SOLICITACAO': '',
                'TIPO NEGOCIACAO': '',
                'NOTAS FISCAIS': '',
                'REVISAO': '',
                'ATIVIDADES': '',
                'ITEM': '',
                'NUMERO': '',
                'NUMERO PROVISORIO': '',
                'ETAPA ITEM': '',
                'PORTABILIDADE': '',
                'OPERADORA CEDENTE': '',
                'NOME CEDENTE': '',
                'CPF CNPJ CEDENTE': '',
                'TELEFONE CEDENTE': '',
                'EMAIL CEDENTE': '',
                'PRODUTO': '',
                'VALOR UNIT': '',
                'QUANTIDADE': '',
                'DATA REF': '',
                'ORIGEM': '',
                'DATA INSTALAÇÃO': '',
                'PERIODO': '',
                'CIDADE INSTALAÇÃO': '',
                'UF': '',
                'RPON': '',
                'INSTANCIA': '',
                'TAGS': 'TESTE_CONEXÃO'
            }
            
            # Carregar sql_map para obter colunas corretas
            import json
            if Path('sql_map.json').exists():
                with open('sql_map.json', 'r', encoding='utf-8') as f:
                    sql_map = json.load(f)
                    expected_columns = sql_map['ExportacaoProducao.xlsx']['colunas']
                    
                    columns = ', '.join(f'[{col}]' for col in expected_columns)
                    placeholders = ', '.join(['?' for _ in expected_columns])
                    insert_stmt = f"INSERT INTO [EXPORTACAO_PRODUCAO] ({columns}) VALUES ({placeholders})"
                    
                    values = [test_record.get(col, '') for col in expected_columns]
                    cursor.execute(insert_stmt, values)
                    connection.commit()
                    print("  ✅ Registro de teste inserido com sucesso!")
                    
                    # Remover registro de teste
                    print("🗑️  Removendo registro de teste...")
                    cursor.execute(f"DELETE FROM [EXPORTACAO_PRODUCAO] WHERE FILA = ?", (test_record['FILA'],))
                    connection.commit()
                    print("  ✅ Registro de teste removido.")
        except Exception as e:
            print(f"  ⚠️  Não foi possível inserir teste: {e}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*60 + "\n")
        return True
        
    except pyodbc.Error as e:
        print(f"\n❌ ERRO DE CONEXÃO ODBC:")
        print(f"   {e}\n")
        print("💡 Possíveis causas:")
        print("   • Servidor SQL Server não está acessível")
        print("   • Credenciais incorretas")
        print("   • Driver ODBC não instalado")
        print("   • Firewall bloqueando porta")
        return False
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        return False

if __name__ == '__main__':
    success = test_mssql_connection()
    sys.exit(0 if success else 1)
