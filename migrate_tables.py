#!/usr/bin/env python3
"""
Script de Migração de Tabelas - SQLAlchemy

Cria/atualiza todas as tabelas no SQL Server baseado nos modelos ORM
Usa as credenciais do .env para conectar ao banco

Uso:
    python migrate_tables.py                 # Criar/verificar tabelas + sincronizar schema
    python migrate_tables.py --drop          # Remover tabelas (CUIDADO!)
    python migrate_tables.py --status        # Verificar status das tabelas
    python migrate_tables.py --sync-schema   # Sincronizar schema (detectar + atualizar)
    python migrate_tables.py --check-schema  # Verificar diferenças (sem atualizar)
"""

import sys
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Carregar .env PRIMEIRO
load_dotenv()

import logging

# Configurar logging ANTES de usar logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar models ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

# Tentar usar models_generated (dinâmicos), fallback para models (estáticos)
try:
    from models_generated import (
        get_engine, 
        Base, 
        ExportacaoProducao, 
        ExportacaoAtividade, 
        ExportacaoStatus,
        create_all_tables,
        MODEL_MAP
    )
    USING_GENERATED = True
except ImportError:
    logger.warning("⚠️  models_generated.py não encontrado, usando models.py estático")
    from models import (
        get_engine, 
        Base, 
        ExportacaoProducao, 
        ExportacaoAtividade, 
        ExportacaoStatus,
        create_all_tables,
        MODEL_MAP
    )
    USING_GENERATED = False

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def criar_tabelas():
    """Cria todas as tabelas se não existirem"""
    print("\n" + "="*80)
    print("CRIANDO/VERIFICANDO TABELAS")
    print("="*80)
    
    try:
        engine = get_engine()
        logger.info(f"Conectando a: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
        
        # Criar todas as tabelas
        Base.metadata.create_all(engine)
        
        print("✅ Tabelas criadas/verificadas com sucesso!")
        print("\nTabelas criadas:")
        print("  • EXPORTACAO_PRODUCAO")
        print("  • EXPORTACAO_ATIVIDADE")
        print("  • EXPORTACAO_STATUS")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        logger.error(f"Erro ao criar tabelas: {e}", exc_info=True)
        return False


def dropar_tabelas():
    """Remove todas as tabelas (CUIDADO!)"""
    print("\n" + "="*80)
    print("⚠️  REMOVENDO TABELAS")
    print("="*80)
    
    # Confirmação
    resposta = input("\n⚠️  CUIDADO! Isso vai DELETAR TODOS OS DADOS!\n"
                     "Digite 'SIM' para confirmar: ").strip().upper()
    
    if resposta != 'SIM':
        print("❌ Operação cancelada")
        return False
    
    try:
        engine = get_engine()
        logger.info(f"Conectando a: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
        
        # Remover todas as tabelas
        Base.metadata.drop_all(engine)
        
        print("✅ Tabelas removidas com sucesso!")
        print("\nTabelas deletadas:")
        print("  • EXPORTACAO_PRODUCAO")
        print("  • EXPORTACAO_ATIVIDADE")
        print("  • EXPORTACAO_STATUS")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao remover tabelas: {e}")
        logger.error(f"Erro ao remover tabelas: {e}", exc_info=True)
        return False


def verificar_status():
    """Verifica status das tabelas"""
    print("\n" + "="*80)
    print("VERIFICANDO STATUS DAS TABELAS")
    print("="*80)
    
    try:
        from sqlalchemy import text, inspect
        
        engine = get_engine()
        logger.info(f"Conectando a: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
        
        inspector = inspect(engine)
        
        # Tabelas esperadas
        tabelas_esperadas = [
            'EXPORTACAO_PRODUCAO',
            'EXPORTACAO_ATIVIDADE',
            'EXPORTACAO_STATUS'
        ]
        
        print("\nStatus das tabelas:")
        print("-" * 80)
        
        with engine.connect() as conn:
            for tabela in tabelas_esperadas:
                # Verificar se tabela existe
                if tabela in inspector.get_table_names():
                    # Contar registros
                    result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {tabela}"))
                    count = result.fetchone()[0]
                    
                    # Listar colunas
                    columns = inspector.get_columns(tabela)
                    col_count = len(columns)
                    
                    print(f"\n✅ {tabela}")
                    print(f"   Registros: {count:,}")
                    print(f"   Colunas: {col_count}")
                    print(f"   Amostra de colunas: {', '.join([c['name'] for c in columns[:5]])}...")
                else:
                    print(f"\n❌ {tabela} (NÃO EXISTE)")
        
        print("\n" + "-" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        logger.error(f"Erro ao verificar status: {e}", exc_info=True)
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Script de migração de tabelas SQLAlchemy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python migrate_tables.py                 # Criar/verificar tabelas + sincronizar
  python migrate_tables.py --drop          # Remover tabelas
  python migrate_tables.py --status        # Verificar status
  python migrate_tables.py --sync-schema   # Sincronizar schema (detectar + atualizar)
  python migrate_tables.py --check-schema  # Verificar diferenças (sem atualizar)
        """
    )
    
    parser.add_argument('--drop', action='store_true', 
                       help='Remover todas as tabelas (cuidado!)')
    parser.add_argument('--status', action='store_true',
                       help='Verificar status das tabelas')
    parser.add_argument('--sync-schema', action='store_true',
                       help='Sincronizar schema (detectar + atualizar modelos)')
    parser.add_argument('--check-schema', action='store_true',
                       help='Verificar diferenças no schema (sem atualizar)')
    
    args = parser.parse_args()
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  Script de Migração - SQLAlchemy ORM".center(78) + "║")
    if USING_GENERATED:
        print("║" + "  [Usando models_generated.py - DINÂMICO]".center(78) + "║")
    else:
        print("║" + "  [Usando models.py - ESTÁTICO]".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    print(f"\nData: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Conexão: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
    
    # Executar ação apropriada
    if args.drop:
        resultado = dropar_tabelas()
    elif args.status:
        resultado = verificar_status()
    elif args.sync_schema or args.check_schema:
        # Importar sincronizador de schema
        try:
            from sincronizar_schema import SchemaSynchronizer
            
            sync = SchemaSynchronizer(
                check_only=args.check_schema,
                verbose=False
            )
            resultado = sync.sincronizar()
        except ImportError:
            logger.error("❌ sincronizar_schema.py não encontrado")
            resultado = False
    else:
        # Ação padrão: criar tabelas + sincronizar schema
        resultado = criar_tabelas()
        
        # Auto-sincronizar schema após criar tabelas
        if resultado:
            logger.info("\n🔄 Sincronizando schema automaticamente...")
            try:
                from sincronizar_schema import SchemaSynchronizer
                
                sync = SchemaSynchronizer(check_only=False, verbose=False)
                resultado = sync.sincronizar()
            except ImportError:
                logger.warning("⚠️  sincronizar_schema.py não encontrado, pulando sync")
    
    print("\n" + "="*80)
    
    if resultado:
        print("✅ Migração concluída com sucesso!")
        return 0
    else:
        print("❌ Migração falhou!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
