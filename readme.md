# 🤖 ROBO DOWNLOAD NEO

> **Sistema de automação empresarial que realiza downloads automatizados de relatórios, processa dados e integra com SQL Server**

---

## 🎯 O que é?

Um **robô web automatizado** que:

1. **Faz login** em sistema corporativo com 2FA/OTP
2. **Baixa relatórios** em Excel (Status, Atividades, Produção)
3. **Processa dados** (normaliza, mapeia, valida)
4. **Armazena em SQL Server** (3 tabelas estruturadas)
5. **Executa sozinho** a cada 30 minutos (8h-22h)

---

## ✨ Principais Características

| Característica | Detalhe |
|---------------|---------| 
| **Login Automatizado** | 2FA/OTP, retry automático |
| **Download Inteligente** | Retry (3x, 60s delay), sem falhas |
| **Parse Robusto** | Normalização de headers, mapeamento flexível |
| **Inserção Rápida** | Sem constrains, per-record processing |
| **Logging Completo** | JSONL estruturado, rastreamento de linha |
| **Agendamento** | Executa automaticamente a cada 30min |
| **Sem Erros** | Duplicatas são ignoradas, batch continua |

---

## 🚀 Começar AGORA (2 min)

```bash
# 1. Clonar repositório
git clone <url>
cd robo_download_neo

# 2. Copiar configuração
copy .env.example .env
# Editar .env com suas credenciais

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
python app.py
```

**Resultado esperado:** Login automático → Download 3 arquivos → Parse → Insert 60.815+ registros

**⚡ Como funciona:**
- O arquivo `.env` é carregado **dinamicamente** em runtime (não compilado no exe)
- Entry point: `scripts/config_embutida.py` → carrega variáveis → executa `app.py`
- Se `.env` não encontrado, tenta `os.environ` (para produção com variáveis de sistema)

---

## 📚 Documentação

**Toda documentação está em `/docs` - Estrutura simples e organizada:**

| Arquivo | Propósito | Tempo |
|---------|-----------|-------|
| **docs/README.md** | 🗺️ Índice e navegação | 2 min |
| **docs/1_INICIO.md** | 🆕 Para quem é novo | 5 min |
| **docs/2_REFERENCIA.md** | ⚙️ Referência rápida (comandos/problemas) | 5 min |
| **docs/3_DETALHES.md** | 📖 Tudo em profundidade | 20 min |
| **docs/REORGANIZACAO_CONCLUIDA.md** | 📊 Histórico de mudanças | 3 min |

👉 **Comece por:** [`docs/README.md`](./docs/README.md) ou [`docs/1_INICIO.md`](./docs/1_INICIO.md)

---

## 🏗️ Arquitetura em 3 Camadas

```
┌─────────────────────────────────────┐
│ CAMADA 1: Automação Web             │
│ ├─ Selenium (Chrome/Edge)           │
│ ├─ Login com 2FA/OTP                │
│ ├─ Download com retry (3x, 60s)    │
│ └─ Vaadin UI Framework              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ CAMADA 2: Processamento de Dados    │
│ ├─ Pandas (read_excel)              │
│ ├─ Normalização de headers          │
│ ├─ Mapeamento de colunas            │
│ └─ Conversão de tipos               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ CAMADA 3: Armazenamento (SQL)       │
│ ├─ SQLAlchemy ORM                   │
│ ├─ SQL Server 2022                  │
│ ├─ 3 tabelas (Produção, Atividade)  │
│ └─ Per-record processing (sem crash)│
└─────────────────────────────────────┘
```

---

## 📊 Banco de Dados

### 3 Tabelas Estruturadas

**EXPORTACAO_PRODUCAO** (53 colunas)
- Dados de pedidos, clientes, produtos
- ~10.000+ registros por execução

**EXPORTACAO_ATIVIDADE** (25 colunas)
- Atividades operacionais
- ~20.000+ registros por execução

**EXPORTACAO_STATUS** (13 colunas)
- Histórico de movimentações
- ~60.815+ registros por execução ⭐

**Características:**
- ✅ Sem constraints (apenas `id` auto-increment)
- ✅ Inserção rápida
- ✅ Duplicatas permitidas (não retorna erro)
- ✅ Per-record processing (1 erro não paralisa lote)

---

## 🔧 Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| **Automação Web** | Selenium | 4.x |
| **Browser** | Chrome/Edge | Latest |
| **Processamento** | Pandas | 2.3.3 |
| **ORM** | SQLAlchemy | 2.0.25 |
| **Banco de Dados** | SQL Server | 2022 |
| **Agendamento** | Schedule | 1.x |
| **Python** | 3.10+ | |

---

## 📁 Estrutura do Projeto

```
robo_download_neo/
├── README.md ........................... Você está aqui!
├── .env.example ........................ Template de configuração
├── app.py ............................. Aplicação principal
├── requirements.txt ................... Dependências Python
│
├── docs/ .............................. Documentação (5 arquivos)
│   ├── README.md (índice)
│   ├── 1_INICIO.md
│   ├── 2_REFERENCIA.md
│   ├── 3_DETALHES.md
│   └── REORGANIZACAO_CONCLUIDA.md
│
├── bases/ ............................. Configuração JSON (obrigatório)
│   ├── map_relative.json ............. XPaths Selenium
│   └── sql_map.json .................. Mapeamento Excel → SQL (colunas e tabelas)
│
├── downloads/ ......................... Arquivos Excel baixados
├── logs/ .............................. Logs estruturados (JSONL)
├── tests/ ............................. Suite de testes
└── .github/
    └── copilot-instructions.md ....... Instruções para devs
```

---

## 🎯 Fluxo de Execução

```
1. INICIALIZAÇÃO
   ├─ Validar .env
   ├─ Criar pastas
   └─ Limpar downloads antigos

2. LOGIN
   ├─ Preencher credenciais
   ├─ Enviar OTP (2FA)
   └─ Aguardar confirmação

3. DOWNLOAD (com retry)
   ├─ Atividades Status (90 dias) .... 3x tentativas
   ├─ Atividades (90 dias) ........... 3x tentativas
   └─ Produção (92 dias) ............ 3x tentativas

4. PROCESSAMENTO
   ├─ Parse Excel (pandas)
   ├─ Normalizar headers
   ├─ Mapear colunas
   └─ Converter tipos

5. INSERÇÃO
   ├─ Conectar ao SQL Server
   ├─ Inserir em batches (25 registros)
   ├─ Per-record processing
   └─ Logging detalhado

6. AGENDAMENTO
   ├─ Próxima execução em 30min
   └─ Entre 8h-22h
```

---

## ⚡ Comandos Principais

```bash
# Executar aplicação completa
python app.py

# Verificar status do banco de dados
python migrate_tables.py --status

# Criar/sincronizar tabelas
python migrate_tables.py

# Limpar tabelas (CUIDADO!)
python migrate_tables.py --drop

# Regenerar modelos ORM
python gerar_models_dinamicos.py

# Testar parsing (sem insert)
python tests/test_parse_producao.py

# Testar insert (sem efeitos)
python tests/test_post_producao.py --dry-run
```

---

## 🔐 Configuração (.env)

```ini
# Sistema Corporativo
SYS_URL=http://seu-sistema.com
SYS_USERNAME=seu_usuario
SYS_PASSWORD=sua_senha
SYS_SECRET_OTP=seu_token_2fa

# Banco de Dados (SQL Server)
DB_SERVER=192.168.11.200:1434
DB_DATABASE=rpa_neocrm
DB_USERNAME=sa
DB_PASSWORD=sua_senha
DB_DRIVER=ODBC Driver 17 for SQL Server

# Browser & Timeouts
BROWSER=chrome              # ou edge
HEADLESS=false
TIMEOUT_DOWNLOAD=60        # segundos

# Inserção
BATCH_SIZE=25              # registros por batch
POST_RETRIES=3
BACKOFF_BASE=1.5

# Teste
DRY_RUN=false              # true = simula, false = executa real
```

---

## 📊 Métricas de Performance

| Operação | Tempo | Volume |
|----------|-------|--------|
| Login | ~30 seg | - |
| Download (3 arquivos) | ~5 min | ~90.815 registros |
| Parse | ~10 seg | 90.815 registros |
| Inserção | ~5 min | 90.815 registros |
| **Total** | **~11 min** | **90.815 registros** |

**Taxa de inserção:** ~300 registros/seg (sem constrains)

---

## 🐛 Tratamento de Erros

| Erro | Comportamento | Solução |
|------|---------------|---------|
| **Elemento não encontrado** | Retry 3x, timeout | Ver logs, atualizar XPath |
| **Login falha** | Pula execução | Verificar credenciais/2FA |
| **Download falha** | Retry automático | Verificar conexão, permissões |
| **Duplicata (PRIMARY KEY)** | ✅ Ignora, continua | Comportamento esperado |
| **Conexão SQL falha** | Retry com backoff | Verificar server, credenciais |

---

## ✅ Status Atual (30/10/2025)

| Aspecto | Status |
|--------|--------|
| **Código** | ✅ Pronto para produção |
| **Banco de Dados** | ✅ 3 tabelas sincronizadas |
| **Modelos ORM** | ✅ Sem erros, sem warnings |
| **Documentação** | ✅ Consolidada (5 arquivos) |
| **Testes** | ✅ Suite completa |
| **Automação** | ✅ Agendamento funcional |
| **Sistema** | 🟢 **PRODUÇÃO** |

---

## 🎓 Próximas Ações

### Para Iniciantes
1. Leia: [`docs/1_INICIO.md`](./docs/1_INICIO.md) (5 min)
2. Configure: `.env` com suas credenciais
3. Execute: `python app.py`
4. Valide: Verificar registros em SQL Server

### Para Developers
1. Leia: [`docs/3_DETALHES.md`](./docs/3_DETALHES.md) (arquitetura completa)
2. Estude: [`app.py`](./app.py) (fluxo principal)
3. Explore: [`models/models_generated.py`](./models/models_generated.py) (ORM)
4. Customize: JSONs em `bases/` conforme necessário

### Para Troubleshooting
1. Verifique: [`docs/2_REFERENCIA.md`](./docs/2_REFERENCIA.md) (problemas comuns)
2. Consulte: Logs em `logs/` (JSONL estruturado)
3. Debug: Screenshots em `element_screenshots/`

---

## 🤝 Contribuindo

Ao fazer mudanças no código:

1. **Atualizar documentação** correspondente em `/docs`
2. **Não criar novo arquivo `.md`** - atualizar seção existente
3. **Adicionar testes** para nova funcionalidade
4. **Seguir padrões** em [`.github/copilot-instructions.md`](./.github/copilot-instructions.md)

---

## 📝 Informações do Projeto

| Informação | Valor |
|-----------|-------|
| **Repositório** | ViFigueiredo/robo_download_neo |
| **Branch** | sql_server |
| **Versão** | 1.1 |
| **Python** | 3.10+ |
| **Última atualização** | 30 de outubro de 2025 |
| **Status** | 🟢 Produção |

---

## 📞 Suporte & Dúvidas

| Dúvida | Caminho |
|--------|---------|
| Como começar? | [`docs/1_INICIO.md`](./docs/1_INICIO.md) |
| Como executar? | [`docs/2_REFERENCIA.md`](./docs/2_REFERENCIA.md) |
| Tenho erro | [`docs/2_REFERENCIA.md`](./docs/2_REFERENCIA.md#-problemas-comuns) |
| Quer entender? | [`docs/3_DETALHES.md`](./docs/3_DETALHES.md) |

---

## 📄 Licença & Informações

**Desenvolvido para:** Automação empresarial de relatórios  
**Autor:** ViFigueiredo  
**Data:** 2025  
**Status:** ✅ Pronto para Produção

---

**Última atualização:** 30 de outubro de 2025  
**Documentação:** ✅ Organizada e consolidada  
**Sistema:** 🟢 **PRONTO PARA USAR**
