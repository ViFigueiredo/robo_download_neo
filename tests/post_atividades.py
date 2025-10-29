#!/usr/bin/env python3
"""
🧪 TESTE POST - ATIVIDADES COM SQLALCHEMY (v2)

Testa o envio de registros de Atividades para SQL Server via SQLAlchemy ORM.
Utiliza apenas as colunas definidas no modelo ORM.

Features:
  - Teste com dados reais parseados de Excel
  - Validação de NUL character handling
  - Teste de duplicatas (PRIMARY KEY: ATIVIDADE)
  - Teste de batch processing
  - DRY_RUN mode para validação sem gravar
  - Logging estruturado

Uso:
  python tests/test_post_atividades_v2.py                    # Test com dados mock
  python tests/test_post_atividades_v2.py --dry-run          # Validar sem gravar
  python tests/test_post_atividades_v2.py --batch-size 10    # Tamanho de batch customizado
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import insert_records_sqlalchemy
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def gerar_dados_mock_atividades(quantidade=50):
    """Gerar dados mock de Atividades para teste (23 campos ExportacaoAtividade)."""
    logger.info(f"📦 Gerando {quantidade} registros mock de Atividades...")
    
    records = []
    for i in range(1, quantidade + 1):
        record = {
            # Colunas do modelo ExportacaoAtividade
            'ATIVIDADE': f'ATI-{i:06d}',  # PRIMARY KEY
            'VINCULADO': f'VIN-{i % 10}',
            'LOGIN': f'user{i % 5}',
            'TIPO': f'TIPO-{i % 3}',
            'CPF_CNPJ': f'{i:011d}',
            'NOME_CLIENTE': f'Cliente {i}',
            'ETAPA': f'Etapa-{i % 5}',
            'CATEGORIA': f'CAT-{i % 5}',
            'SUB_CATEGORIA': 'SubCat-A',
            'PRAZO': f'2025-11-{(i % 28) + 1:02d}',
            'SLA_HORAS': '48',
            'TEMPO': f'{i * 10}min',
            'ULTIMA_MOV': f'2025-10-29 {(i % 24):02d}:00:00',
            'TAGS': f'tag{i % 5}',
            'USUARIO': f'user{i % 10}',
            'TAG_USUARIO': f'tag-user-{i}',
            'EQUIPE': f'EQUIPE-{i % 3}',
            'USUARIO_ADM': f'admin{i % 4}',
            'ATIVIDADE_ORIGEM': f'ATI-ORIG-{i}',
            'CADASTRO': f'2025-10-{(i % 28) + 1:02d}',
            'ATUALIZACAO': f'2025-10-29 {(i % 24):02d}:00:00',
            'RETORNO_FUTURO': 'Não',
            'COMPLEMENTOS': f'Complemento {i}',
            '_line_number': i + 1,
            '_file_name': 'Exportacao Atividade.xlsx'
        }
        records.append(record)
    
    return records


def testar_atividades_simples(dry_run=False, batch_size=25):
    """Teste simples com dados mock."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 1: Atividades com Dados Mock")
    logger.info("="*80)
    
    records = gerar_dados_mock_atividades(quantidade=50)
    
    # Faixa única para este teste: 100001-100050
    for i, rec in enumerate(records, 1):
        rec['ATIVIDADE'] = f'ATI-{i+100000:06d}'
    
    logger.info(f"Total de registros: {len(records)}")
    
    os.environ['DRY_RUN'] = 'true' if dry_run else 'false'
    os.environ['BATCH_SIZE'] = str(batch_size)
    
    logger.info(f"DRY_RUN: {dry_run}, BATCH_SIZE: {batch_size}")
    
    stats = insert_records_sqlalchemy(
        records=records,
        table_name='atividade',
        file_name='Exportacao Atividade.xlsx'
    )
    
    logger.info("\n📊 RESULTADOS DO TESTE 1:")
    logger.info(f"  Sucesso: {stats['success']}")
    logger.info(f"  Falhas: {stats['failed']}")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Taxa de sucesso: {stats['success']/stats['total']*100:.1f}%")
    
    return stats['success'] > 0


def testar_atividades_com_duplicatas(dry_run=False, batch_size=25):
    """Teste com duplicatas para validar detecção (PK: ATIVIDADE)."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 2: Atividades com Duplicatas (PRIMARY KEY: ATIVIDADE)")
    logger.info("="*80)
    
    records = gerar_dados_mock_atividades(quantidade=30)
    
    # Faixa única para este teste: 200001-200030
    for i, rec in enumerate(records, 1):
        rec['ATIVIDADE'] = f'ATI-{i+200000:06d}'
    
    # Adicionar alguns registros duplicados (mesma PK: ATIVIDADE)
    duplicata = records[0].copy()
    duplicata['_line_number'] = 999
    records.append(duplicata)
    records.append(duplicata)
    
    logger.info(f"Total de registros (com duplicatas): {len(records)}")
    logger.info(f"  - Únicos: {len(records) - 2}")
    logger.info(f"  - Duplicatas: 2")
    
    os.environ['DRY_RUN'] = 'true' if dry_run else 'false'
    os.environ['BATCH_SIZE'] = str(batch_size)
    
    stats = insert_records_sqlalchemy(
        records=records,
        table_name='atividade',
        file_name='Exportacao Atividade.xlsx'
    )
    
    logger.info("\n📊 RESULTADOS DO TESTE 2:")
    logger.info(f"  Sucesso: {stats['success']}")
    logger.info(f"  Falhas (duplicatas): {stats['failed']}")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Taxa de sucesso (sem duplicatas): {stats['success']/(stats['total']-2)*100:.1f}%")
    
    return stats['success'] >= 28


def testar_atividades_nul_character(dry_run=False, batch_size=25):
    """Teste com NUL character."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 3: Atividades com NUL Character (0x00)")
    logger.info("="*80)
    
    records = gerar_dados_mock_atividades(quantidade=20)
    
    # Faixa única para este teste: 300001-300020
    for i, rec in enumerate(records, 1):
        rec['ATIVIDADE'] = f'ATI-{i+300000:06d}'
    
    records[0]['NOME_CLIENTE'] = 'Nome\x00com\x00NUL'
    records[5]['COMPLEMENTOS'] = 'Complement\x00quebrado'
    records[10]['TAGS'] = 'tag\x00inv\x00alido'
    
    logger.info(f"Total de registros: {len(records)}")
    logger.info(f"Registros com NUL character: 3")
    
    os.environ['DRY_RUN'] = 'true' if dry_run else 'false'
    os.environ['BATCH_SIZE'] = str(batch_size)
    
    stats = insert_records_sqlalchemy(
        records=records,
        table_name='atividade',
        file_name='Exportacao Atividade.xlsx'
    )
    
    logger.info("\n📊 RESULTADOS DO TESTE 3:")
    logger.info(f"  Sucesso: {stats['success']}")
    logger.info(f"  Falhas: {stats['failed']}")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Taxa de sucesso: {stats['success']/stats['total']*100:.1f}%")
    
    return stats['success'] == 20


def testar_atividades_batch_grande(dry_run=False, batch_size=100):
    """Teste com batch grande."""
    logger.info("\n" + "="*80)
    logger.info("🧪 TESTE 4: Atividades com Batch Grande (500 registros)")
    logger.info("="*80)
    
    records = gerar_dados_mock_atividades(quantidade=500)
    
    # Faixa única para este teste: 400001-400500
    for i, rec in enumerate(records, 1):
        rec['ATIVIDADE'] = f'ATI-{i+400000:06d}'
    
    logger.info(f"Total de registros: {len(records)}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Número de batches: {len(records) // batch_size + 1}")
    
    os.environ['DRY_RUN'] = 'true' if dry_run else 'false'
    os.environ['BATCH_SIZE'] = str(batch_size)
    
    import time
    start = time.time()
    
    stats = insert_records_sqlalchemy(
        records=records,
        table_name='atividade',
        file_name='Exportacao Atividade.xlsx'
    )
    
    elapsed = time.time() - start
    records_per_sec = stats['success'] / elapsed if elapsed > 0 else 0
    
    logger.info("\n📊 RESULTADOS DO TESTE 4:")
    logger.info(f"  Sucesso: {stats['success']}")
    logger.info(f"  Falhas: {stats['failed']}")
    logger.info(f"  Total: {stats['total']}")
    logger.info(f"  Taxa de sucesso: {stats['success']/stats['total']*100:.1f}%")
    logger.info(f"  Tempo decorrido: {elapsed:.2f}s")
    logger.info(f"  Registros/segundo: {records_per_sec:.0f}")
    
    return stats['success'] >= 475


def main():
    """Executar testes de POST para Atividades."""
    parser = argparse.ArgumentParser(
        description='Teste de POST para Atividades com SQLAlchemy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python tests/test_post_atividades_v2.py                    # Todos os testes
  python tests/test_post_atividades_v2.py --dry-run          # Apenas validação
  python tests/test_post_atividades_v2.py --batch-size 50    # Customizar batch size
  python tests/test_post_atividades_v2.py --test 1           # Teste específico
        """
    )
    
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Validar sem gravar no banco de dados')
    parser.add_argument('--batch-size', type=int, default=25,
                        help='Tamanho do batch (padrão: 25)')
    parser.add_argument('--test', type=int, default=None,
                        help='Executar teste específico (1-4)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("🧪 SUITE DE TESTES - POST ATIVIDADES COM SQLALCHEMY (v2)")
    print(f"{'='*80}")
    
    results = []
    
    try:
        if args.test is None or args.test == 1:
            logger.info("\n[1/4] Executando Teste 1...")
            result = testar_atividades_simples(
                dry_run=args.dry_run,
                batch_size=args.batch_size
            )
            results.append(("Teste 1: Dados Mock", result))
        
        if args.test is None or args.test == 2:
            logger.info("\n[2/4] Executando Teste 2...")
            result = testar_atividades_com_duplicatas(
                dry_run=args.dry_run,
                batch_size=args.batch_size
            )
            results.append(("Teste 2: Duplicatas", result))
        
        if args.test is None or args.test == 3:
            logger.info("\n[3/4] Executando Teste 3...")
            result = testar_atividades_nul_character(
                dry_run=args.dry_run,
                batch_size=args.batch_size
            )
            results.append(("Teste 3: NUL Character", result))
        
        if args.test is None or args.test == 4:
            logger.info("\n[4/4] Executando Teste 4...")
            result = testar_atividades_batch_grande(
                dry_run=args.dry_run,
                batch_size=args.batch_size
            )
            results.append(("Teste 4: Batch Grande", result))
    
    except Exception as e:
        logger.error(f"❌ Erro durante execução dos testes: {e}", exc_info=True)
        return 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status} - {name}")
    
    print(f"\n📈 Taxa de sucesso: {passed}/{total} ({int(passed/total*100)}%)")
    
    if passed == total:
        print("\n✨ TODOS OS TESTES PASSARAM! ✅")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == '__main__':
    sys.exit(main())
