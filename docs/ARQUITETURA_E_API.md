# 🏗️ Arquitetura e API - Referência Técnica

**Para:** Arquitetos, Tech Leads, Code Reviewers  
**Nível:** Avançado  
**Tempo de leitura:** 30-45 min

---

## 📋 Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Fluxo de Dados](#fluxo-de-dados)
3. [Funções Principais](#funções-principais)
4. [Configurações](#configurações)
5. [Estrutura de Dados](#estrutura-de-dados)
6. [Integração SQL Server](#integração-sql-server)

---

## Visão Geral da Arquitetura

```
┌──────────────────────────────────────────────────────┐
│           SISTEMA CORPORATIVO (Web)                  │
│           https://neo.solucoes.plus/                 │
└──────────────────┬───────────────────────────────────┘
                   │ Selenium (Chrome/Edge)
                   ├─ Login com 2FA/OTP
                   ├─ Navegação
                   └─ Download Excel
                   │
┌──────────────────▼───────────────────────────────────┐
│           ROBO DOWNLOAD NEO (Python)                 │
│           ├─ app.py (main)                           │
│           ├─ Automação Web (Selenium)                │
│           ├─ Parse Excel (Pandas)                    │
│           └─ Envio SQL (Pyodbc)                      │
└──────────────────┬───────────────────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼─┐  ┌───▼────┐  ┌─▼─────────┐
    │Excel │  │Configs │  │SQL Server │
    │Files │  │ .env   │  │   ODBC    │
    │      │  │JSON    │  │           │
    └──────┘  └────────┘  └───────────┘
         │         │         │
         └────────[downloads/]
                   [logs/]
```

---

## Fluxo de Dados

### 1. Inicialização
```
app.py início
  ├─ Carregar .env
  ├─ Validar variáveis obrigatórias
  ├─ Carregar map_relative.json (XPaths)
  ├─ Criar pastas (downloads, logs, screenshots)
  └─ Iniciar logger
```

### 2. Login
```
Selenium (Chrome/Edge)
  ├─ Acessar SYS_URL
  ├─ Preencher username/password
  ├─ Gerar OTP (POST a OTP_URL)
  ├─ Confirmar OTP
  ├─ Aguardar redirecionamento
  └─ Ready para downloads
```

### 3. Download (3 tipos)
```
Para cada relatório:
  1. Navegar para painel
  2. Selecionar data (D-90 ou D-92)
  3. Clicar "Exportar"
  4. Aguardar arquivo pronto
  5. Download via cookies de sessão
  6. Salvar em ./downloads/
```

### 4. Parse Excel
```
Arquivo baixado
  ├─ Ler com pandas.read_excel()
  ├─ Normalizar headers (sem acentos)
  ├─ Mapear colunas com nocodb_map.json
  ├─ Formatar datas (%Y-%m-%d %H:%M:%S)
  ├─ Converter tipos (int, float, string)
  └─ Retornar lista de dicts
```

### 5. Envio SQL Server
```
Lista de registros
  ├─ Conectar ao SQL (ODBC)
  ├─ Dividir em batches (25 registros)
  ├─ Para cada batch:
  │   ├─ Preparar INSERT statement
  │   ├─ PROCESSAR CADA REGISTRO INDIVIDUALMENTE (Novo!)
  │   │   ├─ Try: cursor.execute(insert_stmt, values)
  │   │   ├─ Except IntegrityError:
  │   │   │   ├─ Se PRIMARY KEY → Marcar como duplicata (ignora, não retry)
  │   │   │   └─ batch_duplicate_count += 1
  │   │   └─ Except OutroErro:
  │   │       └─ batch_error_count += 1
  │   ├─ Retry com backoff exponencial (1.5^attempt) APENAS para erros não-integridade
  │   ├─ Contar: batch_success_count, batch_duplicate_count, batch_error_count
  │   ├─ Log em JSONL com contadores (Novo!)
  │   └─ Commit (após processar TODOS os registros da batch)
  └─ Registrar resumo com taxa de sucesso (%)
```

---

## Funções Principais

### 1. Conexão SQL

**`get_mssql_connection() -> Connection`**

Abre conexão ODBC ao SQL Server.

```python
def get_mssql_connection():
    """Cria conexão com SQL Server usando credenciais do .env"""
    try:
        db_server = os.getenv('DB_SERVER')           # 'servidor,porta'
        db_database = os.getenv('DB_DATABASE')       # 'rpa_neocrm'
        db_username = os.getenv('DB_USERNAME')       # 'usuario'
        db_password = os.getenv('DB_PASSWORD')       # 'senha'
        db_driver = os.getenv('DB_DRIVER')           # 'ODBC Driver 18'
        
        conn_string = (
            f'Driver={{{db_driver}}};'
            f'Server={db_server};'
            f'Database={db_database};'
            f'UID={db_username};'
            f'PWD={db_password};'
            f'Encrypt=no;TrustServerCertificate=no;Connection Timeout=30;'
        )
        connection = pyodbc.connect(conn_string)
        logger.info(f"Conexão OK: {db_server}/{db_database}")
        return connection
    except Exception as e:
        logger.error(f"Erro ao conectar: {e}")
        raise
```

**Parâmetros:**
- Nenhum (lê do `.env`)

**Retorna:**
- `pyodbc.Connection` - Conexão ativa

**Levanta:**
- `Exception` - Se conexão falhar

**Exemplo:**
```python
conn = get_mssql_connection()
cursor = conn.cursor()
# ... usar
cursor.close()
conn.close()
```

---

### 2. Envio de Registros

**`post_records_to_mssql(records, table_name='producao', file_name=None) -> dict`**

Envia registros em batches para SQL Server com retry automático.

```python
def post_records_to_mssql(records, table_name='producao', file_name=None):
    """
    Envia registros para SQL Server em batches.
    
    Args:
        records (list): Lista de dicts com dados
        table_name (str): Nome da tabela para logs ('producao', 'atividades', 'atividades_status')
        file_name (str): Nome do arquivo (para determinar tabela via sql_map.json)
    
    Returns:
        dict: {'success': N, 'failed': N, 'total': N, 'batches_total': N, 'batches_failed': N}
    
    Respeta:
        - DRY_RUN: Se true, apenas loga (não envia)
        - BATCH_SIZE: Tamanho de cada lote (padrão: 25)
        - POST_RETRIES: Tentativas por batch (padrão: 3)
        - BACKOFF_BASE: Base exponencial (padrão: 1.5)
    """
```

**Fluxo:**

```
1. Carregar sql_map.json
   ├─ Encontrar tabela (por file_name)
   ├─ Obter nome da tabela SQL
   └─ Obter colunas esperadas

2. Processar registros
   ├─ Converter None → ""
   ├─ Converter datetime → "YYYY-MM-DD HH:MM:SS"
   ├─ Converter float/int → string
   └─ Garantir todas as colunas existem

3. Dividir em batches (25 registros cada)

4. Para cada batch:
   ├─ Se DRY_RUN=true:
   │   └─ Log em JSONL com status='DRY_RUN'
   ├─ Senão:
   │   ├─ Conectar ao SQL
   │   ├─ Preparar INSERT parametrizado
   │   ├─ Executar cursor.execute() N vezes
   │   ├─ Commit
   │   ├─ Log em JSONL com status='sent'
   │   └─ Retry com backoff se falhar

5. Retornar resumo
```

**Saída de Erro (Retry):**

```
Tentativa 1 (erro real): Falha → aguarda 1.5^1 = 1.5s
Tentativa 2 (erro real): Falha → aguarda 1.5^2 = 2.25s
Tentativa 3 (erro real): Falha → marca como 'failed'

Tentativa 1 (PRIMARY KEY duplicata): Falha → NÃO RETRY (ignorada)
```

**Per-Record Processing (Novo - Fase 6):**

```python
# Antes: Falha em 1 duplicata = toda batch falha (0/25 salvos)
# Depois: Falha em 1 duplicata = batch continua (24/25 salvos)

batch_success_count = 0
batch_duplicate_count = 0
batch_error_count = 0

for idx, record in enumerate(batch, 1):
    try:
        cursor.execute(insert_stmt, values)
        batch_success_count += 1
    except pyodbc.IntegrityError as ie:
        batch_duplicate_count += 1
        logger.debug(f"⚠️  DUPLICATA DETECTADA: {chave_primaria}")
        # NÃO tenta retry (não vai resolver)
    except Exception as record_error:
        batch_error_count += 1
        logger.warning(f"Erro: {type(record_error).__name__}")

# Resultado esperado: "24 inseridos, 1 duplicata ignorada, 0 erros"
```

**Logging em `sent_records_producao.jsonl` (Novo formato - Fase 6):**

```jsonl
{"status":"sent","table":"EXPORTACAO_PRODUCAO","batch_num":2541,"batch_success_count":24,"batch_duplicate_count":1,"batch_error_count":0,"record":{...},"timestamp":"2025-10-28 15:30:45"}
{"status":"sent","table":"EXPORTACAO_PRODUCAO","batch_num":2542,"batch_success_count":25,"batch_duplicate_count":0,"batch_error_count":0,"record":{...},"timestamp":"2025-10-28 15:30:46"}
{"status":"failed","table":"EXPORTACAO_PRODUCAO","batch_num":2543,"batch_success_count":20,"batch_duplicate_count":0,"batch_error_count":5,"error":"Connection timeout","timestamp":"2025-10-28 15:30:47"}
{"status":"DRY_RUN","payload":{...}}
```

**Resumo de Envio (saída em console - Novo formato):**

```
✅ [producao] Batch 2541: 24 inseridos, 1 duplicata ignorada, 0 erros
✅ [producao] Batch 2542: 25 inseridos, 0 duplicatas, 0 erros
❌ [producao] Batch 2543: 20 inseridos, 0 duplicatas, 5 erros
📊 ESTATÍSTICAS: Taxa de sucesso de registros: 98.2% | Batches bem-sucedidos: 2504/2549 (98.2%)
✅ Detalhes: 62577 inseridos, 1175 duplicatas ignoradas, 0 erros
⚠️ ATENÇÃO: 45 batch(es) falharam com 1125 registros. Verifique logs/sent_records_atividades_status.jsonl
```

---

### 3. Parse de Arquivo

**`parse_export_producao(file_path) -> list`**

Parse flexível de Excel com mapeamento.

```python
def parse_export_producao(file_path):
    """
    Parse Excel com normalização flexível.
    
    Args:
        file_path (str): Caminho para arquivo .xlsx
    
    Returns:
        list: Lista de dicts, uma por linha
    
    Lê:
        - nocodb_map.json para headers esperados
        - file_path via pandas.read_excel()
    
    Processa:
        - Normaliza headers (remove acentos, pontuação)
        - Match tolerante (substring)
        - Converte datas (DD/MM/YYYY → YYYY-MM-DD HH:MM:SS)
        - Concatena campos extras em 'TAGS'
    """
```

**Exemplo:**

```python
# Entrada: ExportacaoProducao.xlsx
# ┌─────────┬──────────┬────────┐
# │ Data    │ Cliente  │ Valor  │
# ├─────────┼──────────┼────────┤
# │ 28/10.. │ XYZ Ltda │ 1500   │
# └─────────┴──────────┴────────┘

records = parse_export_producao('./downloads/ExportacaoProducao.xlsx')

# Retorna:
# [
#   {
#     'DATA': '2025-10-28 14:30:00',
#     'CLIENTE': 'XYZ Ltda',
#     'VALOR': '1500',
#     'TAGS': ''
#   }
# ]
```

---

### 4. Limpeza de Arquivos Antigos

**`limpar_arquivos_antigos_downloads(palavras=None, padroes_regex=None, extensoes=(".xlsx",)) -> int`**

Remove arquivos antigos antes de cada download (evita conflitos).

```python
def limpar_arquivos_antigos_downloads(...):
    """
    Remove arquivos da pasta DOWNLOADS_DIR que combinem com padrões.
    
    Args:
        palavras (list): Palavras-chave para buscar (ex: 'exportacao', 'producao')
        padroes_regex (list): Padrões regex (ex: [r'^exportacao.*'])
        extensoes (tuple): Extensões alvo (ex: ('.xlsx',))
    
    Returns:
        int: Quantidade de arquivos removidos
    
    Normaliza nomes (sem acentos, lowercase) e compara com padrões.
    """
```

---

## Configurações

### `.env` - Variáveis Obrigatórias

```properties
# Sistema
SYS_URL                    # URL do sistema corporativo
SYS_USERNAME               # Usuário do sistema
SYS_PASSWORD               # Senha do sistema
SYS_SECRET_OTP             # Token base32 para OTP
OTP_URL                    # URL do servidor de OTP

# Navegador
BROWSER                    # 'chrome' ou 'edge'
HEADLESS                   # 'true' ou 'false'
RETRIES_DOWNLOAD           # Tentativas (default: 3)
TIMEOUT_DOWNLOAD           # Segundos (default: 60)

# Downloads
DOWNLOADS_DIR              # Pasta local (default: ./downloads)

# SQL Server (OBRIGATÓRIO!)
DB_SERVER                  # 'servidor,porta'
DB_DATABASE                # 'nome_banco'
DB_USERNAME                # 'usuario_sql'
DB_PASSWORD                # 'senha_sql'
DB_DRIVER                  # 'ODBC Driver 18 for SQL Server'

# Envio
BATCH_SIZE                 # Registros por batch (default: 25)
POST_RETRIES               # Tentativas por batch (default: 3)
BACKOFF_BASE               # Base exponencial (default: 1.5)
DRY_RUN                    # 'true' ou 'false' (default: false)
```

### 📁 `\bases\` - Pasta de Configuração (Novo - Fase 4)

**IMPORTANTE:** Todos os arquivos JSON de configuração **DEVEM estar em `\bases\`**

**Estrutura esperada:**

```
robo_download_neo/
├── bases/                         ← NOVA PASTA
│   ├── map_relative.json         ← Carregado daqui (OBRIGATÓRIO)
│   ├── nocodb_map.json           ← Carregado daqui (OBRIGATÓRIO)
│   ├── sql_map.json              ← Carregado daqui (OBRIGATÓRIO)
├── downloads/
├── logs/
├── .env
├── app.py
└── ...
```

**Migração (se upgrading de versão antiga):**
```bash
# 1. Criar pasta
mkdir bases

# 2. Mover JSONs
move map_relative.json bases/
move nocodb_map.json bases/
move sql_map.json bases/

# 3. Validar (app.py vai falhar se JSONs não encontrados - erro claro)
python app.py
```

### `map_relative.json` - XPaths

```json
{
  "login": {
    "username_field": "//input[@type='text' and @name='username']",
    "password_field": "//input[@type='password']",
    "otp_field": "//input[@placeholder='Código']",
    "login_button": "//button[contains(text(), 'Entrar')]"
  },
  "producao": {
    "panel": "//div[@data-tab='producao']",
    "date_picker": "//input[@name='dataInicio']",
    "search_button": "//button[@type='submit']",
    "download_link": "//a[contains(@href, 'exportacao')]"
  }
}
```

### `nocodb_map.json` - Mapeamento Excel

```json
{
  "ExportacaoProducao.xlsx": [
    "DATA", "CLIENTE", "PRODUTO", "QUANTIDADE", "VALOR", "PEDIDO_ID", "STATUS", "TAGS"
  ],
  "Exportacao Atividade.xlsx": [
    "DATA", "TIPO", "DESCRICAO", "RESPONSAVEL", "STATUS", "TAGS"
  ],
  "Exportacao Status.xlsx": [
    "DATA", "ATIVIDADE_ID", "STATUS_ANTERIOR", "STATUS_NOVO", "MOTIVO", "TAGS"
  ]
}
```

### `sql_map.json` - Mapeamento SQL

```json
{
  "ExportacaoProducao.xlsx": {
    "tabela": "EXPORTACAO_PRODUCAO",
    "colunas": ["DATA", "CLIENTE", "PRODUTO", "QUANTIDADE", "VALOR", ...]
  },
  "Exportacao Atividade.xlsx": {
    "tabela": "EXPORTACAO_ATIVIDADE",
    "colunas": ["DATA", "TIPO", "DESCRICAO", ...]
  },
  "Exportacao Status.xlsx": {
    "tabela": "EXPORTACAO_STATUS",
    "colunas": ["DATA", "ATIVIDADE_ID", "STATUS_ANTERIOR", ...]
  }
}
```

---

## Estrutura de Dados

### Dados de Entrada (Excel)

```
Headers normalizados por nocodb_map.json:
┌─────────────────────────────────────────┐
│ DATA │ CLIENTE │ PRODUTO │ QUANTIDADE   │
├─────────────────────────────────────────┤
│ 28/10/25 │ ABC Ltd │ Widget A │ 100     │
│ 28/10/25 │ XYZ Inc │ Widget B │ 50      │
└─────────────────────────────────────────┘
```

### Processamento

```python
records = [
    {
        'DATA': '2025-10-28 14:30:00',      # Convertido
        'CLIENTE': 'ABC Ltd',
        'PRODUTO': 'Widget A',
        'QUANTIDADE': '100',                # Convertido para string
        'VALOR': '',                        # None → ""
        'TAGS': 'extra_info | outro_campo'
    },
    ...
]
```

### Armazenamento SQL Server

```sql
INSERT INTO EXPORTACAO_PRODUCAO (DATA, CLIENTE, PRODUTO, QUANTIDADE, VALOR, CRIADO_EM)
VALUES ('2025-10-28 14:30:00', 'ABC Ltd', 'Widget A', '100', '', GETDATE());
```

---

## Integração SQL Server

### Conexão ODBC

```python
conn_string = (
    f'Driver={{ODBC Driver 18 for SQL Server}};'
    f'Server=servidor.local,1434;'
    f'Database=rpa_neocrm;'
    f'UID=usuario;'
    f'PWD=senha;'
    f'Encrypt=no;'
    f'TrustServerCertificate=no;'
    f'Connection Timeout=30;'
)
conn = pyodbc.connect(conn_string)
```

### Insert Parametrizado

```python
# Seguro contra SQL injection
insert_stmt = "INSERT INTO [EXPORTACAO_PRODUCAO] ([DATA], [CLIENTE], [PRODUTO]) VALUES (?, ?, ?)"
cursor.execute(insert_stmt, ['2025-10-28', 'ABC Ltd', 'Widget A'])
conn.commit()
```

### Índices Recomendados

```sql
CREATE INDEX IX_DATA ON EXPORTACAO_PRODUCAO([DATA]);
CREATE INDEX IX_CLIENTE ON EXPORTACAO_PRODUCAO([CLIENTE]);
CREATE INDEX IX_DATA ON EXPORTACAO_ATIVIDADE([DATA]);
CREATE INDEX IX_TIPO ON EXPORTACAO_ATIVIDADE([TIPO]);
CREATE INDEX IX_DATA ON EXPORTACAO_STATUS([DATA]);
CREATE INDEX IX_STATUS ON EXPORTACAO_STATUS([STATUS_NOVO]);
```

---

## Tratamento de Erros - Duplicatas (Novo - Fase 6)

### O Problema Original (Antes da Fase 6)

```
Batch com 25 registros, sendo 1 duplicata:
├─ INSERT registro 1 → OK ✅
├─ INSERT registro 2 → OK ✅
├─ INSERT registro 3 → ERRO: PRIMARY KEY duplicada ❌
├─ INSERT registro 4-25 → CANCELADOS (transação abortada)
└─ RESULTADO: 0/25 registros salvos ❌
```

### A Solução (Depois da Fase 6)

```python
# Per-Record Processing:
for idx, record in enumerate(batch, 1):
    try:
        cursor.execute(insert_stmt, values)
        batch_success_count += 1
    except pyodbc.IntegrityError as ie:
        # Duplicata = IGNORA (não vai resolver com retry)
        batch_duplicate_count += 1
        logger.debug(f"⚠️  DUPLICATA: Chave (47871899, 2025-05-27 16:12:58)")
    except Exception as e:
        # Erro real = REGISTRA
        batch_error_count += 1

conn.commit()  # Após processar TODOS

# RESULTADO: 24/25 registros salvos ✅, 1 ignorado como duplicata
```

**Quando Duplicata Ocorre:**
- ✅ Mesmo NUMERO + ENTROU já existe no banco
- ✅ Exportação de período sobreposto (ex: 90 dias que incluem dia anterior)
- ✅ Reexecução do robô (rodou 2x por acidente)

**O que o App Faz Agora:**
1. Tenta INSERT
2. Pega `pyodbc.IntegrityError` com "PRIMARY KEY"
3. **NÃO tenta retry** (não vai resolver)
4. Registra com debug level (em logs)
5. Continua próximo registro
6. Taxa de sucesso **não cai artificialmente** para 0%

---

## Fluxo de Erro - Comparação

### Erro Real (Retry Aplicado)

```
Tentativa 1: Connection timeout → Aguarda 1.5s
Tentativa 2: Connection timeout → Aguarda 2.25s
Tentativa 3: Connection timeout → FALHA (próxima batch)
```

### Duplicata (Sem Retry)

```
Tentativa 1: PRIMARY KEY violation → IGNORA (não retry)
[Continua próximo registro]
```

---

## Performance e Escalabilidade

### Benchmarks Típicos

| Operação | Tempo |
|----------|-------|
| Login + 2FA | 15-20s |
| Download 1 arquivo | 10-30s |
| Parse 1.000 linhas | 2-5s |
| Insert 1 batch (25 reg) | 0.5-1s |
| Execução total (3 arquivos) | 3-5 min |

### Limite de Escalabilidade

- **Batch size:** 25 (testado, balanceado)
- **Concurrent downloads:** 1 (sequencial, por design)
- **Registros/mês:** ~150k (típico)
- **Storage SQL:** ~100MB/ano (3 tabelas)

### Otimizações Possíveis

```python
# 1. Aumentar BATCH_SIZE para 50-100
#    Risco: Maior consumo de memória

# 2. Usar bulk insert
#    Requer: Extensão T-SQL

# 3. Paralelizar downloads
#    Risco: Complexidade; não recomendado por agora

# 4. Comprimir logs antigos
#    Benefício: Economizar disco
```

---

## Segurança

### Proteção contra SQL Injection
```python
# ✓ Seguro - Parametrizado
cursor.execute("INSERT INTO T ([Col]) VALUES (?)", [user_input])

# ✗ Inseguro - String formatting
cursor.execute(f"INSERT INTO T (Col) VALUES ('{user_input}')")
```

### Credenciais
```python
# ✓ Seguro - Em .env
db_password = os.getenv('DB_PASSWORD')

# ✗ Inseguro - Hardcoded
db_password = "Ctelecom2017"
```

### Logs
```python
# ✓ Seguro - Sem exposição
logger.info("Enviando batch para EXPORTACAO_PRODUCAO")

# ✗ Inseguro - Expõe credencial
logger.info(f"Conectando como {db_username}:{db_password}")
```

---

## Testes Unitários

### Testar Conexão
```python
import pyodbc
conn = get_mssql_connection()
assert conn is not None
conn.close()
```

### Testar Parse
```python
records = parse_export_producao('tests/fixtures/sample.xlsx')
assert len(records) > 0
assert 'DATA' in records[0]
```

### Testar Retry
```python
# Simular falha
with mock.patch('pyodbc.connect', side_effect=[Exception(), Exception(), Mock()]):
    stats = post_records_to_mssql([{'data': 'test'}])
    assert stats['success'] > 0  # Passou na 3ª tentativa
```

---

## Extensões Futuras

- [ ] Suporte a PostgreSQL
- [ ] Webhooks para notificações
- [ ] UI Web para monitoramento
- [ ] Backup automático
- [ ] Compressão de logs
- [ ] Suporte multi-arquivo simultâneo

---

**Última atualização:** Outubro 2025  
**Versão:** 1.0  
**Autor:** ViFigueiredo
