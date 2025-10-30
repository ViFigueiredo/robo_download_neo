# 🚀 COMEÇAR - Visão Geral

## 📌 O que é este projeto?

**ROBO DOWNLOAD NEO** é um sistema automático que:

1. **Faz login** em sistema corporativo (com 2FA/OTP)
2. **Baixa relatórios** em Excel (Status, Atividades, Produção)
3. **Processa dados** (normaliza colunas, mapeia para banco)
4. **Insere em SQL Server** (sem validação de chave primária)
5. **Executa sozinho** a cada 30 minutos (8h-22h)

---

## 🏗️ Arquitetura em 3 Passos

### 1. Download Automático
```
Browser (Selenium)
  ├─ Login com OTP
  ├─ Navegação (Vaadin UI)
  └─ Download 3 arquivos Excel
```

### 2. Processamento
```
Excel Files
  ├─ Parse (pandas + normalização)
  ├─ Mapeamento de colunas
  └─ Conversão para formato SQL
```

### 3. Armazenamento
```
SQL Server (192.168.11.200:1434)
  ├─ EXPORTACAO_PRODUCAO (53 colunas)
  ├─ EXPORTACAO_ATIVIDADE (25 colunas)
  └─ EXPORTACAO_STATUS (13 colunas)
```

---

## 📊 Estado Atual (30/10/2025)

### ✅ O que foi feito HOJE

| Hora | O que | Status |
|------|-------|--------|
| 10:47 | Fix SAWarning | ✅ |
| 12:28 | Removido constrains | ✅ |
| 13:41 | Banco finalizado | ✅ |

### Mudança Principal
```
❌ ANTES:  PK Composta → SAWarning → Lento
✅ DEPOIS: Sem constrains → Sem warnings → Rápido
```

---

## 🗂️ Banco de Dados (FINAL)

### 3 Tabelas

**EXPORTACAO_PRODUCAO** (53 colunas)
- `id` (PK auto-increment)
- NUMERO_ATIVIDADE, PEDIDO_VINCULO, ITEM, ... (sem constraints)
- DATA_IMPORTACAO (NOT NULL)

**EXPORTACAO_ATIVIDADE** (25 colunas)
- `id` (PK auto-increment)
- ATIVIDADE, DATA, USUARIO, ... (sem constraints)
- DATA_IMPORTACAO (NOT NULL)

**EXPORTACAO_STATUS** (13 colunas)
- `id` (PK auto-increment)
- NUMERO, ETAPA, PRAZO, SLA_HORAS, ... (sem constraints)
- DATA_IMPORTACAO (NOT NULL)

**Status:** 3 tabelas, 0 registros, pronto para dados

---

## 🔧 Como Usar

### Execute agora (1 min)
```bash
python app.py
```

Vai fazer:
- Login automático
- Download de 3 arquivos
- Parse dos dados
- Insert em SQL Server
- Log de resultado

### Validar dados (2 min)
```bash
# Terminal SQL Server
sqlcmd -S 192.168.11.200:1434 -d rpa_neocrm

# Query SQL
SELECT COUNT(*) AS total FROM EXPORTACAO_STATUS;
```

Esperado: **60.815+ registros**

---

## 📁 Arquivos Principais

```
app.py ⭐
  └─ Aplicação principal (login, download, parse, insert)

models/
  ├─ models_generated.py ⭐
  │   └─ ORM models (3 tabelas)
  └─ models.py
      └─ Fallback (idêntico)

gerar_models_dinamicos.py
  └─ Gera models_generated.py automaticamente

migrate_tables.py
  └─ Cria/sincroniza tabelas no banco
```

---

## ⚙️ Configuração (.env)

```ini
# Sistema alvo
SYS_URL=http://...
SYS_USERNAME=seu_usuario
SYS_PASSWORD=sua_senha
SYS_SECRET_OTP=seu_token_2fa

# Banco de dados
DB_SERVER=192.168.11.200:1434
DB_DATABASE=rpa_neocrm
DB_USERNAME=sa
DB_PASSWORD=sua_senha

# Browser
BROWSER=chrome
HEADLESS=false
```

---

## 🚨 Próximos Passos

### Agora (immediately)
1. Ler este arquivo ✅
2. Ler `2_REFERENCIA.md` (se tiver dúvida)
3. Executar: `python app.py`

### Depois
1. Validar registros em SQL Server
2. Testar reprocessamento
3. Agendar em production

### Se der erro
1. Ver logs em `logs/`
2. Ler `2_REFERENCIA.md` (Seção "Problemas")
3. Ver `3_DETALHES.md` (Seção "Troubleshooting")

---

## 📞 Próxima Leitura

- ❓ Tenho dúvida? → `2_REFERENCIA.md`
- 🔍 Quer detalhes? → `3_DETALHES.md`
- 📱 Quer executar? → `python app.py`

---

**Status:** 🟢 PRONTO  
**Última atualização:** 30 de outubro de 2025
