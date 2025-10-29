"""
Package de modelos SQLAlchemy para Robô Download Neo

Expõe os principais componentes para facilitar imports
Usa models_generated.py (dinâmicos) com fallback para models.py (estáticos)
"""

# Tentar usar models_generated (dinâmicos), fallback para models (estáticos)
try:
    from .models_generated import (
        Base,
        ExportacaoProducao,
        ExportacaoAtividade,
        ExportacaoStatus,
        MODEL_MAP,
        get_engine,
        get_session,
        create_all_tables,
    )
    USING_GENERATED = True
except ImportError:
    from .models import (
        Base,
        ExportacaoProducao,
        ExportacaoAtividade,
        ExportacaoStatus,
        MODEL_MAP,
        get_engine,
        get_session,
        create_all_tables,
    )
    USING_GENERATED = False

from .db_operations import (
    insert_records_sqlalchemy,
    create_tables,
)

__all__ = [
    'Base',
    'ExportacaoProducao',
    'ExportacaoAtividade',
    'ExportacaoStatus',
    'MODEL_MAP',
    'get_engine',
    'get_session',
    'create_all_tables',
    'insert_records_sqlalchemy',
    'create_tables',
    'USING_GENERATED',
]
