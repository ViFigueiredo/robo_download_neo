# 📋 GUIA RÁPIDO - Script de Migração + Package models/

## 🚀 3 Comandos Principais

### 1️⃣ Criar as Tabelas (PRIMEIRA VEZ)
```bash
python migrate_tables.py
```
**Output esperado:**
```
✅ Tabelas criadas/verificadas com sucesso!

Tabelas criadas:
  • EXPORTACAO_PRODUCAO
  • EXPORTACAO_ATIVIDADE
  • EXPORTACAO_STATUS
```

### 2️⃣ Verificar Status (QUALQUER HORA)
```bash
python migrate_tables.py --status
```
**Output esperado:**
```
✅ EXPORTACAO_PRODUCAO
   Registros: 0
   Colunas: 51

✅ EXPORTACAO_ATIVIDADE
   Registros: 0
   Colunas: 23

✅ EXPORTACAO_STATUS
   Registros: 0
   Colunas: 11
```

### 3️⃣ Remover Tabelas (CUIDADO!)
```bash
python migrate_tables.py --drop
```
**Pede confirmação:**
```
⚠️  CUIDADO! Isso vai DELETAR TODOS OS DADOS!
Digite 'SIM' para confirmar: SIM
```

---

## 📦 Package models/ - Como Usar

### Importação Rápida
```python
# Em app.py ou qualquer lugar
from models import insert_records_sqlalchemy

# Inserir registros
result = insert_records_sqlalchemy(records, 'producao', 'arquivo.xlsx')
print(f"Inseridos: {result['success']}")
print(f"Taxa: {result['taxa_sucesso']:.1f}%")
```

### Importação Detalhada
```python
from models.models import ExportacaoProducao, get_engine, get_session
from models.db_operations import insert_records_sqlalchemy

# Usar modelos diretamente
engine = get_engine()
session = get_session()

# Query customizada
registros = session.query(ExportacaoProducao).all()
session.close()
```

---

## 🗂️ Estrutura Criada

```
robo_download_neo/
├── migrate_tables.py          ← Script de migração (NOVO)
├── models/                    ← Package (NOVO)
│   ├── __init__.py           ← Exports principais
│   ├── models.py             ← 3 modelos ORM
│   ├── db_operations.py      ← Funções de inserção
│   └── README.md             ← Documentação do package
└── ...
```

---

## ⚡ Fluxo Operacional

### 1. Setup (UMA VEZ)
```bash
# Criar tabelas
python migrate_tables.py

# Verificar
python migrate_tables.py --status
```

### 2. Integração (Fase 5)
```python
# Em app.py
from models import insert_records_sqlalchemy, create_all_tables

# Inicializar
create_all_tables()

# Usar
result = insert_records_sqlalchemy(records, 'producao')
```

### 3. Monitoramento
```bash
# Em outro terminal
tail -f logs/sent_records_producao.jsonl
```

---

## 🧪 Validar Funcionalidade

### Teste 1: Script funciona?
```bash
python migrate_tables.py --status
# ✅ Deve mostrar as 3 tabelas
```

### Teste 2: Imports funcionam?
```bash
python -c "from models import insert_records_sqlalchemy; print('✅ OK')"
```

### Teste 3: Inserir dados?
```bash
python -c "
from models import insert_records_sqlalchemy
records = [{'PEDIDO_VINCULO': 'TEST_001', 'ITEM': '1'}]
result = insert_records_sqlalchemy(records, 'producao')
print(f'Inseridos: {result[\"success\"]}')
"
```

---

## 📊 Tipo de Dados

Todas as colunas são **String** no SQL Server:

```
EXPORTACAO_PRODUCAO.PEDIDO_VINCULO     → VARCHAR(500)
EXPORTACAO_PRODUCAO.ITEM               → VARCHAR(MAX)
EXPORTACAO_ATIVIDADE.ATIVIDADE         → VARCHAR(500)
EXPORTACAO_STATUS.NUMERO               → VARCHAR(500)
EXPORTACAO_STATUS.ENTROU               → VARCHAR(500)
```

**Vantagem:** Nenhum problema com NUL characters (0x00) ou tipos incompatíveis

---

## ✅ Checklist

- [x] migrate_tables.py criado
- [x] Package models/ estruturado
- [x] Tabelas criadas no SQL Server
- [x] Script de migração funciona
- [x] Imports estão corretos
- [x] Documentação completa
- [ ] Próxima Fase: Integração com app.py

---

## 🔗 Referências

**Scripts:**
- `migrate_tables.py` - Criar/verificar/remover tabelas

**Package:**
- `models/__init__.py` - Imports principais
- `models/models.py` - Modelos ORM
- `models/db_operations.py` - Operações
- `models/README.md` - Documentação do package

**Documentação:**
- `docs/MIGRACAO_SQLALCHEMY.md` - Completa
- `docs/FASE5_INTEGRACAO_APPPY.md` - Integração
- `RESUMO_FASE_FINAL_SQLALCHEMY.txt` - Resumo

---

**Próxima Fase:** 5 - Integração com app.py  
**Data:** 29 de outubro de 2025  
**Status:** ✅ PRONTO
