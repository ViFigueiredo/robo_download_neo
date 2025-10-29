# 🔄 Reprocessamento de Registros com Erro

**Documento:** Guia para re-inserir registros que falharam nas execuções anteriores  
**Status:** ✅ Pronto para uso  
**Data:** 29 de outubro de 2025  

---

## 📋 O que faz

O script `reprocessar_erros.py` lê os arquivos de erro (`error_records_*.jsonl`) gerados durante as execuções do robô e **tenta re-inserir aqueles registros no SQL Server**, com os seguintes tratamentos:

✅ **Filtra apenas colunas que existem na tabela SQL** (remove colunas extras como `TAGS`)  
✅ **Trunca campos que excedem o limite VARCHAR(255)** (evita erro "String or binary data would be truncated")  
✅ **Trata duplicatas automaticamente** (ignora registros já inseridos)  
✅ **Logging detalhado** de cada operação com rastreamento de linha/arquivo  

---

## 🚀 Como usar

### Passo 1: Verificar arquivos de erro

```bash
dir logs\error_records_*.jsonl
```

Você deve ver arquivos como:
```
error_records_status.jsonl
error_records_atividades.jsonl
error_records_producao.jsonl
```

### Passo 2: Executar reprocessamento

```bash
python reprocessar_erros.py
```

### Passo 3: Verificar resultado

O script gerará um log em `logs/reprocessar_erros.log` e mostrará no console:

```
======================================================================
 RESUMO FINAL
======================================================================
Inseridos com sucesso: 31
 Duplicatas ignoradas: 0
 Erros: 0
 Taxa de sucesso: 100.0%
======================================================================
```

---

## 📂 Arquivos de Erro

### Localização
```
logs/
├── error_records_status.jsonl
├── error_records_atividades.jsonl
├── error_records_producao.jsonl
└── reprocessar_erros.log  ← Gerado após execução
```

### Estrutura de cada linha

```json
{
  "timestamp": "2025-10-29 08:33:11",
  "batch_num": 3,
  "record_num": 809,
  "table": "EXPORTACAO_STATUS",
  "error_type": "DataError",
  "error_msg": "String or binary data would be truncated",
  "source": {
    "file": "Exportacao Status.xlsx",
    "line": "2810"
  },
  "record": { ... dados completos ... },
  "colunas_tentadas": [ ... colunas que foram tentadas ... ]
}
```

---

## 🔧 O que o script faz internamente

### 1. Conecta ao SQL Server
```python
connection = pyodbc.connect(driver, server, database, user, password)
```

### 2. Obtém colunas válidas da tabela
```sql
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'EXPORTACAO_STATUS'
```

### 3. Para cada registro do erro_records_*.jsonl:
- Filtra apenas colunas que existem na tabela SQL
- Trunca strings que excedem 255 caracteres
- Monta INSERT dinâmico: `INSERT INTO TABELA (col1, col2) VALUES (?, ?)`
- Executa no SQL Server
- Trata exceções (duplicatas, integridade, etc)

### 4. Commit e log

```python
connection.commit()
# Log: [1/31] Inserido: Exportacao Status.xlsx linha 2810
```

---

## ⚠️ Possíveis Problemas

### Problema: "Invalid column name 'TAGS'"
**Causa:** Arquivo JSON contém coluna que não existe na tabela SQL  
**Solução:** Script **automaticamente filtra** colunas inválidas  

**Antes:**
```
INSERT INTO EXPORTACAO_STATUS (NUMERO, TAGS, MOVIMENTACAO) VALUES (...)
❌ Invalid column name 'TAGS'
```

**Depois:**
```
INSERT INTO EXPORTACAO_STATUS (NUMERO, MOVIMENTACAO) VALUES (...)
✅ Inserido com sucesso
```

---

### Problema: "String or binary data would be truncated"
**Causa:** Campo maior que VARCHAR(255)  
**Solução:** Script **automaticamente trunca** para 255 caracteres  

**Logs mostram:**
```
Campo 'MOVIMENTACAO' truncado de 417 para 255 chars (Linha 2810 de Exportacao Status.xlsx)
```

---

### Problema: "Violation of PRIMARY KEY constraint"
**Causa:** Registro já foi inserido (duplicata)  
**Solução:** Script **ignora duplicatas** com logging  

**Comportamento:**
```
[5/31] DUPLICATA: Exportacao Status.xlsx linha 24217 (ja inserida em execucao anterior)
```

---

## 📊 Exemplo de Execução Completa

```
2025-10-29 08:44:39,033 - INFO - Processando: logs\error_records_status.jsonl
2025-10-29 08:44:39,033 - INFO - Tabela alvo: EXPORTACAO_STATUS
2025-10-29 08:44:39,159 - INFO - Conectado ao SQL Server: 192.168.11.200,1434/rpa_neocrm
2025-10-29 08:44:39,272 - INFO - Colunas validas na tabela: ENTROU, ETAPA, MOVIMENTACAO, NUMERO, ...
2025-10-29 08:44:39,278 - INFO - Total de registros para reprocessar: 31

2025-10-29 08:44:39,284 - INFO - [1/31] Inserido: Exportacao Status.xlsx linha 2810
2025-10-29 08:44:39,287 - INFO - [2/31] Inserido: Exportacao Status.xlsx linha 12555
2025-10-29 08:44:39,290 - INFO - [3/31] Inserido: Exportacao Status.xlsx linha 18521
...
2025-10-29 08:44:39,376 - INFO - [31/31] Inserido: Exportacao Status.xlsx linha 63170

2025-10-29 08:44:39,421 - INFO - Commit realizado com sucesso
2025-10-29 08:44:39,423 - INFO -
======================================================================
 RESUMO FINAL
======================================================================
2025-10-29 08:44:39,423 - INFO - Inseridos com sucesso: 31
2025-10-29 08:44:39,423 - INFO -  Duplicatas ignoradas: 0
2025-10-29 08:44:39,423 - INFO -  Erros: 0
2025-10-29 08:44:39,424 - INFO -  Taxa de sucesso: 100.0%
```

---

## 📝 Logs Gerados

### `logs/reprocessar_erros.log` (completo)
```
2025-10-29 08:44:39,033 - INFO - Processando: logs\error_records_status.jsonl
...
2025-10-29 08:44:39,284 - INFO - [1/31] Inserido: Exportacao Status.xlsx linha 2810
...
```

### Uso
```bash
# Ver primeiras 10 linhas
head -10 logs/reprocessar_erros.log

# Ver últimas 20 linhas
tail -20 logs/reprocessar_erros.log

# Contar inserções bem-sucedidas
findstr "Inserido" logs/reprocessar_erros.log | find /c "Inserido"

# Ver apenas erros
findstr "Erro" logs/reprocessar_erros.log
```

---

## 🔄 Workflow Recomendado

### Cenário: Registros falharam por coluna grande

1. **Problema ocorreu:**
   ```
   ❌ String or binary data would be truncated
   (Arquivou erros em error_records_status.jsonl)
   ```

2. **Aumentar coluna no SQL:**
   ```sql
   ALTER TABLE EXPORTACAO_STATUS 
   ALTER COLUMN MOVIMENTACAO VARCHAR(MAX);
   ```

3. **Re-inserir com script:**
   ```bash
   python reprocessar_erros.py
   ```

4. **Verificar resultado:**
   ```
   Taxa de sucesso: 100.0%
   ```

---

## 🛠️ Personalização

### Aumentar limite de truncamento

Editar `reprocessar_erros.py`:

```python
# Antes (255 caracteres)
FIELD_LIMITS = {
    'EXPORTACAO_STATUS': {
        'MOVIMENTACAO': 255,  # ← Aumentar para MAX
    }
}

# Depois (máximo - sem limite)
FIELD_LIMITS = {
    'EXPORTACAO_STATUS': {
        'MOVIMENTACAO': 999999,  # Sem truncamento efetivo
    }
}
```

### Adicionar informações de debug

```bash
# Ativar log DEBUG
# Adicionar linha em main():
logging.getLogger().setLevel(logging.DEBUG)
```

---

## ✅ Checklist de Uso

- [ ] Verificar variáveis `.env` estão corretas (DB_SERVER, etc)
- [ ] Ter arquivo(s) `error_records_*.jsonl` em `logs/`
- [ ] Executar `python reprocessar_erros.py`
- [ ] Verificar taxa de sucesso em "RESUMO FINAL"
- [ ] Confirmar dados foram inseridos no SQL com:
  ```sql
  SELECT COUNT(*) FROM EXPORTACAO_STATUS;
  ```

---

## 📞 Suporte

Se houver erros não previstos:

1. Verificar `logs/reprocessar_erros.log` completo
2. Confirmar que colunas SQL foram aumentadas se necessário
3. Verificar conectividade SQL Server com:
   ```bash
   python tests/test_sql_connection.py
   ```
4. Verificar .env está correto

---

**Última atualização:** 29 de outubro de 2025  
**Versão:** 1.0
