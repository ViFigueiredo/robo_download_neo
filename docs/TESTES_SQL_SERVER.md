# 🧪 Testes SQL Server - Envio Individual por Arquivo

**Data:** 28 de outubro de 2025  
**Propósito:** Testar envio de cada arquivo Excel para sua tabela no SQL Server  
**Status:** ✅ IMPLEMENTADO

---

## 🎯 O que foi criado

Três testes novos para enviar dados diretamente para o SQL Server:

| Teste | Arquivo Excel | Tabela SQL | Status |
|-------|--------------|-----------|--------|
| `test_post_sql_atividades.py` | `ExportacaoAtividade.xlsx` | `EXPORTACAO_ATIVIDADE` | ✅ |
| `test_post_sql_status.py` | `ExportacaoStatus.xlsx` | `EXPORTACAO_STATUS` | ✅ |
| `test_post_sql_producao.py` | `ExportacaoProducao.xlsx` | `EXPORTACAO_PRODUCAO` | ✅ |

---

## 📋 Funcionalidades

Todos os testes suportam:

✅ **Arquivo automático** - Procura em `downloads/` o arquivo mais recente  
✅ **Arquivo manual** - Via `--file` para arquivo específico  
✅ **JSON parseado** - Via `--json` para usar arquivo JSON já parseado  
✅ **DRY_RUN** - Simula envio sem tocar no banco  
✅ **Batch customizado** - Via `--batch-size` para alterar tamanho do batch  
✅ **Retry configurável** - Via `--post-retries` e `--backoff-base`  
✅ **Modo verbose** - Via `--verbose` para debug detalhado  
✅ **Logging estruturado** - JSONL em `logs/sent_records_*.jsonl`  
✅ **Rastreamento de linha** - Sabe qual linha do Excel cada registro veio  

---

## 🚀 Como Usar

### 1️⃣ Teste de Atividades

**Uso básico (arquivo recente em downloads/):**
```bash
python tests/test_post_sql_atividades.py
```

**Com arquivo específico:**
```bash
python tests/test_post_sql_atividades.py --file ./downloads/meu_arquivo.xlsx
```

**Com arquivo JSON parseado:**
```bash
python tests/test_post_sql_atividades.py --json ./tests/json/parsed_atividades_20251028.json
```

**Modo DRY_RUN (simula sem enviar):**
```bash
python tests/test_post_sql_atividades.py --dry-run
```

**Com batch customizado:**
```bash
python tests/test_post_sql_atividades.py --batch-size 50
```

**Combinado (DRY_RUN + Verbose):**
```bash
python tests/test_post_sql_atividades.py --dry-run --verbose
```

---

### 2️⃣ Teste de Status

**Uso básico:**
```bash
python tests/test_post_sql_status.py
```

**Com arquivo específico:**
```bash
python tests/test_post_sql_status.py --file ./downloads/ExportacaoStatus.xlsx
```

**Modo DRY_RUN:**
```bash
python tests/test_post_sql_status.py --dry-run
```

---

### 3️⃣ Teste de Produção

**Uso básico:**
```bash
python tests/test_post_sql_producao.py
```

**Com arquivo específico:**
```bash
python tests/test_post_sql_producao.py --file ./downloads/ExportacaoProducao.xlsx
```

**Modo DRY_RUN:**
```bash
python tests/test_post_sql_producao.py --dry-run
```

---

## 📊 Exemplo de Saída

```
======================================================================
🧪 TESTE: Envio de ATIVIDADES para SQL Server
======================================================================

📥 Arquivo Excel encontrado (mais recente): ExportacaoAtividade.xlsx
📖 Parseando arquivo: C:\...\downloads\ExportacaoAtividade.xlsx
✅ Parse bem-sucedido: 1245 registros extraídos

📊 Resumo dos registros a enviar:
   Total: 1245 registros
   Batch Size: default
   DRY_RUN: NÃO

📝 Amostra do primeiro registro:
   ATIVIDADE: 12345
   DESCRICAO: Atividade de teste
   DATA: 2025-10-28
   ... (5 campos adicionais)

🚀 Iniciando envio para SQL Server...
   Tabela: EXPORTACAO_ATIVIDADE
   Registros: 1245

======================================================================
✅ TESTE CONCLUÍDO
======================================================================

📊 RESULTADO:
   ✅ Inseridos: 1245
   ❌ Falhados: 0
   📈 Taxa de sucesso: 100.0%
   ⏱️  Duração: 12.45s
   📦 Batches: 50 (até 25 registros cada)

📋 LOGS GERADOS:
   • logs/sent_records_atividades.jsonl (registros enviados)
   • logs/robo_download.log (detalhes da execução)
```

---

## 🔍 Opções de Linha de Comando

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `--file, -f` | Arquivo Excel específico | `--file ./meu.xlsx` |
| `--json` | Usar JSON parseado | `--json ./parsed.json` |
| `--dry-run` | Simular sem enviar | `--dry-run` |
| `--batch-size` | Tamanho do batch | `--batch-size 50` |
| `--post-retries` | Tentativas HTTP | `--post-retries 5` |
| `--backoff-base` | Fator backoff | `--backoff-base 2.0` |
| `--verbose, -v` | Debug detalhado | `--verbose` |

---

## 📋 Arquivo Automático vs Manual

### Automático (Padrão)
```bash
python tests/test_post_sql_atividades.py
```

**O que faz:**
1. Procura em `downloads/` por arquivo `Exportacao*Atividade*.xlsx`
2. Usa o arquivo MAIS RECENTE
3. Parseia automaticamente
4. Envia para SQL

**Vantagem:** Rápido para testar depois de um download

---

### Manual
```bash
python tests/test_post_sql_atividades.py --file C:\path\to\arquivo.xlsx
```

**O que faz:**
1. Usa o arquivo que você especificou
2. Parseia exatamente esse arquivo
3. Envia para SQL

**Vantagem:** Controle total sobre qual arquivo testar

---

## 🔒 Modo DRY_RUN

Teste sem tocar no banco:

```bash
python tests/test_post_sql_atividades.py --dry-run
```

**Saída:**
```
🔒 DRY_RUN ATIVO - Nenhum dado será enviado para SQL
...
🔒 MODO DRY_RUN: Nenhum dado foi realmente enviado
```

**Logs ainda são criados** em `logs/sent_records_atividades.jsonl` com `"status": "DRY_RUN"`

---

## 📈 Taxa de Sucesso

Cada teste mostra:
- **Inseridos:** Quantos registros foram inseridos com sucesso
- **Falhados:** Quantos registros tiveram erro
- **Taxa de sucesso:** Percentual de sucesso

Exemplo com duplicatas:
```
📊 RESULTADO:
   ✅ Inseridos: 1240
   ❌ Falhados: 5
   📈 Taxa de sucesso: 99.6%
```

---

## 📝 Logs Gerados

Cada teste cria ou adiciona a:

1. **`logs/sent_records_atividades.jsonl`** (ou status/producao)
```jsonl
{"status":"sent","table":"EXPORTACAO_ATIVIDADE","record":{...},"source":{"file":"ExportacaoAtividade.xlsx","line":42},"batch_num":2,"record_num":5,"timestamp":"2025-10-28 16:30:00"}
```

2. **`logs/robo_download.log`** (log geral)
```
[INFO] [atividades] Iniciando envio de 1245 registros para tabela 'EXPORTACAO_ATIVIDADE' em 50 batches
[INFO] [atividades] Processando batch 1/50 com 25 registros
[INFO] [atividades] ✅ Batch 1 processado: 25 inseridos, 0 duplicatas ignoradas, 0 erros
```

---

## 🧪 Casos de Uso

### Caso 1: Testar parse + envio juntos
```bash
# Primeiro parseia, depois envia
python tests/test_post_sql_atividades.py
```

### Caso 2: Validar sem tocar no banco
```bash
# Simula tudo sem enviar
python tests/test_post_sql_atividades.py --dry-run
```

### Caso 3: Testar batch pequeno
```bash
# Processa 10 registros por vez (útil para debug)
python tests/test_post_sql_atividades.py --batch-size 10 --verbose
```

### Caso 4: Retestar arquivo com erro anterior
```bash
# Arquivo específico, modo verbose para ver erro
python tests/test_post_sql_atividades.py --file ./downloads/ExportacaoAtividade.xlsx --verbose
```

### Caso 5: Usar JSON já parseado
```bash
# Se você já tem JSON parseado
python tests/test_post_sql_atividades.py --json ./tests/json/parsed_atividades_20251028.json
```

---

## ✅ Checklist de Testes

Antes de usar em produção:

- [ ] Arquivo Excel existe em `downloads/`
- [ ] Banco SQL Server está acessível
- [ ] Credenciais em `.env` estão corretas (DB_SERVER, DB_USERNAME, DB_PASSWORD)
- [ ] Tabela SQL existe (`EXPORTACAO_ATIVIDADE`, `EXPORTACAO_STATUS`, `EXPORTACAO_PRODUCAO`)
- [ ] Executar teste em DRY_RUN primeiro
- [ ] Verificar logs sem erros
- [ ] Executar teste real
- [ ] Validar dados no SQL Server

```bash
# Checklist rápido
python tests/test_sql_connection.py  # Verifica conexão
python tests/test_post_sql_atividades.py --dry-run  # Simula
python tests/test_post_sql_atividades.py  # Real
```

---

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo encontrado"
```
❌ Nenhum arquivo 'Exportacao*Atividade*.xlsx' encontrado em downloads/
```

**Solução:**
- Rode o download primeiro: `python tests/download_atividades.py`
- Ou forneça arquivo manualmente: `--file ./seu_arquivo.xlsx`

---

### Erro: "Conexão recusada"
```
❌ ERRO AO ENVIAR: OperationalError: Connection failed
```

**Solução:**
- Verificar se SQL Server está rodando: `Get-Service -Name MSSQLSERVER | Select Status`
- Verificar credenciais em `.env`
- Testar conexão: `python tests/test_sql_connection.py`

---

### Erro: "Tabela não existe"
```
❌ ERRO AO ENVIAR: ProgrammingError: Invalid object name 'EXPORTACAO_ATIVIDADE'
```

**Solução:**
- Criar tabela no SQL Server (schema do projeto)
- Ou verificar se nome da tabela está correto em `bases/sql_map.json`

---

### Taxa de sucesso baixa (muitas duplicatas)
```
📊 RESULTADO:
   ✅ Inseridos: 50
   ❌ Falhados: 200
   📈 Taxa de sucesso: 20.0%
```

**Solução:**
- Esperado se rodou o teste 2x com mesmo arquivo
- Usar `--dry-run` antes para validar
- Limpar duplicatas do banco: `DELETE FROM EXPORTACAO_ATIVIDADE WHERE ...`

---

## 🎯 Próximos Passos

1. Testar cada tabela individualmente
2. Validar dados no SQL Server
3. Integrar com rotina automatizada se necessário
4. Monitorar logs em `logs/sent_records_*.jsonl`

---

**Status:** ✅ Implementado  
**Testes Criados:** 3 (Atividades, Status, Produção)  
**Versão:** 2.0.6  
**Última atualização:** 28 de outubro de 2025
