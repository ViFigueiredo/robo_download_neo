# 🎯 Tratamento Automático de Colunas Duplicadas

**Data:** 29 de outubro de 2025  
**Status:** ✅ **IMPLEMENTADO E TESTADO**  
**Fase:** 15.1 - Tratamento de Colunas Duplicadas

---

## 📋 Resumo Executivo

O sistema agora detecta automaticamente colunas duplicadas nos arquivos Excel e as renomeia de forma inteligente no banco de dados SQL Server.

**Exemplo Prático (Arquivo Status):**
- **Excel:** Duas colunas com nome "USUÁRIO"
  - Coluna 1: `USUÁRIO`
  - Coluna 2: `USUÁRIO` (Excel auto-renomeia para `USUÁRIO.1`)
  
- **Banco de Dados:** Ambas criadas com nomes diferenciados
  - Coluna 1: `USUARIO`
  - Coluna 2: `USUARIO_1`

---

## 🔍 Como Funciona

### 1. **Detecção de Duplicatas** (`gerar_sql_map_automatico.py`)

```python
def gerar_mapeamento_colunas(colunas_excel, table_name):
    # Step 1: Remover sufixos do Excel (.1, .2)
    excel_col_base = excel_col.rsplit('.', 1)[0] if '.' in excel_col else excel_col
    
    # Step 2: Agrupar colunas idênticas
    colunas_base[excel_col_base] = [todas as variações]
    
    # Step 3: Renomear no banco de dados
    # Primeira: USUARIO (sem sufixo)
    # Resto:    USUARIO_1, USUARIO_2, etc.
```

### 2. **Mapeamento em sql_map.json**

```json
{
  "Exportacao Status.xlsx": {
    "colunas": ["NUMERO", "ETAPA", "USUÁRIO", "USUÁRIO.1", ...],
    "mapeamento_colunas": {
      "NUMERO": "NUMERO",
      "ETAPA": "ETAPA",
      "USUÁRIO": "USUARIO",           ← Primeira ocorrência
      "USUÁRIO.1": "USUARIO_1",       ← Segunda renomeada com _1
      ...
    }
  }
}
```

### 3. **Geração Automática de Modelos** (`gerar_models_dinamicos.py`)

```python
class ExportacaoStatus(Base):
    __tablename__ = 'EXPORTACAO_STATUS'
    
    NUMERO = Column(String(4000), primary_key=True)
    USUARIO = Column(String(4000))      # Primeira coluna
    USUARIO_1 = Column(String(4000))    # Segunda coluna
    MOVIMENTACAO = Column(String(4000))
    # ...
```

### 4. **Sincronização no SQL Server** (`migrate_tables.py`)

```
✅ EXPORTACAO_STATUS
   • NUMERO (PK)
   • ETAPA
   • PRAZO
   • SLA_HORAS
   • TEMPO
   • ENTROU
   • USUARIO         ← Primeira coluna USUÁRIO
   • SAIU
   • USUARIO_1       ← Segunda coluna USUÁRIO.1
   • MOVIMENTACAO
   • TAG_ATIVIDADE
   • DATA_IMPORTACAO
```

---

## 🛠️ Componentes Afetados

### ✅ Scripts Atualizados

| Script | Mudança | Status |
|--------|---------|--------|
| `gerar_sql_map_automatico.py` | Detecta duplicatas + renomeia | ✅ PRONTO |
| `gerar_models_dinamicos.py` | Gera colunas corretas (COL, COL_1) | ✅ PRONTO |
| `migrate_tables.py` | Auto-sincroniza schema | ✅ PRONTO |
| `models_generated.py` | Inclui USUARIO e USUARIO_1 | ✅ GERADO |

### 📊 Arquivo sql_map.json

**Seção Status (Exemplo):**
```json
"Exportacao Status.xlsx": {
  "colunas": [
    "NUMERO", "ETAPA", "PRAZO", "SLA HORAS", "TEMPO",
    "ENTROU", "USUÁRIO", "SAIU", "USUÁRIO.1",
    "MOVIMENTAÇÃO", "TAG ATIVIDADE"
  ],
  "mapeamento_colunas": {
    "NUMERO": "NUMERO",
    "ETAPA": "ETAPA",
    "PRAZO": "PRAZO",
    "SLA HORAS": "SLA_HORAS",
    "TEMPO": "TEMPO",
    "ENTROU": "ENTROU",
    "USUÁRIO": "USUARIO",          ← Primeira
    "USUÁRIO.1": "USUARIO_1",      ← Segunda (renomeada)
    "SAIU": "SAIU",
    "MOVIMENTAÇÃO": "MOVIMENTACAO",
    "TAG ATIVIDADE": "TAG_ATIVIDADE"
  }
}
```

---

## ✅ Testes Realizados

### Teste 1: Geração de sql_map.json
```bash
$ python gerar_sql_map_automatico.py

ExportacaoProducao.xlsx: 51 colunas + 51 mapeamentos ✅
Exportacao Atividade.xlsx: 23 colunas + 23 mapeamentos ✅
Exportacao Status.xlsx: 11 colunas + 11 mapeamentos ✅
✅ sql_map.json salvo com sucesso
```

**Resultado:** Duplicatas detectadas e mapeadas corretamente

### Teste 2: Geração de Modelos
```bash
$ python gerar_models_dinamicos.py

✅ ExportacaoProducao: 51 colunas
✅ ExportacaoAtividade: 23 colunas
✅ ExportacaoStatus: 11 colunas (USUARIO + USUARIO_1)
✅ Modelos gerados com sucesso
```

**Resultado:** Colunas duplicadas incluídas no modelo

### Teste 3: Sincronização de Schema
```bash
$ python migrate_tables.py

✅ EXPORTACAO_PRODUCAO sincronizado com sucesso
✅ EXPORTACAO_ATIVIDADE sincronizado com sucesso
✅ EXPORTACAO_STATUS sincronizado com sucesso
✅ Nenhuma diferença detectada
```

**Resultado:** Tabelas criadas com sucesso

### Teste 4: Verificação de Colunas no SQL Server
```bash
$ python verify_columns.py

📊 Colunas na tabela EXPORTACAO_STATUS:
────────────────────────────────────────
   NUMERO                    varchar
   ETAPA                     varchar
   PRAZO                     varchar
   SLA_HORAS                 varchar
   TEMPO                     varchar
   ENTROU                    varchar
   USUARIO                   varchar   ← Primeira coluna USUÁRIO
   SAIU                      varchar
   USUARIO_1                 varchar   ← Segunda coluna USUÁRIO.1
   MOVIMENTACAO              varchar
   TAG_ATIVIDADE             varchar
   DATA_IMPORTACAO           varchar
────────────────────────────────────────
```

**Resultado:** ✅ Ambas as colunas criadas com nomes diferenciados!

---

## 🔧 Normalização de Nomes

### Acentos
- `USUÁRIO` → `USUARIO`
- `SLA HORAS` → `SLA_HORAS`
- `ÚLTIMA MOV` → `ULTIMA_MOV`

### Espaços
- `NUMERO ATIVIDADE` → `NUMERO_ATIVIDADE`
- `TAG ATIVIDADE` → `TAG_ATIVIDADE`

### Hífens
- `CPF-CNPJ` → `CPF_CNPJ`
- `SUB-CATEGORIA` → `SUB_CATEGORIA`

### Duplicatas
- 1ª coluna: `USUARIO` (sem sufixo)
- 2ª coluna: `USUARIO_1` (com _1)
- 3ª coluna: `USUARIO_2` (com _2)

---

## 🚀 Pipeline Completo

```
┌─────────────────────────────────────────────────────────┐
│ 1. EXCEL FILES (downloads/)                             │
│    - ExportacaoProducao.xlsx                            │
│    - Exportacao Atividade.xlsx                          │
│    - Exportacao Status.xlsx (⚠️ 2x USUÁRIO)             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 2. GERAR_SQL_MAP_AUTOMATICO.PY                          │
│    ✅ Lê colunas do Excel                               │
│    ✅ Detecta duplicatas (USUÁRIO, USUÁRIO.1)          │
│    ✅ Mapeia com renomeação (USUARIO, USUARIO_1)       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 3. SQL_MAP.JSON (bases/)                                │
│    {                                                    │
│      "USUÁRIO": "USUARIO",                              │
│      "USUÁRIO.1": "USUARIO_1"                           │
│    }                                                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 4. GERAR_MODELS_DINAMICOS.PY                            │
│    ✅ Lê sql_map.json                                   │
│    ✅ Gera models_generated.py com ambas as colunas    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 5. MODELS_GENERATED.PY (models/)                        │
│    class ExportacaoStatus(Base):                        │
│        USUARIO = Column(String(4000))                   │
│        USUARIO_1 = Column(String(4000))                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 6. MIGRATE_TABLES.PY                                    │
│    ✅ Cria/sincroniza schema                            │
│    ✅ Aplica ALTER TABLE se necessário                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 7. SQL SERVER (192.168.11.200)                          │
│    EXPORTACAO_STATUS                                    │
│    ├─ NUMERO (PK)                                       │
│    ├─ USUARIO ✅                                        │
│    ├─ USUARIO_1 ✅                                      │
│    └─ ... (outros campos)                               │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Implementação Técnica

### Algoritmo de Detecção de Duplicatas

```python
# 1. Agrupar por base name
colunas_base = {}
for excel_col in colunas_excel:
    # Remove sufixos do Excel (.1, .2)
    excel_col_base = excel_col.rsplit('.', 1)[0] if '.' in excel_col else excel_col
    
    if excel_col_base not in colunas_base:
        colunas_base[excel_col_base] = []
    colunas_base[excel_col_base].append(excel_col)

# 2. Renomear em caso de duplicatas
for base_name, colunas_iguais in colunas_base.items():
    if len(colunas_iguais) > 1:
        # Múltiplas colunas com mesmo nome
        for idx, excel_col in enumerate(colunas_iguais):
            if idx == 0:
                mapeamento[excel_col] = nome_normalizado
            else:
                mapeamento[excel_col] = f"{nome_normalizado}_{idx}"
    else:
        # Única coluna com esse nome
        mapeamento[colunas_iguais[0]] = nome_normalizado
```

### Normalização com Acentos

```python
def normalizar_nome_coluna(nome):
    import unicodedata
    
    # Remove acentos
    nfd = unicodedata.normalize('NFD', nome)
    sem_acentos = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    
    # Substitui espaços e hífens por underscore
    resultado = sem_acentos.replace(' ', '_').replace('-', '_').upper()
    
    return resultado

# Exemplos:
normalizar_nome_coluna("USUÁRIO")        # → USUARIO
normalizar_nome_coluna("SLA HORAS")      # → SLA_HORAS
normalizar_nome_coluna("CPF-CNPJ")       # → CPF_CNPJ
```

---

## 🎯 Resultado Final

**Arquivo Status com Colunas Duplicadas:**

| Excel | Banco de Dados | Tipo |
|-------|----------------|------|
| USUÁRIO | USUARIO | Primeira ocorrência |
| USUÁRIO.1 | USUARIO_1 | Segunda ocorrência |

**Benefícios:**
✅ Ambas as informações preservadas  
✅ Sem perda de dados  
✅ Nomes diferenciados no banco  
✅ Automático e transparente  
✅ Sem intervenção manual necessária  

---

## 📚 Arquivos Relacionados

- `.github/copilot-instructions.md` - Instruções principais
- `docs/ARQUITETURA_E_API.md` - Arquitetura completa
- `gerar_sql_map_automatico.py` - Script de mapeamento
- `gerar_models_dinamicos.py` - Script de geração de modelos
- `migrate_tables.py` - Script de migração
- `models/models_generated.py` - Modelos gerados

---

**Última atualização:** 29 de outubro de 2025
