#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Sincronização de Schema (Modelos ↔ SQL Server)

Detecta diferenças entre modelos ORM (models_generated.py) e tabelas no SQL Server.
Gera e executa ALTER TABLE automaticamente para manter sincronização.

Uso:
    python sincronizar_schema.py                    # Detectar + atualizar
    python sincronizar_schema.py --check-only       # Apenas detectar diferenças
    python sincronizar_schema.py --generate-sql     # Gerar SQL sem executar
    python sincronizar_schema.py --verbose          # Saída detalhada
"""

import sys
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

# Configurar encoding UTF-8 para Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar .env
load_dotenv()

# Adicionar models ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'models'))

try:
    from sqlalchemy import inspect, text, String, Column
    from models_generated import get_engine, MODEL_MAP, Base
    MODELS_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Erro ao importar modelos: {e}")
    MODELS_AVAILABLE = False


class SchemaSynchronizer:
    """Sincronizador de schema entre modelos ORM e SQL Server"""
    
    def __init__(self, check_only=False, verbose=False):
        self.check_only = check_only
        self.verbose = verbose
        self.engine = None
        self.inspector = None
        self.changes_needed = defaultdict(dict)
        self.warnings = []
        self.errors = []
    
    def conectar(self):
        """Conecta ao SQL Server"""
        try:
            self.engine = get_engine()
            self.inspector = inspect(self.engine)
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"✅ Conectado a: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            self.errors.append(str(e))
            return False
    
    def extrair_colunas_modelo(self, model_class):
        """Extrai informações de colunas do modelo ORM"""
        colunas = {}
        
        for col in model_class.__table__.columns:
            info = {
                'nome': col.name,
                'tipo': str(col.type),
                'nullable': col.nullable,
                'primary_key': col.primary_key,
                'default': col.default,
            }
            colunas[col.name] = info
        
        return colunas
    
    def extrair_colunas_banco(self, table_name):
        """Extrai informações de colunas do SQL Server"""
        colunas = {}
        
        try:
            # Obter colunas da tabela
            columns = self.inspector.get_columns(table_name)
            pk_columns = self.inspector.get_pk_constraint(table_name)['constrained_columns']
            
            for col in columns:
                info = {
                    'nome': col['name'],
                    'tipo': str(col['type']),
                    'nullable': col['nullable'],
                    'primary_key': col['name'] in pk_columns,
                    'default': col.get('default'),
                }
                colunas[col['name']] = info
            
            return colunas
            
        except Exception as e:
            logger.warning(f"⚠️  Erro ao extrair colunas de {table_name}: {e}")
            return {}
    
    def comparar_tipos(self, tipo_modelo, tipo_banco):
        """Compara tipos de dados compatibilidade"""
        # Normalizar nomes de tipo - remover COLLATE e espaços extras
        tipo_modelo_norm = str(tipo_modelo).lower().replace('varchar', 'string').split('(')[0].strip()
        
        # Banco pode ter "VARCHAR COLLATE ..." - remover tudo após COLLATE
        tipo_banco_str = str(tipo_banco).lower()
        if 'collate' in tipo_banco_str:
            tipo_banco_str = tipo_banco_str.split('collate')[0]
        
        tipo_banco_norm = tipo_banco_str.replace('varchar', 'string').split('(')[0].strip()
        
        return tipo_modelo_norm == tipo_banco_norm
    
    def detectar_diferenças(self):
        """Detecta diferenças entre modelos e banco"""
        logger.info("\n🔍 Analisando diferenças...")
        print("-" * 80)
        
        for model_name, model_class in MODEL_MAP.items():
            table_name = model_class.__tablename__
            
            logger.info(f"\n📊 Tabela: {table_name}")
            
            # Extrair colunas
            cols_modelo = self.extrair_colunas_modelo(model_class)
            cols_banco = self.extrair_colunas_banco(table_name)
            
            if not cols_banco:
                logger.warning(f"⚠️  Tabela {table_name} não existe no banco")
                self.changes_needed[table_name]['criar'] = True
                continue
            
            # 1. Colunas novas (no modelo, não no banco)
            colunas_novas = {}
            for col_nome, col_info in cols_modelo.items():
                if col_nome not in cols_banco:
                    colunas_novas[col_nome] = col_info
                    logger.info(f"  ➕ NOVA coluna: {col_nome} ({col_info['tipo']})")
            
            if colunas_novas:
                self.changes_needed[table_name]['add_columns'] = colunas_novas
            
            # 2. Colunas removidas (no banco, não no modelo)
            colunas_removidas = {}
            for col_nome, col_info in cols_banco.items():
                if col_nome not in cols_modelo:
                    colunas_removidas[col_nome] = col_info
                    logger.warning(f"  ❌ REMOVIDA coluna: {col_nome}")
            
            if colunas_removidas:
                self.changes_needed[table_name]['drop_columns'] = colunas_removidas
                self.warnings.append(f"{table_name}: Colunas removidas detectadas (podem ser deletadas)")
            
            # 3. Colunas com tipos diferentes
            tipos_diferentes = {}
            for col_nome in cols_modelo:
                if col_nome in cols_banco:
                    col_modelo = cols_modelo[col_nome]
                    col_banco = cols_banco[col_nome]
                    
                    if not self.comparar_tipos(col_modelo['tipo'], col_banco['tipo']):
                        tipos_diferentes[col_nome] = {
                            'modelo': col_modelo['tipo'],
                            'banco': col_banco['tipo']
                        }
                        logger.warning(f"  ⚠️  TIPO DIFERENTE {col_nome}: "
                                     f"{col_banco['tipo']} → {col_modelo['tipo']}")
            
            if tipos_diferentes:
                self.changes_needed[table_name]['alter_types'] = tipos_diferentes
            
            # 4. Resumo
            if not colunas_novas and not colunas_removidas and not tipos_diferentes:
                logger.info(f"  ✅ {table_name} sincronizado com sucesso")
        
        print("-" * 80)
        return len(self.changes_needed) > 0
    
    def gerar_sql_alteracao(self):
        """Gera scripts SQL para sincronizar"""
        sql_scripts = {}
        
        for table_name, changes in self.changes_needed.items():
            model_class = MODEL_MAP.get(table_name.replace('EXPORTACAO_', '').lower())
            if not model_class:
                # Tentar buscar by table name
                for name, cls in MODEL_MAP.items():
                    if cls.__tablename__ == table_name:
                        model_class = cls
                        break
            
            if not model_class:
                logger.warning(f"⚠️  Modelo não encontrado para {table_name}")
                continue
            
            scripts = []
            
            # Adicionar colunas
            if 'add_columns' in changes:
                for col_nome, col_info in changes['add_columns'].items():
                    # Tipo SQL Server
                    sql_type = self._converter_tipo_sqlserver(col_info['tipo'])
                    nullable_str = "NULL" if col_info['nullable'] else "NOT NULL"
                    
                    # Verificar se é PRIMARY KEY
                    pk_str = " PRIMARY KEY" if col_info['primary_key'] else ""
                    
                    script = (f"ALTER TABLE {table_name} "
                             f"ADD {col_nome} {sql_type} {nullable_str}{pk_str};")
                    scripts.append(script)
                    logger.info(f"  ✅ ADD: {col_nome}")
            
            # Alterar tipos de dados
            if 'alter_types' in changes:
                for col_nome, tipo_info in changes['alter_types'].items():
                    sql_type = self._converter_tipo_sqlserver(tipo_info['modelo'])
                    script = (f"ALTER TABLE {table_name} "
                             f"ALTER COLUMN {col_nome} {sql_type};")
                    scripts.append(script)
                    logger.info(f"  ✅ ALTER: {col_nome} → {sql_type}")
            
            # Remover colunas (com aviso)
            if 'drop_columns' in changes:
                for col_nome in changes['drop_columns']:
                    script = (f"-- ALTER TABLE {table_name} DROP COLUMN {col_nome}; "
                             f"(comentado - revisar antes de executar)")
                    scripts.append(script)
                    logger.warning(f"  ⚠️  DROP (comentado): {col_nome}")
            
            if scripts:
                sql_scripts[table_name] = scripts
        
        return sql_scripts
    
    def _converter_tipo_sqlserver(self, tipo_sqlalchemy):
        """Converte tipo SQLAlchemy para tipo SQL Server"""
        tipo_str = str(tipo_sqlalchemy).lower()
        
        # Mapeamento de tipos
        if 'string' in tipo_str or 'varchar' in tipo_str:
            return "VARCHAR(4000)"
        elif 'integer' in tipo_str or 'int' in tipo_str:
            return "INT"
        elif 'datetime' in tipo_str:
            return "DATETIME"
        elif 'float' in tipo_str or 'numeric' in tipo_str:
            return "FLOAT"
        elif 'boolean' in tipo_str:
            return "BIT"
        else:
            return "VARCHAR(4000)"  # Default
    
    def executar_alteracoes(self, sql_scripts):
        """Executa scripts SQL de sincronização"""
        if self.check_only:
            logger.info("⏭️  Modo --check-only: não executando alterações")
            return True
        
        logger.info("\n⚙️  Executando alterações no SQL Server...")
        print("-" * 80)
        
        total_scripts = sum(len(scripts) for scripts in sql_scripts.values())
        executados = 0
        erros = 0
        
        with self.engine.connect() as conn:
            for table_name, scripts in sql_scripts.items():
                logger.info(f"\n📝 Tabela: {table_name}")
                
                for script in scripts:
                    # Pular scripts comentados (DROP)
                    if script.strip().startswith('--'):
                        logger.warning(f"  ⏭️  Pulando (comentado): {script[:60]}...")
                        continue
                    
                    try:
                        if self.verbose:
                            logger.info(f"  SQL: {script}")
                        
                        conn.execute(text(script))
                        conn.commit()
                        
                        logger.info(f"  ✅ Executado com sucesso")
                        executados += 1
                        
                    except Exception as e:
                        logger.error(f"  ❌ Erro: {e}")
                        erros += 1
                        self.errors.append(f"{table_name}: {str(e)}")
        
        print("-" * 80)
        logger.info(f"\n📊 Resumo: {executados}/{total_scripts} scripts executados")
        
        if erros > 0:
            logger.warning(f"⚠️  {erros} erros encontrados")
        
        return erros == 0
    
    def gerar_relatorio(self):
        """Gera relatório de sincronização"""
        print("\n" + "="*80)
        print("RELATÓRIO DE SINCRONIZAÇÃO DE SCHEMA")
        print("="*80)
        print(f"\nData: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Banco: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}")
        
        if not self.changes_needed:
            print("\n✅ Nenhuma alteração necessária - Schema sincronizado!")
        else:
            print(f"\n📊 Alterações detectadas: {len(self.changes_needed)} tabela(s)")
            
            for table_name, changes in self.changes_needed.items():
                print(f"\n  📋 {table_name}:")
                
                if 'add_columns' in changes:
                    print(f"     ➕ Colunas para adicionar: {len(changes['add_columns'])}")
                    for col in changes['add_columns']:
                        print(f"        • {col}")
                
                if 'alter_types' in changes:
                    print(f"     ⚠️  Colunas para alterar tipo: {len(changes['alter_types'])}")
                    for col in changes['alter_types']:
                        print(f"        • {col}")
                
                if 'drop_columns' in changes:
                    print(f"     ❌ Colunas para remover: {len(changes['drop_columns'])} (comentadas)")
                    for col in changes['drop_columns']:
                        print(f"        • {col}")
        
        if self.warnings:
            print(f"\n⚠️  Avisos ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.errors:
            print(f"\n❌ Erros ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        print("\n" + "="*80)
    
    def sincronizar(self):
        """Executa sincronização completa"""
        if not self.conectar():
            return False
        
        if not self.detectar_diferenças():
            logger.info("✅ Nenhuma diferença detectada")
            self.gerar_relatorio()
            return True
        
        sql_scripts = self.gerar_sql_alteracao()
        
        if not self.check_only:
            logger.info("\n💾 Salvando scripts SQL...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_sql = f"logs/schema_sync_{timestamp}.sql"
            
            os.makedirs("logs", exist_ok=True)
            with open(arquivo_sql, 'w', encoding='utf-8') as f:
                f.write("-- Scripts de Sincronização de Schema\n")
                f.write(f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Banco: {os.getenv('DB_SERVER')}/{os.getenv('DB_DATABASE')}\n\n")
                
                for table_name, scripts in sql_scripts.items():
                    f.write(f"\n-- Tabela: {table_name}\n")
                    for script in scripts:
                        f.write(f"{script}\n")
            
            logger.info(f"✅ Scripts salvos em: {arquivo_sql}")
            
            # Executar
            self.executar_alteracoes(sql_scripts)
        
        self.gerar_relatorio()
        return len(self.errors) == 0


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Sincronizar schema entre modelos ORM e SQL Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python sincronizar_schema.py                    # Detectar + atualizar
  python sincronizar_schema.py --check-only       # Apenas detectar
  python sincronizar_schema.py --generate-sql     # Gerar SQL sem executar
  python sincronizar_schema.py --verbose          # Saída detalhada
        """
    )
    
    parser.add_argument('--check-only', action='store_true',
                       help='Apenas detectar diferenças (não executar)')
    parser.add_argument('--generate-sql', action='store_true',
                       help='Gerar SQL sem executar (salva em logs/)')
    parser.add_argument('--verbose', action='store_true',
                       help='Saída detalhada')
    
    args = parser.parse_args()
    
    if not MODELS_AVAILABLE:
        print("❌ Modelos não disponíveis")
        return 1
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  Sincronizador de Schema - Modelos ↔ SQL Server".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    sync = SchemaSynchronizer(
        check_only=args.check_only or args.generate_sql,
        verbose=args.verbose
    )
    
    resultado = sync.sincronizar()
    
    return 0 if resultado else 1


if __name__ == '__main__':
    sys.exit(main())
