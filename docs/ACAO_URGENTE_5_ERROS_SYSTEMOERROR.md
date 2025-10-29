# 🚨 AÇÃO URGENTE - 5 Erros SystemError (Padrão Sistemático)

**Criado:** 29 de outubro de 2025, 10:50 UTC  
**Prioridade:** 🔴 CRÍTICA  
**Status:** Em execução

---

## 🎯 Situação Atual

```
❌ PROBLEMA DESCOBERTO:
   Não foram apenas 4 erros pontuais
   Segunda execução revelou 5 NOVOS erros SystemError
   Padrão SISTEMÁTICO, não transiente
   
⚠️  IMPACTO:
   Sistema está degradado
   Taxa de erro aumentando
   Potencial: 100+ erros/hora se continuar
   
🔴 STATUS:
   CRÍTICO - Requer intervenção URGENTE
```

---

## 📋 CHECKLIST DE AÇÕES (URGENTE)

### ✅ ETAPA 1: PARAR SISTEMA (Agora - 2 min)

```bash
# 1. Desabilitar agendador
# Editar app.py linha ~1600
# Comentar: schedule.every(30).minutes.do(executar_rotina)

# 2. OU configurar timeout de DEBUG
set DEBUG_MODE=true
set SINGLE_RUN=true  # apenas 1 execução, depois sai

# 3. Evitar mais dados ruins no banco
```

**Por que:** Parar de gerar 100+ erros por execução

---

### ✅ ETAPA 2: AUMENTAR TIMEOUTS (Agora - 5 min)

**Abrir arquivo `.env` e MODIFICAR:**

```properties
# ANTES:
DB_CONNECTION_TIMEOUT=30
TIMEOUT_DOWNLOAD=60
POST_RETRIES=3
BACKOFF_BASE=1.5

# DEPOIS (COPIAR/COLAR):
DB_CONNECTION_TIMEOUT=180
TIMEOUT_DOWNLOAD=180
POST_RETRIES=10
BACKOFF_BASE=3.0
```

**Scripts prontos:**

**Windows (PowerShell):**
```powershell
$file = '.env'
$content = Get-Content $file
$content = $content -replace 'DB_CONNECTION_TIMEOUT=.*', 'DB_CONNECTION_TIMEOUT=180'
$content = $content -replace 'TIMEOUT_DOWNLOAD=.*', 'TIMEOUT_DOWNLOAD=180'
$content = $content -replace 'POST_RETRIES=.*', 'POST_RETRIES=10'
$content = $content -replace 'BACKOFF_BASE=.*', 'BACKOFF_BASE=3.0'
Set-Content $file $content
Write-Host "✅ Configurações atualizadas para URGÊNCIA" -ForegroundColor Green
```

**Verificar resultado:**
```powershell
Select-String "CONNECTION_TIMEOUT|TIMEOUT_DOWNLOAD|RETRIES|BACKOFF" .env
```

---

### ✅ ETAPA 3: ATIVAR SQL PROFILER (2-5 min)

**No SQL Server Management Studio:**

```sql
-- Criar sessão de rastreamento para capturar erro REAL
USE master
GO

-- Criar trace para erros
DECLARE @traceid INT

EXECUTE sp_trace_create 
    @traceid = @traceid OUTPUT,
    @fileName = 'C:\Trace\pyodbc_errors',
    @options = 2,
    @maxfilesize = 500,
    @stoptime = DATEADD(hour, 2, GETDATE());

-- Evento: Error reported
EXECUTE sp_trace_setevent
    @traceid = @traceid,
    @eventid = 67,          -- SQL:BatchCompleted
    @columnid = 12,         -- Duration
    @on = 1;

-- Iniciar trace
EXECUTE sp_trace_setstatus @traceid, 1;

-- Depois da próxima execução, parar e analisar
-- EXECUTE sp_trace_setstatus @traceid, 0;
```

**Por que:** Capturar mensagem de erro REAL (não genérica)

---

### ✅ ETAPA 4: VERIFICAR DRIVER ODBC (2-3 min)

**Windows - Verificar versão:**

```cmd
REM Abrir ODBC Data Source Administrator
odbcconf.exe

REM Ou via PowerShell:
Get-Item "HKLM:\Software\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server"
```

**Esperado:**
- ✅ ODBC Driver 17 (versão 17.10+)
- ❌ ODBC Driver 18 (pode ter conflito)
- ❌ Versão < 17.10 (bug)

**Se versão < 17.10:**
1. Desinstalar driver antigo
2. Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
3. Instalar versão 17.10 ou 18.x (mais recente)
4. Reiniciar

---

### ✅ ETAPA 5: TESTAR CONEXÃO MANUAL (2 min)

**Via sqlcmd:**

```bash
# Substituir valores
sqlcmd -S 192.168.11.200,1434 -U seu_usuario -P sua_senha ^
    -Q "SELECT @@VERSION; SELECT @@SERVERNAME;" -t 120

# Se conectar: ✅ Sucesso (mostrará versão do SQL Server)
# Se não: ❌ Erro específico (use para debug)
```

**Via Python (test_sql_connection.py):**

```bash
cd robo_download_neo
python tests/test_sql_connection.py
```

**Esperado:**
```
✅ Conectado com sucesso!
✅ SQL Server version: Microsoft SQL Server 2019
✅ Timeout: 180 segundos
```

---

### ✅ ETAPA 6: EXECUTAR COM DEBUG (5-10 min)

**Com timeouts aumentados:**

```bash
# Executar uma única vez (sem agendador)
set DEBUG_MODE=true
set SINGLE_RUN=true
python app.py

# Monitorar:
# • Se SystemError desaparece → foi timeout
# • Se continua → problema mais profundo
# • Se "Cannot insert NUL" desaparece → dados/conexão
```

**Observar:**
- Tempo de cada batch
- Se há timeouts em logs
- Se novos erros aparecem

---

## 📞 ESCALAÇÃO (Se Não Resolver)

**Se depois de aumentar timeouts ainda houver erros:**

```
ESCALAR PARA:
├─ DBA: problemas SQL Server
├─ Infraestrutura: problemas de rede/conexão
├─ Microsoft: problemas de driver ODBC
│
ENVIAR:
├─ error_records_producao.jsonl (últimas 2 linhas)
├─ robo_download.log (últimos 100 registros)
├─ Versão ODBC: [resultado do teste acima]
├─ Versão SQL Server: [resultado sqlcmd]
│
INFORMAR:
├─ Timestamp de primeira falha: 2025-10-29 10:37:56 UTC
├─ Timestamp de segunda falha: 2025-10-29 10:49:47 UTC
├─ Padrão: Diferentes batches, mesma mensagem genérica
├─ Taxa: ~5 erros por execução
├─ Paralelo: +200 erros "Cannot insert value NUL"
│
PERGUNTA-CHAVE:
"Por que pyodbc está retornando mensagem genérica
em vez da mensagem real do SQL Server?"
```

---

## 🕐 TIMELINE ESTIMADO

```
AGORA (próximos 15 min):
├─ 2 min: Parar agendador
├─ 5 min: Aumentar timeouts
├─ 2 min: Verificar driver
├─ 3 min: Testar conexão
├─ 3 min: Executar app.py com debug
└─ Total: ~15 min

DEPOIS (próximas 2 horas):
├─ 30 min: Monitorar execução
├─ 30 min: Analisar logs
├─ 30 min: Decisão: resolver ou escalar
├─ 30 min: Comunicar resultado
└─ Total: ~2 horas
```

---

## ✅ SINAIS DE SUCESSO

```
✅ SystemError desaparece
✅ "Cannot insert NUL" desaparece (ou reduz drasticamente)
✅ Taxa de sucesso > 99%
✅ Tempo de execução < 5 minutos
✅ Nenhum novo erro em 3 execuções consecutivas
```

---

## ❌ SINAIS DE FALHA

```
❌ SystemError continua aparecendo
❌ Em diferentes batches cada vez
❌ Mesmo com timeouts aumentados
❌ Driver ODBC versão antiga
❌ SQL Server desconectando
```

**Se acontecer:** Escalar IMEDIATAMENTE para infraestrutura

---

## 📝 TEMPLATE DE COMUNICAÇÃO

```
Para: DBA / Infraestrutura
Assunto: URGENTE - Erro SystemError sistemático em pyodbc
Prioridade: CRÍTICA

Histórico:
- 29/10/2025 10:37-10:38: 4 erros SystemError
- 29/10/2025 10:49: 5 novos erros SystemError
- Padrão: Diferentes batches, mesma mensagem genérica

Ações Tomadas:
- Aumentar timeouts: 30s→180s
- Aumentar retries: 3→10
- Aumentar backoff: 1.5→3.0

Necessário:
- Ativar SQL Profiler para capturar erro real
- Verificar health do SQL Server
- Verificar driver ODBC (versão atual: [X.X])

Impacto:
- +200 erros "Cannot insert value NUL" por execução
- Taxa de erro: 0,025%+ e aumentando
- Potencial: 100+ erros/hora se continuar

Anexos:
- error_records_producao.jsonl
- robo_download.log (últimas 100 linhas)
- Relatório de versão ODBC
```

---

## 🎯 Resumo Executivo

| Item | Status | Ação |
|------|--------|------|
| **Parar Agendador** | 🟡 PENDENTE | 2 min |
| **Aumentar Timeouts** | 🟡 PENDENTE | 5 min |
| **Ativar SQL Profiler** | 🟡 PENDENTE | 5 min |
| **Verificar Driver** | 🟡 PENDENTE | 3 min |
| **Testar Conexão** | 🟡 PENDENTE | 3 min |
| **Executar Debug** | 🟡 PENDENTE | 10 min |
| **Escalar se necessário** | 🟡 PRONTO | Conforme resultado |

**Tempo Total:** ~15-30 min para diagnóstico

---

**Documento:** AÇÃO URGENTE - 5 Erros SystemError  
**Criado:** 29 de outubro de 2025, 10:50 UTC  
**Status:** 🔴 CRÍTICO - Requer ação imediata  
**Próxima revisão:** Após aumentar timeouts (em ~10 min)

