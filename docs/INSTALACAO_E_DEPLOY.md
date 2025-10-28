# 🚀 Instalação e Deploy - Guia Completo

**Tempo Total:** 4-8 horas  
**Dificuldade:** Intermediária  
**Pré-requisitos:** Windows, Python 3.8+, SQL Server 2016+

---

## 📋 Índice

1. [Fase 1: Preparação](#fase-1-preparação)
2. [Fase 2: SQL Server](#fase-2-sql-server)
3. [Fase 3: Configuração](#fase-3-configuração)
4. [Fase 4: Testes](#fase-4-testes)
5. [Fase 5: Deploy](#fase-5-deploy)
6. [Fase 6: Monitoramento](#fase-6-monitoramento)

---

## Fase 1: Preparação

### 1.1 Verificar Python
```bash
python --version
# Deve ser 3.8+ (ex: Python 3.10.5)

# Se não tiver, baixe de https://www.python.org/downloads/
```

### 1.2 Clonar/Baixar Projeto
```bash
git clone https://github.com/ViFigueiredo/robo_download_neo.git
cd robo_download_neo

# Ou baixe como ZIP
```

### 1.3 Criar Ambiente Virtual (Recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Agora o prompt muda para: (venv) C:\...>
```

### 1.4 Instalar Dependências
```bash
pip install -r requirements.txt

# Aguarde ~2-3 minutos
# Instala: selenium, pandas, requests, schedule, python-dotenv, pyodbc
```

### 1.5 Instalar ODBC Driver 18 (IMPORTANTE!)
```bash
# Windows: Download do site Microsoft
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Ou via Chocolatey (se tiver)
choco install sql-odbc-driver

# Verificar instalação
odbcconf /j /a {REGSVR "C:\Program Files\Microsoft ODBC Driver 18 for SQL Server\msodbcsql.dll"}
```

### ✅ Checklist Fase 1
- [ ] Python 3.8+ instalado
- [ ] Projeto clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências instaladas (`pip list` mostra tudo)
- [ ] ODBC Driver 18 instalado

---

## Fase 2: SQL Server

### 2.1 Verificar Conexão

```bash
# Windows PowerShell ou cmd
sqlcmd -S seu_servidor -U seu_usuario -P sua_senha

# Se conectar, escreva: exit
# Se não: verifique servidor, user, pass
```

### 2.2 Criar Banco de Dados (Se não existir)

```sql
-- Execute no SQL Server Management Studio ou via sqlcmd
CREATE DATABASE rpa_neocrm;
GO

USE rpa_neocrm;
GO
```

### 2.3 Criar Tabelas

Execute este script SQL **completo** no seu banco:

```sql
USE rpa_neocrm;
GO

-- Tabela 1: EXPORTACAO_PRODUCAO
CREATE TABLE [dbo].[EXPORTACAO_PRODUCAO] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [DATA] DATETIME,
    [CLIENTE] NVARCHAR(255),
    [PRODUTO] NVARCHAR(255),
    [QUANTIDADE] INT,
    [VALOR] DECIMAL(12,2),
    [PEDIDO_ID] NVARCHAR(50),
    [STATUS] NVARCHAR(100),
    [CRIADO_EM] DATETIME DEFAULT GETDATE(),
    [ATUALIZADO_EM] DATETIME DEFAULT GETDATE()
);

CREATE INDEX IX_DATA ON [EXPORTACAO_PRODUCAO]([DATA]);
CREATE INDEX IX_CLIENTE ON [EXPORTACAO_PRODUCAO]([CLIENTE]);
GO

-- Tabela 2: EXPORTACAO_ATIVIDADE
CREATE TABLE [dbo].[EXPORTACAO_ATIVIDADE] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [DATA] DATETIME,
    [TIPO] NVARCHAR(100),
    [DESCRICAO] NVARCHAR(500),
    [RESPONSAVEL] NVARCHAR(255),
    [STATUS] NVARCHAR(100),
    [CRIADO_EM] DATETIME DEFAULT GETDATE(),
    [ATUALIZADO_EM] DATETIME DEFAULT GETDATE()
);

CREATE INDEX IX_DATA ON [EXPORTACAO_ATIVIDADE]([DATA]);
CREATE INDEX IX_TIPO ON [EXPORTACAO_ATIVIDADE]([TIPO]);
GO

-- Tabela 3: EXPORTACAO_STATUS
CREATE TABLE [dbo].[EXPORTACAO_STATUS] (
    [ID] INT IDENTITY(1,1) PRIMARY KEY,
    [DATA] DATETIME,
    [ATIVIDADE_ID] NVARCHAR(50),
    [STATUS_ANTERIOR] NVARCHAR(100),
    [STATUS_NOVO] NVARCHAR(100),
    [MOTIVO] NVARCHAR(500),
    [CRIADO_EM] DATETIME DEFAULT GETDATE(),
    [ATUALIZADO_EM] DATETIME DEFAULT GETDATE()
);

CREATE INDEX IX_DATA ON [EXPORTACAO_STATUS]([DATA]);
CREATE INDEX IX_STATUS ON [EXPORTACAO_STATUS]([STATUS_NOVO]);
GO

-- Verificar criação
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'dbo';
GO
```

### 2.4 Verificar Tabelas
```bash
# Via sqlcmd
sqlcmd -S seu_servidor -U seu_usuario -P sua_senha -d rpa_neocrm -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"

# Deve retornar 3 tabelas:
# - EXPORTACAO_PRODUCAO
# - EXPORTACAO_ATIVIDADE
# - EXPORTACAO_STATUS
```

### ✅ Checklist Fase 2
- [ ] SQL Server acessível
- [ ] Banco de dados criado
- [ ] 3 tabelas criadas
- [ ] Índices criados
- [ ] Credenciais testadas

---

## Fase 3: Configuração

### 3.1 Criar `.env` do `.env.example`

```bash
# Copiar arquivo de exemplo
copy .env.example .env

# Abrir em editor (VS Code, Notepad++, etc)
code .env
```

### 3.2 Preencher `.env`

```properties
# ============================================
# SISTEMA CORPORATIVO
# ============================================
SYS_URL=https://neo.solucoes.plus/
SYS_USERNAME=seu_usuario_aqui
SYS_PASSWORD=sua_senha_aqui
SYS_SECRET_OTP=seu_token_otp_base32
OTP_URL=http://seu_servidor_otp:porta/generate_otp

# ============================================
# NAVEGADOR
# ============================================
BROWSER=chrome              # Usar: chrome ou edge
HEADLESS=true              # false = ver navegador (debug)
RETRIES_DOWNLOAD=3         # Tentativas de download
TIMEOUT_DOWNLOAD=60        # Segundos por tentativa

# ============================================
# DOWNLOADS
# ============================================
# Local para salvar os arquivos Excel baixados
DOWNLOADS_DIR=./downloads  # Relativo ao projeto
# Ou caminho absoluto: C:\dados\relatorios

# ============================================
# SQL SERVER (OBRIGATÓRIO)
# ============================================
DB_SERVER=seu_servidor.local,1434
DB_DATABASE=rpa_neocrm
DB_USERNAME=seu_usuario_sql
DB_PASSWORD=sua_senha_sql
DB_DRIVER=ODBC Driver 18 for SQL Server

# ============================================
# ENVIO E RETRY
# ============================================
BATCH_SIZE=25              # Registros por lote
POST_RETRIES=3             # Tentativas por lote
BACKOFF_BASE=1.5           # Exponencial (1.5^attempt)
DRY_RUN=false              # true = não envia (teste seguro)

# ============================================
# DESTINO FINAL (OPCIONAL)
# ============================================
# Pasta para arquivo final (não usado agora)
DESTINO_FINAL_DIR=Y:
```

### 3.3 Validar Configuração

```bash
# Teste leitura de .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SYS_URL:', os.getenv('SYS_URL')); print('DB_SERVER:', os.getenv('DB_SERVER'))"

# Deve mostrar os valores configurados
```

### 3.4 Criar Pasta `\bases\` e Mover JSONs (NOVO - Fase 4)

**IMPORTANTE:** O app carrega todos os JSONs de `\bases\`. Se você está upgrading de versão antiga:

```bash
# 1. Criar pasta
mkdir bases

# 2. Mover JSONs para lá
move map_relative.json bases/
move nocodb_map.json bases/
move sql_map.json bases/

# 3. Validar estrutura
dir bases\
# Deve listar:
# - map_relative.json
# - nocodb_map.json
# - sql_map.json
```

**Estrutura final esperada:**

```
robo_download_neo/
├── bases/
│   ├── map_relative.json
│   ├── nocodb_map.json
│   ├── sql_map.json
├── downloads/
├── logs/
├── .env
├── app.py
└── ...
```

**Se algum JSON faltar:**
```bash
python app.py
# Erro claro:
# Arquivo map_relative.json não encontrado em: C:\...\bases\map_relative.json
```

### ✅ Checklist Fase 3
- [ ] Arquivo `.env` criado
- [ ] Valores preenchidos corretamente
- [ ] Sem espaços extras ou aspas incorretas
- [ ] `.env` está em `.gitignore`
- [ ] Pasta `\bases\` criada (novo)
- [ ] JSONs movidos para `\bases\` (novo)

---

## Fase 4: Testes

### 4.1 Testar Conexão SQL

```bash
python tests/test_sql_connection.py

# Saída esperada:
# ✓ Conectado ao SQL Server
# ✓ Versão: SQL Server 2019 (ou sua versão)
# ✓ Tabela EXPORTACAO_PRODUCAO: OK
# ✓ Tabela EXPORTACAO_ATIVIDADE: OK
# ✓ Tabela EXPORTACAO_STATUS: OK
# ✓ Espaço em disco: OK
```

### 4.2 Testar Variáveis de Ambiente

```bash
# Verificar se todas as variáveis estão carregadas
python -c "
from dotenv import load_dotenv
import os
load_dotenv()

vars_obrigatorias = ['SYS_URL', 'SYS_USERNAME', 'DB_SERVER', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD']
for var in vars_obrigatorias:
    valor = os.getenv(var)
    status = '✓' if valor else '✗'
    print(f'{status} {var}: {valor[:20]}...' if valor else f'{status} {var}: FALTANDO')
"
```

### 4.3 Teste Seguro (DRY_RUN)

```bash
# Modo teste - lê tudo mas não envia ao BD
set DRY_RUN=true
python app.py

# Aguarde ~5-10 minutos
# Verificar logs:
type logs\robo_download.log
type logs\sent_records_*.jsonl
```

Se tudo OK:
```bash
# Logs devem mostrar:
# ✓ Login realizado
# ✓ Downloads completados
# ✓ 3 arquivos processados
# DRY_RUN ativo no sent_records_*.jsonl
```

### ✅ Checklist Fase 4
- [ ] Conexão SQL testa OK
- [ ] Variáveis carregadas corretamente
- [ ] DRY_RUN executa sem erros
- [ ] Logs mostram processamento

---

## Fase 5: Deploy

### 5.1 Primeira Execução Real

```bash
# Remover DRY_RUN (ou set DRY_RUN=false)
set DRY_RUN=false

# Executar
python app.py

# Aguarde ~5-10 minutos
```

### 5.2 Verificar Dados no SQL

```sql
-- Conectar ao banco e verificar
USE rpa_neocrm;
GO

SELECT COUNT(*) as Total FROM EXPORTACAO_PRODUCAO;
SELECT COUNT(*) as Total FROM EXPORTACAO_ATIVIDADE;
SELECT COUNT(*) as Total FROM EXPORTACAO_STATUS;

-- Deve retornar > 0 se enviou com sucesso
```

### 5.3 Agendar Execução (Windows Task Scheduler)

**Via interface gráfica:**

1. Abrir "Agendador de Tarefas"
2. Criar Tarefa Básica:
   - **Nome:** `Robo Download Neo`
   - **Gatilho:** Diário (qualquer hora - o app controla horário)
   - **Ação:** 
     - Programa: `C:\caminho\venv\Scripts\python.exe`
     - Argumentos: `C:\caminho\app.py`
     - Iniciar em: `C:\caminho\`

**Via PowerShell (alternativa):**

```powershell
# Criar tarefa
$action = New-ScheduledTaskAction -Execute "C:\caminho\venv\Scripts\python.exe" -Argument "C:\caminho\app.py" -WorkingDirectory "C:\caminho\"
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "Robo Download Neo" -Description "Download de relatórios"
```

### 5.4 Verificar Agendamento

```bash
# Ver tarefas agendadas
tasklist /fi "imagename eq python.exe"

# Ver logs de execução
Get-EventLog -LogName System | Where-Object {$_.Source -like "*Task*"} | Select-Object TimeGenerated, Message | head -20
```

### ✅ Checklist Fase 5
- [ ] Primeira execução OK
- [ ] Dados no SQL Server verificados
- [ ] Tarefa agendada criada
- [ ] Execução automática funcionando

---

## Fase 6: Monitoramento

### 6.1 Verificar Logs Diários

```bash
# Ver log principal
tail -f logs/robo_download.log

# Ver envios
tail -f logs/sent_records_*.jsonl

# Ver resumo
cat logs/envios_resumo.jsonl
```

### 6.2 Queries de Monitoramento

```sql
-- Dados recebidos hoje
SELECT COUNT(*) as Total, MAX(CRIADO_EM) as Ultima_Atualizacao 
FROM EXPORTACAO_PRODUCAO 
WHERE CAST(CRIADO_EM AS DATE) = CAST(GETDATE() AS DATE);

-- Distribuição por hora
SELECT CONVERT(VARCHAR(13), CRIADO_EM, 121) as Hora, COUNT(*) as Total 
FROM EXPORTACAO_PRODUCAO 
GROUP BY CONVERT(VARCHAR(13), CRIADO_EM, 121)
ORDER BY Hora DESC;

-- Últimas 24h de todas as tabelas
SELECT 'PRODUCAO' as Tabela, COUNT(*) as Total FROM EXPORTACAO_PRODUCAO WHERE CRIADO_EM > DATEADD(day, -1, GETDATE())
UNION ALL
SELECT 'ATIVIDADE', COUNT(*) FROM EXPORTACAO_ATIVIDADE WHERE CRIADO_EM > DATEADD(day, -1, GETDATE())
UNION ALL
SELECT 'STATUS', COUNT(*) FROM EXPORTACAO_STATUS WHERE CRIADO_EM > DATEADD(day, -1, GETDATE());
```

### 6.3 Alertas Recomendados

**Configure alertas para:**
- ❌ Falha de conexão SQL
- ❌ Falha de login na web
- ⚠️ Mais de 10% de falhas em batch
- ⚠️ Execução após 22h (fora do horário)
- 📉 0 registros processados

---

## 🚨 Troubleshooting Rápido

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError: No module named 'pyodbc'` | `pip install pyodbc` |
| `[HY000] [Microsoft][ODBC Driver 18]` | Instalar ODBC Driver 18 |
| `Login failed for user` | Verificar DB_USERNAME/DB_PASSWORD |
| `[42S01] Syntax error: line 1` | Verificar script SQL |
| `Connection timeout` | Verificar DB_SERVER e firewall |

Ver completo: **TROUBLESHOOTING.md**

---

## 📊 Validação Final

Após completar todas as fases:

```bash
# 1. Verificar estrutura
ls -la downloads/
ls -la logs/

# 2. Verificar dados SQL
python -c "
import pyodbc
conn = pyodbc.connect('Driver={ODBC Driver 18 for SQL Server};Server=seu_servidor;Database=rpa_neocrm;UID=usuario;PWD=senha')
cursor = conn.cursor()
for table in ['EXPORTACAO_PRODUCAO', 'EXPORTACAO_ATIVIDADE', 'EXPORTACAO_STATUS']:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} registros')
"

# 3. Verificar logs
grep "Finalizado em" logs/robo_download.log | tail -5
```

---

## ✅ Checklist Completo de Deploy

**Fase 1:**
- [ ] Python 3.8+
- [ ] Dependências instaladas
- [ ] ODBC Driver 18

**Fase 2:**
- [ ] SQL Server acessível
- [ ] Banco criado
- [ ] 3 Tabelas criadas

**Fase 3:**
- [ ] `.env` preenchido
- [ ] Variáveis validadas

**Fase 4:**
- [ ] Testes passaram
- [ ] DRY_RUN funcionou

**Fase 5:**
- [ ] Primeira execução OK
- [ ] Dados no SQL
- [ ] Agendamento criado

**Fase 6:**
- [ ] Logs verificados
- [ ] Alertas configurados
- [ ] Monitoramento ativo

---

## 🎉 Pronto!

Se completou tudo, seu robô está:
- ✅ **Instalado** - Todas as dependências
- ✅ **Configurado** - `.env` pronto
- ✅ **Testado** - Conexão e dados OK
- ✅ **Agendado** - Execução automática 08h-22h
- ✅ **Monitorado** - Logs e alertas

**Próximo passo:** Voltar a [README.md](./README.md) para entender a arquitetura

---

**Tempo total:** 4-8 horas  
**Dificuldade:** Intermediária  
**Suporte:** Ver TROUBLESHOOTING.md
