# 🐛 Troubleshooting - Soluções de Problemas

**Para:** Todos  
**Urgência:** Quando algo dá errado  
**Tempo:** 5-30 min por problema

---

## 🔍 Diagnóstico Rápido

### 1. Verificar Logs
```bash
# Log principal
tail -f logs/robo_download.log

# Envios para SQL (com rastreamento de linha)
tail -f logs/sent_records_*.jsonl

# Erros específicos
grep ERROR logs/robo_download.log
grep "Linha" logs/robo_download.log
```

### 2. Verificar Registro com Erro

Agora cada registro que falha mostra:
- **Qual arquivo:** `arquivo.xlsx`
- **Qual linha:** `Linha 42 de arquivo.xlsx`
- **Qual dado:** Primeiras 3 colunas do registro que falhou
- **Tipo de erro:** `IntegrityError`, `TypeError`, etc

Exemplo de log com rastreamento:
```
❌ ERRO ao inserir registro 5 do batch 2 (Linha 42 de ExportacaoProducao.xlsx): 
IntegrityError
Detalhes: Violation of PRIMARY KEY constraint
Dados: {'NUMERO': '12345', 'CLIENTE': 'XYZ Inc', 'VALOR': '1000.50'}
```

### 3. Debugar em JSONL

Arquivo: `logs/sent_records_*.jsonl`

Cada linha tem:
```json
{
  "status": "sent",
  "record": {...},
  "source": {
    "file": "ExportacaoProducao.xlsx",
    "line": 42
  },
  "batch_num": 2,
  "record_num": 5
}
```

Procurar erros:
```bash
# Erros em JSONL
jq '.[] | select(.status=="failed")' logs/sent_records_*.jsonl

# Ver qual linha falhou
jq '.[] | select(.status=="failed") | .source.line' logs/sent_records_*.jsonl
```

### 4. Verificar Variáveis
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB_SERVER:', os.getenv('DB_SERVER')); print('SYS_URL:', os.getenv('SYS_URL'))"
```

### 5. Verificar Conexão SQL
```bash
python tests/test_sql_connection.py
```

---

## 📋 Problemas Comuns

### ❌ `ModuleNotFoundError: No module named 'pyodbc'`

**Erro completo:**
```
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import pyodbc
ModuleNotFoundError: No module named 'pyodbc'
```

**Causas:**
- Dependência não instalada
- Venv não ativado
- Python errado

**Solução:**
```bash
# 1. Verificar venv
venv\Scripts\activate
# Deve aparecer (venv) no prompt

# 2. Instalar
pip install -r requirements.txt

# 3. Verificar instalação
pip list | grep pyodbc
```

---

### ❌ `[HY000] [Microsoft][ODBC Driver 18] Connection failed`

**Erro completo:**
```
pyodbc.OperationalError: [HY000] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]
Login failed for user
```

**Causas:**
- ODBC Driver não instalado
- Credenciais incorretas
- SQL Server inacessível

**Solução:**

**Passo 1: Instalar ODBC Driver 18**
```bash
# Windows - Download de:
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Ou via Chocolatey
choco install sql-odbc-driver

# Verificar instalação
odbcconf /j /a {REGSVR "C:\Program Files\Microsoft ODBC Driver 18 for SQL Server\msodbcsql.dll"}
```

**Passo 2: Verificar Credenciais**
```bash
# Testar com sqlcmd
sqlcmd -S seu_servidor -U seu_usuario -P sua_senha

# Se conectar, sai com: exit
# Se não: erro de credenciais/servidor
```

**Passo 3: Verificar .env**
```properties
# Verificar formato (SEM aspas extras)
DB_SERVER=192.168.11.200,1434    # ✓
DB_SERVER="192.168.11.200,1434"  # ✗ (com aspas)

DB_USERNAME=usuario              # ✓
DB_USERNAME=usuario              # ✓

DB_PASSWORD=senha123             # ✓
```

**Passo 4: Verificar Firewall**
```bash
# SQL Server porta padrão: 1433
# Verificar se aberta:
netstat -an | findstr :1433

# Se não aparecer, SQL Server não está rodando ou porta fechada
```

---

### ❌ `FileNotFoundError: [Errno 2] No such file or directory: '.env'`

**Erro completo:**
```
Traceback (most recent call last):
  File "app.py", line 45, in <module>
    if not Path('.env').exists():
FileNotFoundError: [Errno 2] No such file or directory: '.env'
```

**Causa:**
- Arquivo `.env` não existe

**Solução:**
```bash
# Copiar de exemplo
cp .env.example .env

# Ou criar manualmente
echo. > .env

# Preencher:
# SYS_URL=https://...
# DB_SERVER=...
# etc
```

---

### ❌ `[42S01] There is already an object named 'EXPORTACAO_PRODUCAO'`

**Erro completo:**
```
pyodbc.ProgrammingError: [42S01] [Microsoft][ODBC Driver 18 for SQL Server]
There is already an object named 'EXPORTACAO_PRODUCAO' in the database
```

**Causa:**
- Tabela já existe (pode ser primeira execução)

**Solução - OPÇÃO 1: Remover tabelas antigas**
```sql
DROP TABLE IF EXISTS EXPORTACAO_PRODUCAO;
DROP TABLE IF EXISTS EXPORTACAO_ATIVIDADE;
DROP TABLE IF EXISTS EXPORTACAO_STATUS;

-- Depois rodar script de criação novamente
```

**Solução - OPÇÃO 2: Continuar (sem recrear)**
```bash
# Tabelas já existem, apenas execute normalmente
python app.py
```

---

### ❌ `PermissionError: [WinError 32] O arquivo está sendo usado por outro processo`

**Erro completo:**
```
PermissionError: [WinError 32] O arquivo 'downloads\ExportacaoProducao.xlsx' 
está sendo usado por outro processo
```

**Causa:**
- Arquivo aberto em Excel
- Antivírus escaneando
- Outro programa usando

**Solução:**
```bash
# 1. Fechar arquivo
#    Feche em Excel, VS Code, etc

# 2. Reiniciar aplicação
python app.py

# 3. Se persistir, usar admin
#    Executar cmd como administrador
```

---

### ❌ `Elemento não encontrado: XPath //button[@id='export']`

**Erro completo:**
```
[ERROR] Elemento não encontrado para XPath: //button[@id='export']
[ERROR] Elemento não encontrado: //button[@id='export'] (referência map.json: producao.export_button)
```

**Causa:**
- XPath incorreto ou mudou
- Elemento não existe na página
- JavaScript ainda carregando

**Solução:**

**Passo 1: Verificar se é timeout**
```bash
# Aumentar TIMEOUT_DOWNLOAD em .env
TIMEOUT_DOWNLOAD=120  # Aumentar de 60 para 120 segundos
```

**Passo 2: Verificar elemento no navegador**
```bash
# Executar com HEADLESS=false para ver
set HEADLESS=false
python app.py

# Pausa aparecerá na página - verifique se elemento existe
```

**Passo 3: Atualizar XPath**
```bash
# Usar ferramenta gerar_xpath_relativo.py
python gerar_xpath_relativo.py

# Ou verificar manualmente com F12 no navegador
```

**Passo 4: Registrar screenshot para debug**
```bash
# Logs criarão element_screenshots/
# Verifique se elemento visível no screenshot
ls element_screenshots/
```

---

### ❌ `Login failed - Código autenticador inválido`

**Erro completo:**
```
[ERROR] Erro detectado, tentando novamente...
[ERROR] Código autenticador inválido
```

**Causa:**
- OTP_URL offline
- Token OTP expirado
- Servidor OTP com erro

**Solução:**

**Passo 1: Verificar OTP_URL**
```bash
# Testar endpoint diretamente
curl -X POST http://seu_servidor_otp:porta/generate_otp -d '{"secret":"seu_token"}' -H "Content-Type: application/json"

# Deve retornar: {"otp":"123456"}
```

**Passo 2: Verificar token base32**
```properties
# Verificar em .env se token está correto
# Formato: ABCDEFGH1234567890...==
# Sem espaços ou caracteres inválidos
```

**Passo 3: Verificar relógio do servidor**
```bash
# OTP usa time-based
# Se servidor estiver com relógio atrasado/adiantado, falha

# Sincronizar hora:
w32tm /resync
```

**Passo 4: Testes manuais**
```bash
# Você pode executar com HEADLESS=false e fazer login manual
set HEADLESS=false
python app.py

# Verá o navegador e poderá confirmar OTP manualmente
```

---

### ⚠️ `0 registros processados - Arquivo vazio`

**Erro completo:**
```
[INFO] Parsed 0 registros de downloads/ExportacaoProducao.xlsx
[WARNING] Nenhum dado para enviar
```

**Causa:**
- Arquivo Excel vazio
- Formato Excel inválido
- Mapeamento incorreto

**Solução:**

**Passo 1: Verificar arquivo**
```bash
# Abrir Excel
start downloads\ExportacaoProducao.xlsx

# Verificar se tem dados (não só headers)
```

**Passo 2: Verificar mapeamento**
```bash
# Ver nocodb_map.json
type nocodb_map.json

# Headers no Excel devem corresponder (aproximadamente)
# Ordem não importa, matching parcial OK
```

**Passo 3: Testar parse manualmente**
```bash
python tests/test_parse_atividades.py downloads/ExportacaoProducao.xlsx

# Gera: tests/json/parsed_producao_YYYYMMDD_HHMMSS.json
# Verificar conteúdo
```

---

### ❌ `Violation of PRIMARY KEY constraint` (Novo - Fase 6)

**Erro completo:**
```
pyodbc.IntegrityError: [23000] [Microsoft][ODBC Driver 18 for SQL Server]
Violation of PRIMARY KEY constraint 'PK__EXPORTAC__061A2F85400E3766'
Cannot insert duplicate key in object 'dbo.EXPORTACAO_STATUS'
The duplicate key value is (47871899, 2025-05-27 16:12:58)
```

**Comportamento esperado (Fase 6):**
```
ANTES: Toda batch falhava (0/25 registros salvos)
DEPOIS: Batch continua, duplicata é ignorada (24/25 salvos)

[DEBUG] [status] ⚠️  DUPLICATA DETECTADA no batch 2541, registro 3
[INFO] [status] ✅ Batch 2541: 24 inseridos, 1 duplicata ignorada, 0 erros
```

**Causa:**
- Exportação com períodos sobrepostos (ex: 90 dias que incluem dia anterior)
- Reexecução do robô (rodou 2x por acidente)
- Importação de dados duplicados da origem

**Solução:**

**Passo 1: Verificar que é realmente duplicata (não erro real)**

```bash
# Logs mostram duplicata e batch continua?
grep "DUPLICATA DETECTADA" logs/robo_download.log
# ✅ Se tiver linhas, é duplicata (não erro)

# Verificar taxa de sucesso
grep "📊 ESTATÍSTICAS" logs/robo_download.log
# ✅ Deve mostrar percentual realista (não 0%)
```

**Passo 2: Identificar duplicatas no SQL**

```sql
-- Ver se realmente há duplicatas
USE rpa_neocrm;
GO

-- Para EXPORTACAO_STATUS (PRIMARY KEY é NUMERO + ENTROU)
SELECT NUMERO, ENTROU, COUNT(*) as Duplicatas
FROM EXPORTACAO_STATUS
GROUP BY NUMERO, ENTROU
HAVING COUNT(*) > 1
ORDER BY Duplicatas DESC;

-- Para EXPORTACAO_ATIVIDADE
SELECT * FROM EXPORTACAO_ATIVIDADE
WHERE ATIVIDADE IN (
    SELECT ATIVIDADE FROM EXPORTACAO_ATIVIDADE GROUP BY ATIVIDADE HAVING COUNT(*) > 1
);
```

**Passo 3: (Opcional) Limpar duplicatas antigos**

```sql
-- Manter apenas 1 cópia, deletar extras (último INSERT é mantido)
WITH CTE AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY NUMERO, ENTROU ORDER BY CRIADO_EM DESC) as rn
    FROM EXPORTACAO_STATUS
)
DELETE FROM CTE WHERE rn > 1;

-- Verificar resultado
SELECT COUNT(*) FROM EXPORTACAO_STATUS;  -- Deve ter menos registros
```

**Passo 4: Prevenir duplicatas futuras**

```bash
# 1. Ajustar período de exportação para não sobrepor
#    Se exporta últimos 90 dias, não exporte últimos 91 dias

# 2. Usar DRY_RUN para validar antes de enviar
set DRY_RUN=true
python app.py

# 3. Verificar logs antes de production
grep "DUPLICATA" logs/robo_download.log
```

**O que NÃO fazer:**
- ❌ Não aumentar `POST_RETRIES` (retry não resolve PRIMARY KEY)
- ❌ Não modificar código de retry (duplicatas são tratadas)
- ❌ Não limpar logs quando há duplicatas (são informação valiosa)

**Referência:** Ver `TRATAMENTO_DUPLICATAS.md` para guia completo.

---

**Comportamento esperado:**
```
[INFO] DRY_RUN ativo. Payload batch 1: {...} (...)
[INFO] [producao] DRY_RUN ativo. Enviando 25 registros...
```

**Logs em `sent_records_producao.jsonl`:**
```jsonl
{"status":"DRY_RUN","payload":{...}}
```

**Solução:**
```bash
# Remover ou desabilitar DRY_RUN
set DRY_RUN=false

# Ou no .env
DRY_RUN=false

# Depois executar
python app.py
```

---

### ❌ `Execução pendente por 22h - Fora da janela`

**Log:**
```
[INFO] Hora atual: 22:30 - Fora da janela de execução (08:00-22:00)
[INFO] Aguardando...
```

**Comportamento normal:**
- App só executa entre 08h e 22h
- Fora desse horário, apenas aguarda

**Para forçar execução:**
```bash
# Remover lógica de horário (não recomendado)
# Ou usar Task Scheduler para iniciar manualmente
```

---

### ❌ `Connection timeout - SQL Server não responde`

**Erro completo:**
```
pyodbc.OperationalError: [08001] [Microsoft][ODBC Driver 18 for SQL Server]
Cannot open a connection
```

**Causa:**
- SQL Server offline
- Firewall bloqueando
- Porta incorreta
- Network latência

**Solução:**

```bash
# 1. Verificar se SQL Server está rodando
Get-Service -Name MSSQLSERVER | Select Status

# 2. Verificar conectividade com servidor
ping seu_servidor

# 3. Verificar porta
Test-NetConnection -ComputerName seu_servidor -Port 1434

# 4. Testar com sqlcmd
sqlcmd -S seu_servidor -U usuario -P senha

# 5. Aumentar timeout
# .env:
# DB_CONNECTION_TIMEOUT=60  (padrão)
```

---

### ❌ `Arquivo enviado mas não aparece no SQL`

**Log mostra:**
```
[INFO] [producao] Enviado: 25 registros com sucesso
```

**Mas query retorna 0:**
```sql
SELECT COUNT(*) FROM EXPORTACAO_PRODUCAO;
```

**Causa:**
- Commit não executado
- Transação aberta não finalizada
- Dados em tabela temporária

**Solução:**

```sql
-- 1. Verificar se dados existem
SELECT COUNT(*) FROM EXPORTACAO_PRODUCAO;

-- 2. Verificar últimos inserts
SELECT TOP 10 * FROM EXPORTACAO_PRODUCAO ORDER BY CRIADO_EM DESC;

-- 3. Se vazio, verificar logs de erro SQL
-- Executar teste novamente com DRY_RUN=false
```

```bash
# 4. Verificar logs
grep "failed" logs/sent_records_*.jsonl

# Pode conter dados mas erros na inserção
```

---

### ❌ `Erro de codificação: 'charmap' codec can't encode character`

**Erro completo:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 0
```

**Causa:**
- Terminal Windows com encoding limitado
- Caracteres especiais (✓, ✗, emoji) não suportados

**Solução:**

```bash
# 1. Mudar encoding no PowerShell
$env:PYTHONIOENCODING = "utf-8"
python app.py

# 2. Ou usar Python com UTF-8
python -X utf8 app.py

# 3. Ou remover caracteres especiais do código (não ideal)
```

---

## 🧪 Testes de Diagnóstico

### Teste 1: Conexão SQL
```bash
python tests/test_sql_connection.py
# Deve retornar: ✓ Conexão OK, ✓ Tabelas OK
```

### Teste 2: Variáveis Carregadas
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('\n'.join([f'{k}={v[:20]}...' for k,v in os.environ.items() if 'DB_' in k or 'SYS_' in k]))"
```

### Teste 3: Parse de Arquivo
```bash
python tests/test_parse_atividades.py downloads/ExportacaoProducao.xlsx
# Gera JSON em tests/json/
```

### Teste 4: DRY_RUN Seguro
```bash
set DRY_RUN=true
python app.py
# Lê tudo, não envia
```

---

## 📊 Checklist de Debug

Quando algo dá errado, verificar nesta ordem:

- [ ] Ler `logs/robo_download.log` completo
- [ ] Verificar `logs/sent_records_*.jsonl` para erros específicos
- [ ] Rodar `python tests/test_sql_connection.py`
- [ ] Verificar `.env` (sem aspas extras, valores corretos)
- [ ] Testar com `DRY_RUN=true` primeiro
- [ ] Ver `element_screenshots/` para problemas de UI
- [ ] Aumentar `TIMEOUT_DOWNLOAD` se timeout
- [ ] Executar com `HEADLESS=false` se XPath falhar
- [ ] Verificar credenciais SQL com `sqlcmd`
- [ ] Aumentar loglevel se precisa de mais detalhes
- [ ] **Verificar se há duplicatas** (novo - Fase 6)
  - `grep "DUPLICATA" logs/robo_download.log`
  - Se houver, é esperado! Veja seção "Violation of PRIMARY KEY constraint"

---

## 📞 Contato e Suporte

**Se ainda não resolveu:**

1. Copiar log completo: `logs/robo_download.log`
2. Copiar erro do `.jsonl`: `logs/sent_records_*.jsonl`
3. Descrever o que tentou fazer
4. Abrir issue no GitHub: https://github.com/ViFigueiredo/robo_download_neo/issues

---

**Última atualização:** Outubro 2025  
**Versão:** 1.0
