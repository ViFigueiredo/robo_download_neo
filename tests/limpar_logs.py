"""
🧪 Teste da função limpar_logs()
Demonstra o funcionamento da limpeza de logs antes de executar
"""

import os
from pathlib import Path
from datetime import datetime

# Simular a função do app.py
def limpar_logs():
    """
    🔧 NOVO (Fase 10): Limpa pasta \logs antes de cada execução
    Mantém arquivo robo_download.log para histórico, remove error_records_*.jsonl e sent_records_*.jsonl
    """
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print("❌ Pasta logs não encontrada")
        return 0
    
    removidos = 0
    
    # Arquivos que SEMPRE podem ser removidos (logs de execução anterior)
    patterns_remover = [
        'error_records_*.jsonl',      # Logs de erros da execução anterior
        'sent_records_*.jsonl',        # Logs de envios da execução anterior
    ]
    
    print("\n" + "=" * 70)
    print("🧹 LIMPEZA DE LOGS")
    print("=" * 70)
    
    for pattern in patterns_remover:
        for arquivo in logs_dir.glob(pattern):
            try:
                tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
                arquivo.unlink()
                print(f"🗑️  Removido: {arquivo.name} ({tamanho_mb:.2f} MB)")
                removidos += 1
            except Exception as e:
                print(f"⚠️  Erro ao remover {arquivo.name}: {e}")
    
    if removidos > 0:
        print(f"\n✅ Limpeza concluída: {removidos} arquivo(s) removido(s)")
    else:
        print(f"\n✅ Nenhum arquivo para limpar (logs já estão limpos)")
    
    print("=" * 70 + "\n")
    
    return removidos


def verificar_estado_logs():
    """Mostra o estado atual dos logs"""
    logs_dir = Path('logs')
    
    print("\n📂 ESTADO ATUAL DOS LOGS")
    print("=" * 70)
    
    if not logs_dir.exists():
        print("❌ Pasta logs não encontrada")
        return
    
    arquivos = sorted(logs_dir.glob('*'))
    
    if not arquivos:
        print("📭 Pasta logs está vazia")
    else:
        total_mb = 0
        for arquivo in arquivos:
            tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
            data_mod = datetime.fromtimestamp(arquivo.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {arquivo.name:40s} {tamanho_mb:8.2f} MB   {data_mod}")
            total_mb += tamanho_mb
        
        print(f"\n  {'TOTAL':40s} {total_mb:8.2f} MB")
    
    print("=" * 70)


# Executar teste
if __name__ == '__main__':
    print("\n🧪 TESTE DE LIMPEZA DE LOGS")
    print("=" * 70)
    
    # Estado antes
    print("\n📊 ANTES DA LIMPEZA:")
    verificar_estado_logs()
    
    # Executar limpeza
    removidos = limpar_logs()
    
    # Estado depois
    print("\n📊 DEPOIS DA LIMPEZA:")
    verificar_estado_logs()
    
    # Resumo
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO COM SUCESSO")
    print(f"   Total removido: {removidos} arquivo(s)")
    print("=" * 70)
