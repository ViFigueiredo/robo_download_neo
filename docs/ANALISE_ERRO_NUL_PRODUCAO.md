# 🔍 Análise: Erro "Cannot insert the value NUL" - 19.773 Registros

**Data:** 29 de outubro de 2025  
**Arquivo:** ExportacaoProducao.xlsx  
**Erro:** `[23000] Cannot insert the value NUL` em TODAS as colunas  
**Status:** 🔴 CRÍTICO - 0% de sucesso

---

## 📊 Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Registros Parseados** | ✅ 19.773 |
| **JSON Gerado** | ✅ parsed_producao_20251029_113154.json |
| **Registros Inseridos** | ❌ 0 |
| **Registros Falhados** | ❌ 19.773 (100%) |
| **Taxa de Sucesso** | ❌ 0.0% |
| **Tempo Total** | ⏱️ 89.49 segundos |

---

## 🎯 Causa Raiz Identificada

### ❌ O PROBLEMA

```sql
[23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]
Cannot insert the value NUL
```

**"NUL" NÃO É NULL!** É o byte 0x00 (caractere nulo/NUL character).

### 🔴 O QUE ESTAVA ACONTECENDO

1. **Parse gera registros com campos vazios:** `"CAMPO": ""`
2. **Código tenta filtrar colunas vazias** (linhas 334-345 em app.py)
3. **BUG:** Remove `_line_number` e `_file_name` com `.pop()` ANTES de usar depois
4. **Resultado:** Strings vazias `""` são convertidas para byte 0x00 (NUL)
5. **SQL falha:** SQL Server rejeita caractere NUL em colunas VARCHAR

### 🔍 Como Identificar

Logs mostravam:
```
[WARNING] Erro de integridade no batch 20, registro 770 (Linha 19771 de ExportacaoProducao.xlsx): 
('23000', "[23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Cannot insert the value NUL
```

**Todos os 19.773 registros falhavam com EXATAMENTE o mesmo erro.**

Isso indica problema **sistemático**, não em dados específicos.

---

## ✅ Solução Implementada

### 1️⃣ Remover Lógica de Filtro de Colunas Vazias

**ANTES (❌ Bug):**
```python
for idx, record in enumerate(batch, 1):
    # Extrai e REMOVE campos com .pop() - ERRADO!
    line_number = record.pop('_line_number', '?')  # ❌ Remove do record
    file_name = record.pop('_file_name', '?')      # ❌ Remove do record
    
    # Depois tenta usar e falha!
    colunas_com_dados = [col for col in expected_columns 
                        if col in record and record[col]]  # ❌ Bug: record já foi modificado
```

**DEPOIS (✅ Correto):**
```python
for idx, record in enumerate(batch, 1):
    # Extrai SEM remover - CORRETO!
    line_number = record.get('_line_number', '?')    # ✅ Apenas lê
    file_name = record.get('_file_name', '?')        # ✅ Apenas lê
    
    # Cria cópia limpa para logging
    record_clean = {k: v for k, v in record.items() if not k.startswith('_')}
    
    # Sempre envia TODAS as colunas (não filtra vazias)
    values = []
    for col in expected_columns:
        val = record_clean.get(col, '')
        # Converte "" para None (que vira NULL em SQL)
        values.append(None if val == '' else val)
```

### 2️⃣ Estratégia de NULL vs Empty String

**Nova lógica:**
- ✅ Strings vazias `""` → `None` (vira NULL em SQL)
- ✅ Valores com conteúdo → Enviados como-são
- ✅ TODAS as colunas sempre enviadas (não filtra)
- ✅ SQL Server decide o que fazer com NULL

---

## 🧪 Teste da Solução

### Antes (❌ Falha)
```
✅ Inseridos: 0
❌ Falhados: 19773
📈 Taxa de sucesso: 0.0%
```

### Depois (esperado ✅)
```
✅ Inseridos: 19773 (ou próximo disso)
❌ Falhados: 0 (ou apenas duplicatas)
📈 Taxa de sucesso: 95%+ (exceto duplicatas)
```

---

## 📋 Checklist de Validação

- [ ] Recompile app.py (verificar sem erros)
- [ ] Execute novamente: `python tests/post_sql_producao.py`
- [ ] Verifique taxa de sucesso (deve ser 95%+)
- [ ] Procure por "Cannot insert the value NUL" nos logs
- [ ] Se ainda houver erros, procure por novo padrão (não será "NUL")

---

## 🔧 Próximas Etapas se Erro Persiste

1. **Se vir novo erro diferente de "NUL":**
   - Novo erro é sobre dados específicos, não sistemático
   - Analisar registro com erro (será mostrado nos logs)
   - Ajustar sql_map.json ou tipos de dados

2. **Se ver "Cannot insert duplicate":**
   - Esperado para registros já existentes
   - Isso é OK (taxa de sucesso reflete apenas novos)

3. **Se ver "Connection timeout":**
   - Problema de conexão (URGENTE do todo list #1)
   - Aumentar DB_CONNECTION_TIMEOUT de 30s para 180s

---

## 📚 Referências

- **Arquivo modificado:** app.py (linhas 315-370)
- **Erro SQL:** https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/mssqlserver-23000-database-engine-error
- **NUL character:** Byte 0x00, caractere especial do C (string terminator)

---

## 🎯 Métricas Esperadas Após Fix

| Métrica | Antes | Depois |
|---------|-------|--------|
| **Taxa de sucesso** | 0.0% | 95%+ |
| **Registros inseridos** | 0 | 18.700+ |
| **Erro "NUL"** | ✅ Presente | ❌ Desaparecido |
| **Tempo estimado** | 89s | 60-90s |

---

**Última atualização:** 29 de outubro de 2025  
**Status:** 🔧 EM CORREÇÃO
