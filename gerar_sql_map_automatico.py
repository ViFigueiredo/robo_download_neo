#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para gerar/atualizar sql_map.json automaticamente

Lê arquivos Excel em \downloads, mapeia as colunas e cria/atualiza sql_map.json
mantendo o mesmo formato.

Uso:
    python gerar_sql_map_automatico.py
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuração
DOWNLOADS_DIR = 'downloads'
SQL_MAP_FILE = 'bases/sql_map.json'

# Nomes esperados dos arquivos
EXPECTED_FILES = {
    'ExportacaoProducao.xlsx': 'producao',
    'Exportacao Atividade.xlsx': 'atividade',
    'Exportacao Status.xlsx': 'status',
}

# Mapeamento de nomes de colunas do Excel → Modelo (já conhecido)
COLUMN_MAPPINGS = {
    'producao': {
        'NUMERO ATIVIDADE': 'NUMERO_ATIVIDADE',
        'PEDIDO VINCULO': 'PEDIDO_VINCULO',
        'COTAÇÃO': 'COTACAO',
        'ATIVIDADE ORIGEM': 'ATIVIDADE_ORIGEM',
        'CODIGO PORTABILIDADE': 'CODIGO_PORTABILIDADE',
        'LOGIN OPERADORA': 'LOGIN_OPERADORA',
        'NOME CLIENTE': 'NOME_CLIENTE',
        'CPF/CNPJ': 'CPF_CNPJ',
        'PF OU PJ': 'PF_OU_PJ',
        'CIDADE CLIENTE': 'CIDADE_CLIENTE',
        'PROPRIETÁRIO DO PEDIDO': 'PROPRIETARIO_DO_PEDIDO',
        'TAGS USUARIO PEDIDO': 'TAGS_USUARIO_PEDIDO',
        'ADM DO PEDIDO': 'ADM_DO_PEDIDO',
        'CONSULTOR NA OPERADORA': 'CONSULTOR_NA_OPERADORA',
        'ETAPA PEDIDO': 'ETAPA_PEDIDO',
        'SUB-CATEGORIA': 'SUB_CATEGORIA',
        'TIPO NEGOCIACAO': 'TIPO_NEGOCIACAO',
        'NOTAS FISCAIS': 'NOTAS_FISCAIS',
        'NUMERO PROVISORIO': 'NUMERO_PROVISORIO',
        'ETAPA ITEM': 'ETAPA_ITEM',
        'OPERADORA CEDENTE': 'OPERADORA_CEDENTE',
        'NOME CEDENTE': 'NOME_CEDENTE',
        'CPF CNPJ CEDENTE': 'CPF_CNPJ_CEDENTE',
        'TELEFONE CEDENTE': 'TELEFONE_CEDENTE',
        'EMAIL CEDENTE': 'EMAIL_CEDENTE',
        'VALOR UNIT': 'VALOR_UNIT',
        'DATA REF': 'DATA_REF',
        'DATA INSTALAÇÃO': 'DATA_INSTALACAO',
        'CIDADE INSTALAÇÃO': 'CIDADE_INSTALACAO',
    },
    'atividade': {
        'CPF-CNPJ': 'CPF_CNPJ',
        'NOME CLIENTE': 'NOME_CLIENTE',
        'SUB-CATEGORIA': 'SUB_CATEGORIA',
        'SLA HORAS': 'SLA_HORAS',
        'ÚLTIMA MOV': 'ULTIMA_MOV',
        'TAG USUÁRIO': 'TAG_USUARIO',
        'USUÁRIO ADM': 'USUARIO_ADM',
        'ATIVIDADE ORIGEM': 'ATIVIDADE_ORIGEM',
        'RETORNO FUTURO': 'RETORNO_FUTURO',
    },
    'status': {
        'SLA HORAS': 'SLA_HORAS',
        'MOVIMENTAÇÃO': 'MOVIMENTACAO',
        'TAG ATIVIDADE': 'TAG_ATIVIDADE',
        'USUÁRIO': 'USUARIO',  # Primeira ocorrência (entrada)
    }
}


def normalizar_nome_coluna(col_name):
    """
    Normaliza nome de coluna para comparação
    Remove espaços extras, acentos, lowercase
    """
    import unicodedata
    
    # Remover acentos
    col_name = ''.join(
        c for c in unicodedata.normalize('NFD', col_name)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Normalizar: strip, uppercase, espaços extras
    return ' '.join(col_name.strip().split()).upper()


def ler_arquivo_excel(filepath):
    """Lê arquivo Excel e retorna lista de nomes de colunas"""
    try:
        df = pd.read_excel(filepath, nrows=0)  # Lê apenas cabeçalho
        colunas = df.columns.tolist()
        print(f"   ✅ {len(colunas)} colunas lidas")
        return colunas
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return None


def gerar_mapeamento_colunas(colunas_excel, table_name):
    """
    Gera mapeamento de colunas baseado em nomes conhecidos
    Detecta colunas duplicadas (incluso Excel.1, Excel.2) e renomeia automaticamente no banco
    
    Args:
        colunas_excel: Lista de nomes de colunas do Excel
        table_name: Nome da tabela (producao, atividade, status)
    
    Returns:
        Dict com mapeamento de colunas (excel_col -> nome_no_banco)
    """
    mapeamento = {}
    mapping_base = COLUMN_MAPPINGS.get(table_name, {})
    
    # Detectar duplicatas incluindo Excel.1, Excel.2, etc
    # Exemplo: "USUÁRIO", "USUÁRIO.1", "USUÁRIO.2"
    colunas_base = {}  # Mapeamento de base -> lista de variações
    
    for excel_col in colunas_excel:
        # Remover sufixo .1, .2, etc que Excel adiciona
        excel_col_base = excel_col.rsplit('.', 1)[0] if '.' in excel_col else excel_col
        
        if excel_col_base not in colunas_base:
            colunas_base[excel_col_base] = []
        colunas_base[excel_col_base].append(excel_col)
    
    # Processar mapeamento com suporte a duplicatas
    for excel_col_base, colunas_iguais in colunas_base.items():
        # Procurar correspondência no mapeamento conhecido (usar base sem sufixo)
        excel_col_norm = normalizar_nome_coluna(excel_col_base)
        nome_banco = None
        
        for mapa_excel, mapa_model in mapping_base.items():
            if normalizar_nome_coluna(mapa_excel) == excel_col_norm:
                nome_banco = mapa_model
                break
        
        # Se encontrou mapeamento, usar para todas as colunas iguais
        if nome_banco:
            if len(colunas_iguais) == 1:
                # Coluna única, usar o nome mapeado normalmente
                mapeamento[colunas_iguais[0]] = nome_banco
            else:
                # Colunas duplicadas, renomear com sufixo
                for idx, excel_col in enumerate(colunas_iguais):
                    if idx == 0:
                        # Primeira ocorrência usa nome sem sufixo
                        mapeamento[excel_col] = nome_banco
                    else:
                        # Próximas ocorrências recebem sufixo _1, _2, etc
                        mapeamento[excel_col] = f"{nome_banco}_{idx}"
        else:
            # Sem mapeamento conhecido, usar o nome normalizado
            nome_padrao = normalizar_nome_coluna(excel_col_base).replace(' ', '_')
            if len(colunas_iguais) == 1:
                mapeamento[colunas_iguais[0]] = nome_padrao
            else:
                for idx, excel_col in enumerate(colunas_iguais):
                    if idx == 0:
                        mapeamento[excel_col] = nome_padrao
                    else:
                        mapeamento[excel_col] = f"{nome_padrao}_{idx}"
    
    return mapeamento


def carregar_sql_map_existente():
    """Carrega sql_map.json existente, se houver"""
    if os.path.exists(SQL_MAP_FILE):
        try:
            with open(SQL_MAP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Erro ao carregar sql_map.json existente: {e}")
            return {}
    return {}


def salvar_sql_map(sql_map):
    """Salva sql_map.json com formatação bonita"""
    os.makedirs(os.path.dirname(SQL_MAP_FILE), exist_ok=True)
    
    try:
        with open(SQL_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(sql_map, f, ensure_ascii=False, indent=2)
        print(f"✅ sql_map.json salvo com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar sql_map.json: {e}")
        return False


def processar_arquivo(filepath, table_name):
    """
    Processa um arquivo Excel e retorna entrada para sql_map
    
    Args:
        filepath: Caminho para o arquivo
        table_name: Nome da tabela
    
    Returns:
        Dict com entrada sql_map ou None
    """
    print(f"\n📄 Processando: {os.path.basename(filepath)}")
    
    # Ler colunas
    colunas = ler_arquivo_excel(filepath)
    if colunas is None:
        return None
    
    # Gerar mapeamento
    mapeamento = gerar_mapeamento_colunas(colunas, table_name)
    
    # Criar entrada sql_map
    entrada = {
        'colunas': colunas,
        'mapeamento_colunas': mapeamento,
        'processado_em': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_colunas': len(colunas),
        'total_mapeamentos': len(mapeamento),
    }
    
    print(f"   📊 Colunas: {len(colunas)}")
    print(f"   🔄 Mapeamentos: {len(mapeamento)}")
    
    if mapeamento:
        print(f"   Exemplos:")
        for i, (excel_col, model_col) in enumerate(list(mapeamento.items())[:3]):
            print(f"      • '{excel_col}' → '{model_col}'")
        if len(mapeamento) > 3:
            print(f"      ... e mais {len(mapeamento) - 3}")
    
    return entrada


def main():
    """Função principal"""
    print("=" * 80)
    print("🔄 GERADOR AUTOMÁTICO DE SQL_MAP.JSON")
    print("=" * 80)
    
    # 1. Verificar se downloads/ existe
    if not os.path.isdir(DOWNLOADS_DIR):
        print(f"❌ Pasta '{DOWNLOADS_DIR}' não encontrada!")
        return False
    
    print(f"\n📂 Lendo arquivos em: {os.path.abspath(DOWNLOADS_DIR)}/")
    
    # 2. Listar arquivos
    arquivos_encontrados = {}
    for filename, table_name in EXPECTED_FILES.items():
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(filepath):
            arquivos_encontrados[filepath] = (filename, table_name)
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️  {filename} (não encontrado)")
    
    if not arquivos_encontrados:
        print("\n❌ Nenhum arquivo Excel encontrado em downloads/!")
        return False
    
    # 3. Carregar sql_map existente
    print(f"\n📖 Carregando sql_map existente...")
    sql_map = carregar_sql_map_existente()
    
    # 4. Processar cada arquivo
    print(f"\n🔍 Processando arquivos...")
    for filepath, (filename, table_name) in arquivos_encontrados.items():
        entrada = processar_arquivo(filepath, table_name)
        if entrada:
            # Atualizar ou criar chave (usar nome do arquivo como chave)
            sql_map[filename] = entrada
    
    # 5. Salvar sql_map
    print(f"\n💾 Salvando resultados...")
    if salvar_sql_map(sql_map):
        print(f"\n✅ SQL_MAP ATUALIZADO COM SUCESSO!")
        print(f"\n📊 Resumo:")
        print(f"   Total de arquivos processados: {len(arquivos_encontrados)}")
        print(f"   Total de entradas em sql_map.json: {len(sql_map)}")
        
        # Mostrar preview
        print(f"\n📋 Preview do sql_map.json:")
        print(json.dumps(sql_map, ensure_ascii=False, indent=2)[:500] + "...")
        
        return True
    else:
        return False


if __name__ == '__main__':
    sucesso = main()
    print("\n" + "=" * 80)
    if sucesso:
        print("🎉 Operação concluída com sucesso!")
    else:
        print("❌ Operação falhou!")
    print("=" * 80)
