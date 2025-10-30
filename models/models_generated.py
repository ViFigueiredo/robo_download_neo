#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modelos SQLAlchemy Gerados Dinamicamente

Este arquivo é gerado automaticamente por gerar_models_dinamicos.py
Não edite manualmente!

Data de geração: 2025-10-30 13:38:50
Fonte: bases/sql_map.json
"""

from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Base para todos os modelos
Base = declarative_base()


def get_engine():
    """Cria engine de conexão ao SQL Server"""
    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_DATABASE', 'rpa_neocrm')
    username_var = os.getenv('DB_USERNAME', 'sa')
    password_var = os.getenv('DB_PASSWORD', '')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
    
    # Connection string
    connection_string = (
        f'mssql+pyodbc://{username_var}:{password_var}@{server}:1434/{database}'
        f'?driver={driver}&TrustServerCertificate=yes'
    )
    
    return create_engine(connection_string, echo=False, pool_pre_ping=True)


def get_session():
    """Cria uma nova session para operações com banco"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables():
    """Cria todas as tabelas no banco de dados"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return True


# MODEL_MAP para mapeamento dinâmico
MODEL_MAP = {}



class ExportacaoProducao(Base):
    """Modelo ORM para tabela EXPORTACAO_PRODUCAO"""
    __tablename__ = 'EXPORTACAO_PRODUCAO'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Campos de dados - SEM constrains, SEM PK, SEM índices únicos
    GRUPO = Column(String(4000))
    FILA = Column(String(4000))
    NUMERO_ATIVIDADE = Column(String(4000))
    PEDIDO_VINCULO = Column(String(4000))
    COTACAO = Column(String(4000))
    ATIVIDADE_ORIGEM = Column(String(4000))
    CODIGO_PORTABILIDADE = Column(String(4000))
    LOGIN_OPERADORA = Column(String(4000))
    NOME_CLIENTE = Column(String(4000))
    CPF_CNPJ = Column(String(4000))
    PF_OU_PJ = Column(String(4000))
    CIDADE_CLIENTE = Column(String(4000))
    ESTADO = Column(String(4000))
    DDD = Column(String(4000))
    PROPRIETARIO_DO_PEDIDO = Column(String(4000))
    TAGS_USUARIO_PEDIDO = Column(String(4000))
    ADM_DO_PEDIDO = Column(String(4000))
    CONSULTOR_NA_OPERADORA = Column(String(4000))
    EQUIPE = Column(String(4000))
    ETAPA_PEDIDO = Column(String(4000))
    CATEGORIA = Column(String(4000))
    SUB_CATEGORIA = Column(String(4000))
    CADASTRO = Column(String(4000))
    ATUALIZACAO = Column(String(4000))
    SOLICITACAO = Column(String(4000))
    TIPO_NEGOCIACAO = Column(String(4000))
    NOTAS_FISCAIS = Column(String(4000))
    REVISAO = Column(String(4000))
    ATIVIDADES = Column(String(4000))
    ITEM = Column(String(4000))
    NUMERO = Column(String(4000))
    NUMERO_PROVISORIO = Column(String(4000))
    ETAPA_ITEM = Column(String(4000))
    PORTABILIDADE = Column(String(4000))
    OPERADORA_CEDENTE = Column(String(4000))
    NOME_CEDENTE = Column(String(4000))
    CPF_CNPJ_CEDENTE = Column(String(4000))
    TELEFONE_CEDENTE = Column(String(4000))
    EMAIL_CEDENTE = Column(String(4000))
    PRODUTO = Column(String(4000))
    VALOR_UNIT = Column(String(4000))
    QUANTIDADE = Column(String(4000))
    DATA_REF = Column(String(4000))
    ORIGEM = Column(String(4000))
    DATA_INSTALACAO = Column(String(4000))
    PERIODO = Column(String(4000))
    CIDADE_INSTALACAO = Column(String(4000))
    UF = Column(String(4000))
    RPON = Column(String(4000))
    INSTANCIA = Column(String(4000))
    TAGS = Column(String(4000))
    DATA_IMPORTACAO = Column(String, nullable=False, default='')

    def __repr__(self):
        return f"<ExportacaoProducao(...)>"

class ExportacaoAtividade(Base):
    """Modelo ORM para tabela EXPORTACAO_ATIVIDADE"""
    __tablename__ = 'EXPORTACAO_ATIVIDADE'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Campos de dados - SEM constrains, SEM PK, SEM índices únicos
    ATIVIDADE = Column(String(4000))
    VINCULADO = Column(String(4000))
    LOGIN = Column(String(4000))
    TIPO = Column(String(4000))
    CPF_CNPJ = Column(String(4000))
    NOME_CLIENTE = Column(String(4000))
    ETAPA = Column(String(4000))
    CATEGORIA = Column(String(4000))
    SUB_CATEGORIA = Column(String(4000))
    PRAZO = Column(String(4000))
    SLA_HORAS = Column(String(4000))
    TEMPO = Column(String(4000))
    ULTIMA_MOV = Column(String(4000))
    TAGS = Column(String(4000))
    USUARIO = Column(String(4000))
    TAG_USUARIO = Column(String(4000))
    EQUIPE = Column(String(4000))
    USUARIO_ADM = Column(String(4000))
    ATIVIDADE_ORIGEM = Column(String(4000))
    CADASTRO = Column(String(4000))
    ATUALIZACAO = Column(String(4000))
    RETORNO_FUTURO = Column(String(4000))
    COMPLEMENTOS = Column(String(4000))
    DATA_IMPORTACAO = Column(String, nullable=False, default='')

    def __repr__(self):
        return f"<ExportacaoAtividade(...)>"

class ExportacaoStatus(Base):
    """Modelo ORM para tabela EXPORTACAO_STATUS
    
    Nota Importante: A tabela Status contém histórico de movimentações.
    Sem restrições de chave primária ou índice único - permite inserir dados livremente.
    """
    __tablename__ = 'EXPORTACAO_STATUS'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Campos de dados - SEM constrains, SEM PK, SEM índices únicos
    NUMERO = Column(String(4000))
    ETAPA = Column(String(4000))
    PRAZO = Column(String(4000))
    SLA_HORAS = Column(String(4000))
    TEMPO = Column(String(4000))
    ENTROU = Column(String(4000))
    USUARIO = Column(String(4000))
    SAIU = Column(String(4000))
    USUARIO_1 = Column(String(4000))
    MOVIMENTACAO = Column(String(4000))
    TAG_ATIVIDADE = Column(String(4000))
    DATA_IMPORTACAO = Column(String, nullable=False, default='')

    def __repr__(self):
        return f"<ExportacaoStatus(NUMERO={self.NUMERO}, ETAPA={self.ETAPA}, ENTROU={self.ENTROU})>"


# Mapeamento dinâmico de nome de tabela → Classe
MODEL_MAP = {
    'producao': ExportacaoProducao,
    'atividade': ExportacaoAtividade,
    'status': ExportacaoStatus,
}


__all__ = [
    'Base',
    'get_engine',
    'get_session',
    'create_all_tables',
    'MODEL_MAP',
    'ExportacaoProducao',
    'ExportacaoAtividade',
    'ExportacaoStatus',
]
