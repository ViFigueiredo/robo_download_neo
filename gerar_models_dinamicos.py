#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador Dinâmico de Modelos SQLAlchemy

Lê sql_map.json e gera models.py automaticamente com:
- Modelos ORM para cada tabela
- Todas as colunas mapeadas
- Primary keys corretos
- Relacionamentos (se aplicável)

Uso:
    python gerar_models_dinamicos.py
    
Saída:
    models/models_generated.py (substitui models.py)
"""

import json
import os
from datetime import datetime

SQL_MAP_FILE = 'bases/sql_map.json'
OUTPUT_FILE = 'models/models_generated.py'

# Mapeamento de arquivo Excel → Nome da Classe e Tabela
FILE_TO_CLASS = {
    'ExportacaoProducao.xlsx': {
        'class_name': 'ExportacaoProducao',
        'table_name': 'EXPORTACAO_PRODUCAO',
        'primary_key': 'NUMERO_ATIVIDADE',
    },
    'Exportacao Atividade.xlsx': {
        'class_name': 'ExportacaoAtividade',
        'table_name': 'EXPORTACAO_ATIVIDADE',
        'primary_key': 'ATIVIDADE',
    },
    'Exportacao Status.xlsx': {
        'class_name': 'ExportacaoStatus',
        'table_name': 'EXPORTACAO_STATUS',
        'primary_key': 'NUMERO',
    },
}

# Colunas que devem ser de DATA (auto-detectadas por nome)
DATA_KEYWORDS = ['data', 'data_', 'timestamp', 'timestamp_']


def normalizar_nome_coluna(nome_excel):
    """Converte nome da coluna Excel para nome de atributo Python"""
    # Já vem mapeado em sql_map.json, mas se não estiver, tenta normalizar
    nome = nome_excel.upper()
    
    # Remover acentos e caracteres especiais
    acentos = {
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C',
    }
    for acentuado, sem_acento in acentos.items():
        nome = nome.replace(acentuado, sem_acento)
    
    # Trocar caracteres especiais por underscore
    nome = nome.replace('-', '_').replace('/', '_').replace(' ', '_').replace('.', '_')
    
    # Remover underscores múltiplos
    while '__' in nome:
        nome = nome.replace('__', '_')
    
    return nome.strip('_')


def gerar_coluna_sqlalchemy(nome_excel, eh_pk=False):
    """Gera definição de coluna SQLAlchemy"""
    nome_py = normalizar_nome_coluna(nome_excel)
    
    # Tipo de coluna
    tipo = 'String'
    
    # Adicionar tamanho padrão para String
    tamanho = '(4000)'  # Tamanho generoso para NVARCHAR
    
    # Primary key
    if eh_pk:
        tipo_def = f'Column({tipo}{tamanho}, primary_key=True)'
    else:
        tipo_def = f'Column({tipo}{tamanho})'
    
    return f"    {nome_py} = {tipo_def}"


def gerar_modelo(class_info, colunas_excel):
    """Gera código de um modelo SQLAlchemy"""
    class_name = class_info['class_name']
    table_name = class_info['table_name']
    primary_key = normalizar_nome_coluna(class_info['primary_key'])
    
    linhas = []
    linhas.append(f"\nclass {class_name}(Base):")
    linhas.append(f'    """Modelo ORM para tabela {table_name}"""')
    linhas.append(f'    __tablename__ = \'{table_name}\'')
    linhas.append("")
    
    # Gerar colunas
    for col_excel in colunas_excel:
        if col_excel.startswith('_'):  # Ignorar colunas internas
            continue
        
        # Normalizar nome para comparação
        col_normalizado = normalizar_nome_coluna(col_excel)
        eh_pk = col_normalizado == primary_key
        linhas.append(gerar_coluna_sqlalchemy(col_excel, eh_pk))
    
    # Adicionar DATA_IMPORTACAO
    linhas.append(f"    DATA_IMPORTACAO = Column(String, nullable=False, default='')")
    
    linhas.append("")
    linhas.append(f"    def __repr__(self):")
    linhas.append(f'        return f"<{class_name}(...)>"')
    
    return '\n'.join(linhas)


def gerar_imports():
    """Gera imports necessários"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Modelos SQLAlchemy Gerados Dinamicamente

Este arquivo é gerado automaticamente por gerar_models_dinamicos.py
Não edite manualmente!

Data de geração: {timestamp}
Fonte: bases/sql_map.json
\"\"\"

from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Base para todos os modelos
Base = declarative_base()


def get_engine():
    \"\"\"Cria engine de conexão ao SQL Server\"\"\"
    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_DATABASE', 'rpa_neocrm')
    username_var = os.getenv('DB_USERNAME', 'sa')
    password_var = os.getenv('DB_PASSWORD', '')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
    
    # Connection string
    connection_string = (
        f'mssql+pyodbc://{{username_var}}:{{password_var}}@{{server}}:1434/{{database}}'
        f'?driver={{driver}}&TrustServerCertificate=yes'
    )
    
    return create_engine(connection_string, echo=False, pool_pre_ping=True)


def get_session():
    \"\"\"Cria uma nova session para operações com banco\"\"\"
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables():
    \"\"\"Cria todas as tabelas no banco de dados\"\"\"
    engine = get_engine()
    Base.metadata.create_all(engine)
    return True


# MODEL_MAP para mapeamento dinâmico
MODEL_MAP = {{}}


"""


def gerar_model_map(file_class_map):
    """Gera o dicionário MODEL_MAP"""
    linhas = []
    linhas.append("# Mapeamento dinâmico de nome de tabela → Classe")
    linhas.append("MODEL_MAP = {")
    
    for arquivo, info in file_class_map.items():
        class_name = info['class_name']
        table_name = info['table_name']
        # Usar nome da tabela em minúsculas como chave (sem EXPORTACAO_)
        chave = table_name.replace('EXPORTACAO_', '').lower()
        linhas.append(f"    '{chave}': {class_name},")
    
    linhas.append("}")
    
    return '\n'.join(linhas)


def main():
    """Função principal"""
    print("=" * 80)
    print("🔄 GERADOR DINÂMICO DE MODELOS SQLALCHEMY")
    print("=" * 80)
    
    # 1. Verificar se sql_map.json existe
    if not os.path.exists(SQL_MAP_FILE):
        print(f"❌ Arquivo '{SQL_MAP_FILE}' não encontrado!")
        return False
    
    print(f"\n📖 Carregando: {SQL_MAP_FILE}")
    
    # 2. Carregar sql_map.json
    try:
        with open(SQL_MAP_FILE, 'r', encoding='utf-8') as f:
            sql_map = json.load(f)
        print(f"   ✅ {len(sql_map)} entradas carregadas")
    except Exception as e:
        print(f"   ❌ Erro ao carregar: {e}")
        return False
    
    # 3. Gerar modelos
    print(f"\n🔧 Gerando modelos...")
    
    modelos_gerados = []
    model_map_entries = {}
    
    for arquivo, info_arquivo in sql_map.items():
        if arquivo not in FILE_TO_CLASS:
            print(f"   ⚠️  Arquivo '{arquivo}' não mapeado, pulando...")
            continue
        
        class_info = FILE_TO_CLASS[arquivo]
        colunas = info_arquivo.get('colunas', [])
        
        # Gerar modelo
        modelo = gerar_modelo(class_info, colunas)
        modelos_gerados.append(modelo)
        
        # Adicionar ao map
        model_map_entries[arquivo] = class_info
        
        print(f"   ✅ {class_info['class_name']}: {len(colunas)} colunas")
    
    # 4. Construir arquivo completo
    print(f"\n📝 Construindo arquivo de saída...")
    
    conteudo = gerar_imports()
    
    # Adicionar classes
    for modelo in modelos_gerados:
        conteudo += modelo + "\n"
    
    # Adicionar MODEL_MAP
    conteudo += "\n\n" + gerar_model_map(model_map_entries) + "\n"
    
    # Adicionar __all__
    conteudo += "\n\n__all__ = [\n"
    conteudo += "    'Base',\n"
    conteudo += "    'get_engine',\n"
    conteudo += "    'get_session',\n"
    conteudo += "    'create_all_tables',\n"
    conteudo += "    'MODEL_MAP',\n"
    for arquivo, info in model_map_entries.items():
        conteudo += f"    '{info['class_name']}',\n"
    conteudo += "]\n"
    
    # 5. Salvar arquivo
    print(f"\n💾 Salvando: {OUTPUT_FILE}")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"   ✅ Arquivo gerado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao salvar: {e}")
        return False
    
    # 6. Resumo
    print(f"\n✅ MODELOS GERADOS COM SUCESSO!")
    print(f"\n📊 Resumo:")
    print(f"   Arquivo de entrada: {SQL_MAP_FILE}")
    print(f"   Arquivo de saída: {OUTPUT_FILE}")
    print(f"   Total de modelos: {len(modelos_gerados)}")
    print(f"   Total de colunas: {sum(len(info_arquivo.get('colunas', [])) for info_arquivo in sql_map.values())}")
    
    print(f"\n📋 Modelos gerados:")
    for arquivo, info in model_map_entries.items():
        print(f"   • {info['class_name']} → {info['table_name']}")
    
    print(f"\n🚀 Próximo passo:")
    print(f"   → migrate_tables.py usará models_generated.py automaticamente")
    
    return True


if __name__ == '__main__':
    sucesso = main()
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 Operação concluída com sucesso!")
    else:
        print("❌ Operação falhou!")
    print("=" * 80)
