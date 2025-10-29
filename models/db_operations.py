"""
Funções de inserção usando SQLAlchemy ORM

Substitui o insert raw com pyodbc por operações ORM
Usa models_generated.py (dinâmicos) com fallback para models.py (estáticos)
"""
import json
from datetime import datetime
import os
import logging

# Tentar usar models_generated (dinâmicos), fallback para models (estáticos)
try:
    from .models_generated import get_session, MODEL_MAP, Base, get_engine, ExportacaoProducao, ExportacaoAtividade, ExportacaoStatus
    USING_GENERATED = True
except ImportError:
    from .models import get_session, MODEL_MAP, Base, get_engine, ExportacaoProducao, ExportacaoAtividade, ExportacaoStatus
    USING_GENERATED = False

logger = logging.getLogger(__name__)


def insert_records_sqlalchemy(records, table_name='producao', file_name=None):
    """
    Insere registros usando SQLAlchemy ORM
    
    Args:
        records: Lista de dicts com registros
        table_name: Nome da tabela (producao, atividade, status)
        file_name: Nome do arquivo para rastreamento
    
    Returns:
        Dict com estatísticas de sucesso/erro
    """
    # Mapear table_name para model
    model_map = {
        'producao': ExportacaoProducao,
        'atividade': ExportacaoAtividade,
        'status': ExportacaoStatus,
    }
    
    model_class = model_map.get(table_name)
    if not model_class:
        logger.error(f"Tabela '{table_name}' não encontrada no mapa de modelos")
        return {
            'success': 0,
            'failed': len(records),
            'duplicates': 0,
            'total': len(records),
        }
    
    # Mapear nomes de colunas do Excel para nomes do modelo (se necessário)
    # Especialmente para Status que tem colunas com espaços
    column_rename_map = {
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
        'status': {
            'SLA HORAS': 'SLA_HORAS',
            'MOVIMENTAÇÃO': 'MOVIMENTACAO',
            'TAG ATIVIDADE': 'TAG_ATIVIDADE',
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
        }
    }
    
    # Para Status: handle dos dois USUÁRIO (primeiro=ENTRADA, segundo=SAIDA)
    # Isso será feito durante o parse dos records (ver adiante)
    
    # Criar session
    session = get_session()
    
    success_count = 0
    failed_count = 0
    duplicate_count = 0
    error_file = os.path.join('logs', f'error_records_{table_name}.jsonl')
    
    try:
        for idx, record in enumerate(records, 1):
            # Extrair metadados
            line_number = record.pop('_line_number', '?')
            file_name_record = record.pop('_file_name', '?')
            
            # Remover caracteres NUL
            for key, value in record.items():
                if isinstance(value, str):
                    record[key] = value.replace('\x00', '')
            
            # Renomear colunas do Excel para nomes do modelo (se mapa existir)
            rename_map = column_rename_map.get(table_name, {})
            for excel_col, model_col in rename_map.items():
                if excel_col in record:
                    record[model_col] = record.pop(excel_col)
            
            # Filtrar apenas colunas válidas do modelo
            valid_columns = [col.name for col in model_class.__table__.columns]
            record_filtered = {k: v for k, v in record.items() if k in valid_columns}
            
            try:
                # Criar instância do modelo
                obj = model_class(**record_filtered)
                
                # Adicionar DATA_IMPORTACAO automaticamente
                obj.DATA_IMPORTACAO = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Adicionar à session
                session.add(obj)
                session.flush()  # Flush para detectar erros ANTES do commit
                
                success_count += 1
                logger.debug(f"[{table_name}] ✅ Registro {idx} inserido")
                
            except Exception as e:
                # Detectar tipo de erro
                error_str = str(e)
                
                # Duplicata ou constraint violation
                if 'PRIMARY KEY' in error_str or 'UNIQUE' in error_str:
                    session.rollback()
                    duplicate_count += 1
                    
                    logger.debug(
                        f"[{table_name}] ⚠️  DUPLICATA no registro {idx} "
                        f"(Linha {line_number} de {file_name_record}): "
                        f"Chave primária já existe"
                    )
                    
                    # Log do erro
                    with open(error_file, 'a', encoding='utf-8') as ef:
                        ef.write(json.dumps({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'record_num': idx,
                            'table': table_name,
                            'error_type': 'IntegrityError',
                            'error_msg': 'Chave primária duplicada',
                            'source': {
                                'file': file_name_record,
                                'line': line_number
                            },
                            'record': record
                        }, ensure_ascii=False, default=str) + '\n')
                else:
                    # Outro erro
                    session.rollback()
                    failed_count += 1
                    
                    logger.warning(
                        f"[{table_name}] ❌ ERRO ao inserir registro {idx} "
                        f"(Linha {line_number} de {file_name_record}): {type(e).__name__}\n"
                        f"    Detalhes: {str(e)[:150]}"
                    )
                    
                    # Log do erro
                    with open(error_file, 'a', encoding='utf-8') as ef:
                        ef.write(json.dumps({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'record_num': idx,
                            'table': table_name,
                            'error_type': type(e).__name__,
                            'error_msg': str(e)[:200],
                            'source': {
                                'file': file_name_record,
                                'line': line_number
                            },
                            'record': record
                        }, ensure_ascii=False, default=str) + '\n')
        
        # Commit final
        session.commit()
        logger.info(f"[{table_name}] Commit final: {success_count} registros inseridos")
        
    except Exception as e:
        session.rollback()
        logger.error(f"[{table_name}] Erro fatal ao processar batch: {e}")
        failed_count += success_count  # Rollback anula sucesso
        success_count = 0
    
    finally:
        session.close()
    
    # Calcular taxa de sucesso
    total = success_count + failed_count + duplicate_count
    taxa_sucesso = (success_count / total * 100) if total > 0 else 0
    
    logger.info(
        f"[{table_name}] 📊 Resultado: ✅ {success_count} inseridos, "
        f"⚠️  {duplicate_count} duplicatas, ❌ {failed_count} erros | "
        f"Taxa: {taxa_sucesso:.1f}%"
    )
    
    return {
        'success': success_count,
        'failed': failed_count,
        'duplicates': duplicate_count,
        'total': total,
        'taxa_sucesso': taxa_sucesso,
    }


def create_tables():
    """Cria tabelas automaticamente baseado nos modelos"""
    logger.info("Criando tabelas...")
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("✅ Tabelas criadas/verificadas")


if __name__ == '__main__':
    # Teste
    create_tables()
    print("✅ Tudo pronto")
