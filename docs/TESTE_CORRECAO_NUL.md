# 🔧 Instruções: Testar Correção do Erro "Cannot insert the value NUL"

**Data:** 29 de outubro de 2025  
**Objetivo:** Validar que o fix resolveu o erro de inserção  
**Tempo estimado:** 5-10 minutos

---

## 📋 Pré-requisitos

- ✅ Arquivo `ExportacaoProducao.xlsx` em `downloads/`
- ✅ app.py modificado (linhas 315-370)
- ✅ SQL Server conectado e rodando
- ✅ Tabela `EXPORTACAO_PRODUCAO` existe

---

## 🧪 Teste 1: Parse (Deve Funcionar - Baseline)

```bash
# Gera JSON parseado
python tests/parse_producao.py

# Esperado: ✅ 
# - "✅ Parsed 19773 records de ExportacaoProducao.xlsx"
# - "💾 Saída gravada em: tests\json\parsed_producao_YYYYMMDD_HHMMSS.json"
```

**Resultado Esperado:**
```
📖 Parseando arquivo: downloads\ExportacaoProducao.xlsx
✅ Parsed 19773 records de ExportacaoProducao.xlsx
💾 Saída gravada em: tests\json\parsed_producao_20251029_120000.json
📊 Total: 19773 registros salvos em JSON
```

✅ **Se funciona:** Parse está OK, problema é na inserção.

---

## 🧪 Teste 2: INSERT com DRY_RUN (Valida sem enviar)

```bash
# Testa sem enviar para SQL
python tests/post_sql_producao.py --dry-run

# Esperado: ✅
# - "🔒 DRY_RUN ATIVO"
# - "0 RESULTADO: ✅ Inseridos: 19773"
# - "📈 Taxa de sucesso: 100.0%"
```

**Resultado Esperado:**
```
🔒 DRY_RUN ATIVO - Nenhum dado será enviado para SQL

📖 Parseando arquivo: downloads\ExportacaoProducao.xlsx
✅ Parse bem-sucedido: 19773 registros extraídos

📊 Resumo dos registros a enviar:
   Total: 19773 registros
   Batch Size: default
   DRY_RUN: SIM ✓

🚀 Iniciando envio para SQL Server...
   Tabela: EXPORTACAO_PRODUCAO
   Registros: 19773

======================================================================
✅ TESTE CONCLUÍDO
======================================================================

📊 RESULTADO:
   ✅ Inseridos: 19773
   ❌ Falhados: 0
   📈 Taxa de sucesso: 100.0%
   ⏱️  Duração: 2.34s
   📦 Batches: 20 (até 1000 registros cada)

🔒 MODO DRY_RUN: Nenhum dado foi realmente enviado
```

✅ **Se vê taxa 100%:** Validação passou, problema era no código.

---

## 🧪 Teste 3: INSERT REAL (Enviar para SQL)

```bash
# Envia REALMENTE para SQL
python tests/post_sql_producao.py

# Esperado: ✅
# - "❌ Falhados: 0 ou poucos (apenas duplicatas)"
# - "📈 Taxa de sucesso: 95%+" (exceto se houver duplicatas)
# - NENHUMA mensagem "Cannot insert the value NUL"
```

**Resultado Esperado (Cenário A - Sem Duplicatas):**
```
📖 Parseando arquivo: downloads\ExportacaoProducao.xlsx
✅ Parse bem-sucedido: 19773 registros extraídos

🚀 Iniciando envio para SQL Server...

======================================================================
✅ TESTE CONCLUÍDO
======================================================================

📊 RESULTADO:
   ✅ Inseridos: 19773
   ❌ Falhados: 0
   📈 Taxa de sucesso: 100.0%
   ⏱️  Duração: 87.32s
```

**Resultado Esperado (Cenário B - Com Algumas Duplicatas OK):**
```
📊 RESULTADO:
   ✅ Inseridos: 18050
   ❌ Falhados: 1723 (todas duplicatas - OK!)
   📈 Taxa de sucesso: 91.3%
   ⏱️  Duração: 89.12s
```

✅ **Se vê taxa acima de 80%:** FIX FUNCIONOU! ✅

---

## 🔴 Sinais de Falha

Se você vir algum desses, o fix NÃO funcionou:

### ❌ Erro: "Cannot insert the value NUL"
```
Taxa de sucesso: 0.0%
Falhados: 19773
```
→ **Solução:** Erro ainda presente. Verificar se app.py foi salvo corretamente.

### ❌ Erro: "Column does not exist"
```
Error at inserting record... 'COLUNA_ERRADA' not found
```
→ **Solução:** Verificar sql_map.json, nomes de colunas errados.

### ❌ Erro: "Connection timeout"
```
[08001] Cannot open a connection
```
→ **Solução:** URGENTE - Aumentar timeouts (ver todo list #1).

### ❌ Erro: "Invalid column name"
```
[207] Invalid column name '[COLUNA]'
```
→ **Solução:** Coluna não existe na tabela SQL. Verificar CREATE TABLE.

---

## 📊 Comparação Antes vs Depois

### ANTES (❌ Bug Original)

```
Taxa de sucesso: 0.0%
✅ Inseridos: 0
❌ Falhados: 19773 (100%)

Erro: Cannot insert the value NUL
Duração: 89.49s
```

**Todos os registros falhavam com erro NUL.**

### DEPOIS (✅ Esperado com Fix)

```
Taxa de sucesso: 91%+ (ou 100% se sem duplicatas)
✅ Inseridos: 18000+ (ou 19773)
❌ Falhados: 0-1700 (apenas duplicatas - OK!)

Erro: NENHUM "Cannot insert the value NUL"
Duração: 87-92s
```

**Registros inserem com sucesso, apenas duplicatas podem falhar (esperado).**

---

## 🔍 Se Ainda Houver Erro Diferente

### Registrar Informações

```bash
# 1. Ver log completo
Get-Content logs\robo_download.log | Select-Object -Last 50

# 2. Ver erros gravados
jq '.[] | select(.error_type != null)' logs\error_records_producao.jsonl | head -5

# 3. Ver primeiro registro que falhou
jq '.[] | select(.status == "failed") | .record' logs\sent_records_producao.jsonl | head -1
```

### Criar Ticket com Informações

Se problema persiste, salvar:
- `logs/robo_download.log` (últimas 100 linhas)
- `logs/error_records_producao.jsonl` (primeiros 5 erros)
- Output do teste completo
- Versão do ODBC Driver

---

## ✅ Validação Final

Se todos os testes passarem:

- [ ] Parse gera 19773 registros ✅
- [ ] DRY_RUN mostra 100% ✅
- [ ] INSERT REAL tem 95%+ de sucesso ✅
- [ ] Nenhum erro "Cannot insert the value NUL" ✅
- [ ] Registros aparecem no SQL Server ✅

**Se tudo OK: 🎉 FIX RESOLVEU O PROBLEMA!**

---

## 🚀 Próximas Etapas

1. **Se taxa de sucesso OK:**
   - Executar app.py completo
   - Monitorar logs por 24h
   - Ir para todo item #1 (aumentar timeouts)

2. **Se ainda houver erros:**
   - Executar SQL Profiler para ver mensagem real
   - Analisar tipo de dados das colunas
   - Verificar se há corrupção de dados no Excel

---

**Tempo estimado de testes:** 10-15 minutos  
**Responsável por testes:** Você  
**Próxima revisão:** Após testes bem-sucedidos

---

*Última atualização: 29 de outubro de 2025*
