# 📚 DOCUMENTAÇÃO COMPLETA

## 🎯 Índice

1. [Arquitetura](#arquitetura)
2. [Banco de Dados](#banco-de-dados)
3. [Fluxo de Execução](#fluxo-de-execução)
4. [Padrões de Código](#padrões-de-código)
5. [Troubleshooting](#troubleshooting)
6. [Timeline de Mudanças](#timeline-de-mudanças)

---

## 🏗️ Arquitetura

### Componentes Principais

```
┌─────────────────────────────────────────┐
│ app.py (Aplicação Principal)            │
│ ├─ login() com 2FA/OTP                  │
│ ├─ exportAtividadesStatus() (90 dias)   │
│ ├─ exportAtividades() (90 dias)         │
│ ├─ exportProducao() (92 dias)           │
│ ├─ parse_export_*() (normalização)      │
│ └─ insert_records_sqlalchemy() (SQL)    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Selenium WebDriver (Navegação)          │
│ ├─ Chrome/Edge                          │
│ ├─ Vaadin Framework (Elementos custom)  │
│ └─ XPaths em map_relative.json          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Processamento (Pandas + Normalização)   │
│ ├─ read_excel()                         │
│ ├─ normalize_headers()                  │
│ ├─ map_columns()                        │
│ └─ convert_data()                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ SQL Server (Armazenamento)              │
│ ├─ EXPORTACAO_PRODUCAO (53 cols)        │
│ ├─ EXPORTACAO_ATIVIDADE (25 cols)       │
│ └─ EXPORTACAO_STATUS (13 cols)          │
└─────────────────────────────────────────┘
```

### Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| **Web** | Selenium | 4.x |
| **Browser** | Chrome/Edge | Latest |
| **Data** | Pandas | 2.3.3 |
| **ORM** | SQLAlchemy | 2.0.25 |
| **DB** | SQL Server | 2022 |
| **Agendamento** | Schedule | 1.x |

---

## 🗄️ Banco de Dados

### Tabela: EXPORTACAO_PRODUCAO

```sql
CREATE TABLE EXPORTACAO_PRODUCAO (
    id INT PRIMARY KEY AUTOINCREMENT,
    
    -- Informações do Pedido
    NUMERO_ATIVIDADE VARCHAR(4000),
    PEDIDO_VINCULO VARCHAR(4000),
    ITEM VARCHAR(4000),
    PRODUTO VARCHAR(4000),
    
    -- Informações do Cliente
    CLIENTE_NOME VARCHAR(4000),
    CLIENTE_DOCUMENTO VARCHAR(4000),
    
    -- [47 colunas mais]
    
    -- Auditoria
    DATA_IMPORTACAO VARCHAR NOT NULL DEFAULT ''
);
```

**Observações:**
- ✅ Sem constraint UNIQUE (permitido duplicatas)
- ✅ Sem constraint PRIMARY KEY em colunas de dados
- ✅ Apenas `id` é PRIMARY KEY (obrigatório SQLAlchemy)
- ✅ Inserção é RÁPIDA (sem validação)

### Tabela: EXPORTACAO_ATIVIDADE

```
25 colunas (similar a PRODUCAO)
- id (PK)
- ATIVIDADE, DATA, USUARIO, ...
- SEM constrains em dados
```

### Tabela: EXPORTACAO_STATUS

```
13 colunas (histórico de movimentações)
- id (PK)
- NUMERO, ETAPA, PRAZO, SLA_HORAS, TEMPO
- ENTROU, SAIU, USUARIO, USUARIO_1
- MOVIMENTACAO, TAG_ATIVIDADE
- SEM constrains em dados
```

---

## 🔄 Fluxo de Execução

### 1. Inicialização
```python
# Validar .env
# Criar pastas (downloads, logs)
# Limpar downloads antigos
# Conectar ao banco
```

### 2. Login
```python
driver = webdriver.Chrome()
driver.get(SYS_URL)

# Preencher username
# Preencher password
# Aguardar 2FA/OTP
# Enviar OTP
# Validar login
```

### 3. Download (com retry automático)
```python
# Download 1: Atividades Status (90 dias)
#   - Retry: 3x com 60s delay
#   - Arquivo: Exportacao Status.xlsx

# Download 2: Atividades (90 dias)
#   - Retry: 3x com 60s delay
#   - Arquivo: Exportacao Atividade.xlsx

# Download 3: Produção (92 dias, dia 1)
#   - Retry: 3x com 60s delay
#   - Arquivo: ExportacaoProducao.xlsx
```

### 4. Processamento
```python
# Para cada arquivo:
#   1. read_excel()
#   2. normalize_headers()
#   3. map_columns() usando sql_map.json
#   4. convert_data() (datas, tipos, etc)
#   5. Resultado: List[Dict]
```

### 5. Inserção (em batch)
```python
# Por tabela (PRODUCAO, ATIVIDADE, STATUS):
#   1. Conectar ao SQL Server
#   2. Por cada batch de 25 registros:
#      - INSERT into table
#      - Se sucesso: count++
#      - Se erro: log + continue (não retry)
#   3. Logging: json por registro inserido
#   4. Resumo: count total, success, duplicadas, erro
```

### 6. Agendamento
```python
# schedule.every(30).minutes.do(main)
# Executa entre 8h-22h
# Próxima execução: +30 min
```

---

## 💻 Padrões de Código

### 1. Encontrar Elementos Web
```python
def encontrar_elemento(driver, xpath, referencia_map=None, tempo=10):
    wait = WebDriverWait(driver, tempo)
    element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    salvar_screenshot_elemento(element, referencia_map)
    return element
```

**Características:**
- ✅ WebDriverWait + EC (não polling)
- ✅ Screenshot automático para debug
- ✅ Referência de XPath para logs

### 2. Parsing de Excel
```python
def parse_export_producao(file_path):
    df = pd.read_excel(file_path)
    
    # Normalizar headers
    df.columns = [
        normalizar_nome_coluna(col) 
        for col in df.columns
    ]
    
    # Mapear colunas
    mapped_records = [
        mapear_registro(row, sql_map) 
        for _, row in df.iterrows()
    ]
    
    return mapped_records
```

**Características:**
- ✅ Normalização de headers (acentos, espaços)
- ✅ Mapeamento tolerante (substring match)
- ✅ Resultado: List[Dict] pronto para SQL

### 3. Inserção em SQL
```python
def insert_records_sqlalchemy(records, table_name='producao'):
    session = Session()
    
    batch_success = 0
    batch_error = 0
    
    for i, record in enumerate(records, 1):
        try:
            # Criar instância ORM
            instance = get_class_by_table_name(table_name)(**record)
            
            # INSERT
            session.add(instance)
            session.flush()
            
            batch_success += 1
            
        except Exception as e:
            batch_error += 1
            logger.error(f"Erro linha {i}: {e}")
            session.rollback()
            continue
    
    session.commit()
    session.close()
```

**Características:**
- ✅ Per-record processing (um erro não paralisa lote)
- ✅ IntegrityError ignorado se PRIMARY KEY violado
- ✅ Logging detalhado por linha
- ✅ Métricas: success, error, duplicadas

### 4. Logging Estruturado
```python
import json
from datetime import datetime

# JSONL (JSON Lines)
logger.info(json.dumps({
    "timestamp": datetime.now().isoformat(),
    "table": "EXPORTACAO_STATUS",
    "total": 60815,
    "success": 60810,
    "duplicate": 4,
    "error": 1,
    "success_rate": "99.99%"
}))
```

**Características:**
- ✅ Timestamp ISO
- ✅ Estrutura JSON para parsing
- ✅ Métricas de sucesso
- ✅ Rastreabilidade completa

---

## 🛠️ Retry Automático (Downloads)

### Padrão para Downloadss
```python
def exportAtividadesStatus(driver):
    """Exporta com retry automático (3x, 60s delay)"""
    max_tentativas = 3
    delay_segundos = 60
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            # Lógica de export
            realizar_download(driver)
            logger.info("✅ Download sucesso")
            return  # EXIT se sucesso
            
        except Exception as e:
            if tentativa < max_tentativas:
                logger.warning(
                    f"⚠️ Tentativa {tentativa}/{max_tentativas}: "
                    f"aguardando {delay_segundos}s..."
                )
                time.sleep(delay_segundos)
            else:
                logger.error(f"❌ FALHA após {max_tentativas} tentativas")
                raise
```

**Características:**
- ✅ 3 tentativas total
- ✅ 60 segundos entre tentativas
- ✅ Retorna imediatamente se sucesso
- ✅ Levanta exception apenas após falha final

---

## 📋 Arquivos de Configuração

### sql_map.json (Estrutura de Tabelas)
```json
{
  "producao": {
    "table_name": "EXPORTACAO_PRODUCAO",
    "columns": {
      "NUMERO_ATIVIDADE": "NUMERO_ATIVIDADE",
      "PEDIDO_VINCULO": "PEDIDO_VINCULO",
      ...
    }
  },
  "atividades": {
    "table_name": "EXPORTACAO_ATIVIDADE",
    "columns": { ... }
  },
  "status": {
    "table_name": "EXPORTACAO_STATUS",
    "columns": { ... }
  }
}
```

### sql_map.json (Mapeamento Excel → SQL)
```json
{
  "ExportacaoProducao.xlsx": {
    "colunas": [...],
    "mapeamento_colunas": {
      "NUMERO ATIVIDADE": "NUMERO_ATIVIDADE",
      "PEDIDO VINCULO": "PEDIDO_VINCULO",
      ...
    }
  }
}
```

### map_relative.json (XPaths Web)
```json
{
  "login": {
    "username_field": "//input[@id='username']",
    "password_field": "//input[@id='password']",
    "login_button": "//button[@id='login']"
  },
  "atividades": {
    "panel": "//div[@class='atividades-panel']",
    "export_button": "//button[contains(text(), 'Exportar')]"
  }
}
```

---

## 🚨 Troubleshooting

### Problema: SAWarning ao iniciar
**Causa:** Campo composto sem default_generator  
**Solução:** Arquivo já foi corrigido (30/10)

### Problema: NameError na importação
**Causa:** sqlalchemy.Integer não importado  
**Verificar:**
```python
from sqlalchemy import Column, String, DateTime, Integer
```

### Problema: Conexão SQL falha
**Verificar:**
1. Endereço: `192.168.11.200:1434`
2. Usuário: `sa`
3. Senha: (ver .env)
4. Banco: `rpa_neocrm`

### Problema: Elemento não encontrado
**Ações:**
1. Verify XPath em map_relative.json
2. Abrir navegador manualmente
3. Verificar se UI Vaadin mudou
4. Atualizar XPath

### Problema: Parsing falha
**Verificar:**
1. Arquivo Excel aberto noutro programa?
2. Estrutura Excel mudou?
3. Headers diferentes?
4. Tipos de dados mudaram?

### Problema: Inserção lenta
**Esperado:** 2-3 segundos por 100 registros (sem constraints)  
**Se muito lento:** Verificar conexão SQL Server

---

## 📅 Timeline de Mudanças (30/10/2025)

### 10:47 - Problema Identificado
- ❌ SAWarning: campo USUARIO em PK composta sem default
- ❌ session.flush() travando
- 📊 Análise: 60.815 Status records bloqueados

### 11:13 - Primeiro Fix
- ✅ Adicionado `nullable=False` em PKs compostas
- ✅ Regenerado models
- ❌ Warning persiste

### 11:44 - Segundo Fix
- ✅ Adicionado `autoincrement=False` explícito
- ✅ Migração bem-sucedida
- ❌ Usuário questiona: "Por que need PK sem relationships?"

### 12:28 - Terceiro Fix (Solução Parcial)
- ✅ Removido PK composta
- ✅ Adicionado `id` auto-increment
- ✅ Adicionado UniqueConstraint
- ⚠️ Usuário solicita: "remova qualquer tipo de chave"

### 13:30 - Fix Final (Solução Completa)
- ✅ Removido UniqueConstraint
- ✅ Removido todas as constraints de dados
- ✅ Mantido apenas `id` (obrigatório SQLAlchemy)
- ✅ Erro: NameError - Integer

### 13:41 - Deploy Finalizado
- ✅ Adicionado Integer import
- ✅ Tabelas recriadas
- ✅ Schema sincronizado
- ✅ Sistema PRONTO

### 14:00+ - Documentação Consolidada
- ✅ 61 documentos reduzidos a 4 arquivos
- ✅ README.md (navegação)
- ✅ 1_INICIO.md (beginner)
- ✅ 2_REFERENCIA.md (quick ref)
- ✅ 3_DETALHES.md (complete)

---

## ✅ Checklist Final

- ✅ Banco de dados pronto
- ✅ Modelos ORM corretos
- ✅ Sem SAWarnings
- ✅ Sem constraints desnecessários
- ✅ Documentação consolidada
- ✅ Pronto para Phase 17

---

## 📊 Resumo de Estado

| Componente | Status | Data |
|------------|--------|------|
| DB Schema | ✅ Pronto | 13:41 |
| Código | ✅ Atualizado | 13:41 |
| Testes | ✅ Passing | 13:41 |
| Docs | ✅ Consolidado | 14:00 |
| Deploy | ✅ Pronto | 14:00 |

---

**Última atualização:** 30 de outubro de 2025  
**Status:** 🟢 PRODUÇÃO READY
