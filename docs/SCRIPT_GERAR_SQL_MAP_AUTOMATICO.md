# 🔄 Script: Gerar SQL_MAP Automático

**Arquivo:** `gerar_sql_map_automatico.py`

---

## 📋 O Que Faz

Este script **automaticamente**:

1. ✅ Lê arquivos Excel em `\downloads`
2. ✅ Extrai os nomes de colunas de cada arquivo
3. ✅ Mapeia nomes de colunas (Excel com espaços → Modelo com underscores)
4. ✅ Cria ou atualiza `bases/sql_map.json`
5. ✅ Mantém o mesmo formato do sql_map.json original

---

## 🚀 Como Usar

### Opção 1: Linha de Comando Simples

```bash
python gerar_sql_map_automatico.py
```

### Opção 2: Com Output Detalhado

```bash
python gerar_sql_map_automatico.py 2>&1 | tee log_sql_map_update.txt
```

---

## 📂 Pré-requisitos

### Arquivos Esperados em `\downloads`

```
downloads/
├── ExportacaoProducao.xlsx      ✅ Obrigatório
├── Exportacao Atividade.xlsx    ✅ Obrigatório
└── Exportacao Status.xlsx       ✅ Obrigatório
```

### Pasta `\bases` Deve Existir

```
bases/
└── (sql_map.json será criado/atualizado aqui)
```

---

## 📊 O Que Gera

O script cria/atualiza `bases/sql_map.json` com este formato:

```json
{
  "ExportacaoProducao.xlsx": {
    "colunas": [
      "GRUPO",
      "FILA",
      "NUMERO ATIVIDADE",
      ...
    ],
    "mapeamento_colunas": {
      "NUMERO ATIVIDADE": "NUMERO_ATIVIDADE",
      "COTAÇÃO": "COTACAO",
      ...
    },
    "processado_em": "2025-10-29 17:24:57",
    "total_colunas": 51,
    "total_mapeamentos": 29
  },
  "Exportacao Atividade.xlsx": { ... },
  "Exportacao Status.xlsx": { ... }
}
```

---

## ⚙️ Funcionalidades

### ✅ Leitura Inteligente

- Lê apenas cabeçalhos dos arquivos (rápido!)
- Suporta arquivos grandes (não carrega dados)
- Normaliza nomes de colunas para comparação

### ✅ Mapeamento Automático

- Mapeia colunas com **espaços** → underscores
- Mapeia colunas com **hífens** → underscores
- Remove **acentos** automaticamente
- Usa lista predefinida de mapeamentos conhecidos

### ✅ Flexibilidade

- Preserva dados existentes em sql_map.json
- Atualiza apenas entradas dos arquivos processados
- Adiciona timestamp de processamento
- Conta total de mapeamentos para referência

---

## 🔍 Exemplo de Output

```
================================================================================
🔄 GERADOR AUTOMÁTICO DE SQL_MAP.JSON
================================================================================

📂 Lendo arquivos em: C:\...\robo_download_neo\downloads/

   ✅ ExportacaoProducao.xlsx
   ✅ Exportacao Atividade.xlsx
   ✅ Exportacao Status.xlsx

📖 Carregando sql_map existente...

🔍 Processando arquivos...

📄 Processando: ExportacaoProducao.xlsx
   ✅ 51 colunas lidas
   📊 Colunas: 51
   🔄 Mapeamentos: 29
   Exemplos:
      • 'NUMERO ATIVIDADE' → 'NUMERO_ATIVIDADE'
      • 'COTAÇÃO' → 'COTACAO'
      ... e mais 26

📄 Processando: Exportacao Atividade.xlsx
   ✅ 23 colunas lidas
   📊 Colunas: 23
   🔄 Mapeamentos: 9

📄 Processando: Exportacao Status.xlsx
   ✅ 11 colunas lidas
   📊 Colunas: 11
   🔄 Mapeamentos: 3

💾 Salvando resultados...
✅ sql_map.json salvo com sucesso

✅ SQL_MAP ATUALIZADO COM SUCESSO!

📊 Resumo:
   Total de arquivos processados: 3
   Total de entradas em sql_map.json: 3

================================================================================
🎉 Operação concluída com sucesso!
================================================================================
```

---

## 🔧 Configuração (Customização)

### Alterar Diretórios

Editar no topo do arquivo:

```python
DOWNLOADS_DIR = 'downloads'  # Pasta de entrada
SQL_MAP_FILE = 'bases/sql_map.json'  # Arquivo de saída
```

### Alterar Nomes de Arquivos Esperados

```python
EXPECTED_FILES = {
    'ExportacaoProducao.xlsx': 'producao',
    'Exportacao Atividade.xlsx': 'atividade',
    'Exportacao Status.xlsx': 'status',
}
```

### Adicionar Novos Mapeamentos

```python
COLUMN_MAPPINGS = {
    'producao': {
        'NOVO NOME': 'novo_nome',
        # ... existentes
    },
    # ... outras tabelas
}
```

---

## 📝 Notas Importantes

### ⚠️ Preservação de Dados

- ✅ Dados existentes em sql_map.json são **preservados**
- ✅ Apenas entradas dos arquivos processados são **atualizadas**
- ✅ Outras entradas não são **afetadas**

### ⚠️ Normalização

- Colunas são normalizadas (espaços extras removidos)
- Comparação é **case-insensitive**
- Acentos são mantidos nos nomes originais

### ⚠️ Performance

- Lê apenas cabeçalhos (rápido!)
- Tipicamente < 5 segundos para 3 arquivos
- Não carrega dados das linhas

---

## 🚀 Integração com App

### Após Executar Este Script

O `app.py` vai usar o sql_map.json atualizado:

```python
# Em app.py
from models.db_operations import insert_records_sqlalchemy

# Colunas serão mapeadas automaticamente usando sql_map.json
result = insert_records_sqlalchemy(records, table_name='producao')
```

---

## ❓ Troubleshooting

### Erro: "Pasta 'downloads' não encontrada"

```bash
# Criar pasta manualmente
mkdir downloads
# Ou copiar arquivos Excel para lá
```

### Erro: "Missing optional dependency 'openpyxl'"

```bash
# Instalar dependência
pip install openpyxl
# Ou via requirements.txt
pip install -r requirements.txt
```

### Erro: "Erro ao carregar sql_map.json existente"

- Arquivo `bases/sql_map.json` está corrompido
- Script cria um novo arquivo automaticamente

### Nenhum mapeamento encontrado

- Colunas não correspondem aos mapeamentos conhecidos
- Adicionar manualmente em `COLUMN_MAPPINGS`
- Ou editar `bases/sql_map.json` após execução

---

## 📈 Casos de Uso

### Caso 1: Primeira Execução

```bash
# Gera sql_map.json do zero
python gerar_sql_map_automatico.py
```

### Caso 2: Atualizando Arquivos

```bash
# Atualiza entradas dos arquivos novos
# Preserva dados antigos
python gerar_sql_map_automatico.py
```

### Caso 3: Adicionando Novos Arquivos

```python
# Editar EXPECTED_FILES:
EXPECTED_FILES = {
    'NovoArquivo.xlsx': 'nova_tabela',
    # ... existentes
}

# Executar script
python gerar_sql_map_automatico.py
```

---

## 🔗 Relacionado

- `bases/sql_map.json` - Arquivo de saída
- `models/db_operations.py` - Usa sql_map.json
- `app.py` - Usa column mappings automaticamente

---

## ✅ Checklist

- ✅ Arquivos Excel em `\downloads`
- ✅ Pasta `\bases` existe
- ✅ pandas instalado
- ✅ openpyxl instalado
- ✅ Executar script
- ✅ Verificar `bases/sql_map.json` gerado
- ✅ Usar em app.py

---

**Criado em:** 29 de outubro de 2025  
**Versão:** 1.0  
**Status:** ✅ Pronto para uso

