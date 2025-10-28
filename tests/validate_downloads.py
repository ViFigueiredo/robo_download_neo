#!/usr/bin/env python3
"""
Teste de verificação: Confirmar que Status e Atividades baixam corretamente

Uso:
    python tests/validate_downloads.py

Verifica:
    1. Se Exportacao Status.xlsx existe
    2. Se Exportacao Atividades.xlsx existe  
    3. Se são arquivos diferentes (tamanhos ou linhas)
"""

import os
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS_DIR = os.path.join(ROOT, 'downloads')

def main():
    print("=" * 70)
    print("✓ Validação de Downloads")
    print("=" * 70)
    
    # Arquivos esperados
    status_file = os.path.join(DOWNLOADS_DIR, 'Exportacao Status.xlsx')
    atividades_file = os.path.join(DOWNLOADS_DIR, 'Exportacao Atividades.xlsx')
    
    # Verificar existência
    print(f"\n📁 Verificando pasta: {DOWNLOADS_DIR}")
    
    status_exists = os.path.exists(status_file)
    atividades_exists = os.path.exists(atividades_file)
    
    print(f"  • Exportacao Status.xlsx:      {'✅ EXISTE' if status_exists else '❌ NÃO EXISTE'}")
    print(f"  • Exportacao Atividades.xlsx:  {'✅ EXISTE' if atividades_exists else '❌ NÃO EXISTE'}")
    
    if not (status_exists and atividades_exists):
        print("\n❌ Faltam arquivos!")
        return False
    
    # Carregar e verificar conteúdo
    print("\n📊 Analisando conteúdo:")
    
    try:
        df_status = pd.read_excel(status_file)
        df_atividades = pd.read_excel(atividades_file)
        
        print(f"  • Status: {len(df_status)} linhas, {len(df_status.columns)} colunas")
        print(f"  • Atividades: {len(df_atividades)} linhas, {len(df_atividades.columns)} colunas")
        
        # Headers
        print(f"\n  📋 Headers do Status:")
        for col in list(df_status.columns)[:5]:
            print(f"     - {col}")
        print(f"     ... e mais {len(df_status.columns) - 5}")
        
        print(f"\n  📋 Headers do Atividades:")
        for col in list(df_atividades.columns)[:5]:
            print(f"     - {col}")
        print(f"     ... e mais {len(df_atividades.columns) - 5}")
        
        # Verificar se são diferentes
        if df_status.shape == df_atividades.shape and list(df_status.columns) == list(df_atividades.columns):
            print("\n⚠️  AVISO: Status e Atividades parecem ter a mesma estrutura!")
            print("   Pode estar baixando o mesmo arquivo duas vezes!")
            return False
        else:
            print("\n✅ Status e Atividades são estruturalmente diferentes")
            return True
            
    except Exception as e:
        print(f"\n❌ Erro ao analisar: {e}")
        return False

if __name__ == '__main__':
    success = main()
    print("\n" + "=" * 70)
    if success:
        print("✅ VALIDAÇÃO OK: Downloads estão corretos!")
    else:
        print("❌ PROBLEMA: Verifique os downloads!")
    print("=" * 70)
    sys.exit(0 if success else 1)
