# GitHub Copilot Instructions - Robô de Download Neo

---

## 🚨 INSTRUÇÃO CRÍTICA - LEI FUNDAMENTAL

### ⚠️ REGRA ABSOLUTA: NÃO CRIAR DOCUMENTAÇÃO NA RAIZ DO PROJETO

**LEIA E ENTENDA:**

```
❌ PROIBIDO:
   Criar qualquer arquivo .md, .txt ou documentação na RAIZ do projeto
   Exemplos ERRADOS:
   • ANALISE_ERROS.md (na raiz)
   • RESUMO.txt (na raiz)
   • RELATORIO.md (na raiz)
   • Qualquer novo .md fora de docs/

✅ OBRIGATÓRIO:
   Criar TODA documentação em: docs/ (subdiretório)
   Exemplos CORRETOS:
   • docs/ANALISE_ERROS.md
   • docs/RESUMO.txt
   • docs/RELATORIO.md
   
🔔 EXCEÇÃO ÚNICA:
   .github/copilot-instructions.md (já está fora da raiz, mantém-se aqui)
```

---

## 📋 Contexto do Projeto

**Sistema de automação web empresarial** que:
- Realiza **login automatizado** com 2FA/OTP
- **Baixa relatórios** em Excel de sistema corporativo (Vaadin)
- **Processa dados** com normalização e mapeamento flexível
- **Armazena em SQL Server** (3 tabelas, 60.815+ registros)
- **Executa agendado** a cada 30 minutos entre 8h-22h

**Stack:** Python 3.11 + Selenium + Pandas + SQLAlchemy + SQL Server 2022 + PyInstaller

## 🎯 Objetivos Principais

- **Automação Web**: Login automatizado com 2FA/OTP e navegação por interface Vaadin
- **Download de Relatórios**: Extração de dados de Produção, Atividades e Status de Atividades
- **Processamento de Dados**: Parse flexível de arquivos Excel com mapeamento dinâmico
- **Integração Database**: Envio em batches para SQL Server com retry e logging detalhado
- **Execução Agendada**: Runs a cada 30 minutos entre 8h-22h

## 🏗️ Arquitetura e Componentes (FINAL - Fase 14)

### Estrutura Principal
```
🎯 ENTRY POINT: scripts/config_embutida.py
   └─→ Carrega .env dinamicamente
   └─→ Popula os.environ com 18 variáveis de configuração
   └─→ Executa app.py

app.py                      # Aplicação principal com toda a lógica
bases/                      # 📁 JSONs de configuração
  ├── map_relative.json     # XPaths relativos (Vaadin)
  └── sql_map.json          # Mapeamento SQL (tabelas/colunas)

📦 OUTPUTS (gerados automaticamente):
  ├── dist/robo_neo.exe     # Executável único (34.1 MB)
  ├── logs/                 # Logs estruturados em JSONL
  ├── downloads/            # Arquivos Excel baixados
  └── LEIA_ME.txt           # Instruções automáticas

downloads/          # 📁 Arquivos Excel baixados
logs/               # 📁 Logs estruturados em JSONL
tests/              # 📁 Suite completa de testes
scripts/            # 📁 Scripts utilitários
  ├── config_embutida.py    # 🔑 Carregador dinâmico de .env
  ├── robo_neo.spec         # 📦 Especificação PyInstaller
  ├── empacotar_robo_neo.bat # 📦 Script build (Windows)
  ├── validar_build.py      # ✅ Validador de build
  └── gerar_xpath_relativo.py # 🔍 Gerador de XPaths

.env                # 🔐 Configurações sensíveis (carregadas dinamicamente)
```

**⚡ IMPORTANTE (Fase 8-14):** 
- **Credenciais:** Carregadas **DINAMICAMENTE** do `.env` em runtime (NOT hardcoded)
- **Configuração:** Entry point `scripts/config_embutida.py` antes de `app.py`
- **Fallback:** Se `.env` ausente, tenta `os.environ` (para produção)
- **JSONs:** APENAS `sql_map.json` + `map_relative.json` em `bases/`

### Tecnologias Core
- **Selenium WebDriver** (Chrome/Edge) - Automação web
- **Pandas** - Processamento Excel
- **PyODBC** - Conexão SQL Server (substituiu NocoDB)
- **Schedule** - Agendamento de tasks
- **PyInstaller** - Empacotamento executável
- **SQLAlchemy** - ORM para SQL Server

## � Build e Empacotamento (FINAL - Fase 13)

### Estrutura do Build Final
```
dist/
├── robo_neo.exe          # ✅ Executável único (34.1 MB)
├── logs/                 # Auto-criado em runtime
├── downloads/            # Auto-criado em runtime
└── LEIA_ME.txt           # Instruções auto-geradas
```

**⚡ IMPORTANTE (Fase 13):**
- **Arquivo único:** `robo_neo.exe` está DIRETAMENTE em `dist/` (sem subpasta)
- **Sem COLLECT():** `robo_neo.spec` modificado para usar APENAS `EXE()` block
- **Tamanho:** 34.1 MB (otimizado)
- **Autossuficiente:** Inclui todas as dependências Python compiladas

### Como Construir o Executável

**Pré-requisitos:**
```bash
pip install pyinstaller>=6.0
pip install -r requirements.txt
```

**Comando de Build (Windows):**
```batch
# Na raiz do projeto:
scripts\empacotar_robo_neo.bat

# OU manualmente:
pyinstaller "scripts\robo_neo.spec" --distpath dist --workpath build -y
```

**Validação do Build:**
```bash
# Verificar se foi construído corretamente:
python scripts/validar_build.py

# Executar o .exe:
dist\robo_neo.exe
```

**⚠️ Possíveis Problemas:**

| Erro | Causa | Solução |
|------|-------|---------|
| `ModuleNotFoundError` em runtime | Dependência não incluída no `.exe` | Adicionar em `robo_neo.spec` hidden_imports |
| `[HY001]` (SQL Server timeout) | Conexão ODBC lenta | Aumentar `TIMEOUT_DOWNLOAD` no `.env` |
| Arquivo não baixa | Overlay interceptando click | Testar com `HEADLESS=false` e screenshot |

### Arquivo robo_neo.spec (FINAL)
```python
# CRÍTICO: SEM COLLECT() - apenas EXE()
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='robo_neo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
# ✅ Resultado: Single exe em dist/ (sem pasta robo_neo/)
```

## �🔧 Padrões de Código

### 1. Função de Elementos Web
```python
def encontrar_elemento(driver, xpath, referencia_map=None, tempo=10):
    # Sempre usar WebDriverWait com EC
    # Incluir referencia_map para logs
    # Salvar screenshot para debug
```

### 2. XPaths Relativos
- Usar `map_relative.json` para todos os seletores
- XPaths absolutos robustos para framework Vaadin
- Referências organizadas hierarquicamente (login.username_field, atividades.panel)

### 3. Processamento de Dados
```python
def parse_export_producao(file_path):
    # Usar pandas.read_excel()
    # Normalizar headers (acentos, pontuação)
    # Mapeamento tolerante com sql_map.json
    # Formato de data: "%Y-%m-%d %H:%M:%S"
```

### 4. Envio de APIs
```python
def post_records_to_mssql(records, table_name='producao', file_name=None):
    # Conectar ao SQL Server usando pyodbc
    # Usar sql_map.json para determinar tabela e colunas
    # Processar em batches (BATCH_SIZE)
    # NOVO (Fase 6): Por-RECORD processing com IntegrityError handling
    #   - Cada registro processado individualmente
    #   - IntegrityError + PRIMARY KEY = IGNORA (não retry)
    #   - Outro erro = tenta retry com backoff
    #   - Contadores: batch_success_count, batch_duplicate_count, batch_error_count
    # NOVO: Rastreamento de linha (number_line) para cada registro
    #   - _line_number adicionado em parse_export_producao (linha do Excel)
    #   - _file_name adicionado (nome do arquivo)
    #   - Logs de erro mostram: qual linha, qual arquivo, qual dado falhou
    # Logging em JSONL estruturado
    # NOVO (Fase 5): Taxa de sucesso em porcentagem
    # Suporte a DRY_RUN
```

### 5. Download com Retry Automático (Novo - Fase 8)
```python
def exportAtividadesStatus(driver):
    """Exporta com retry automático (3 tentativas, 1 min delay)."""
    max_tentativas = 3
    delay_segundos = 60
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            # Lógica de export
            realizar_download(driver)
            logger.info("✅ Arquivo baixado com sucesso!")
            return  # Exit imediato se sucesso
        except Exception as e:
            if tentativa < max_tentativas:
                logger.warning(f"⚠️ Tentativa {tentativa}/{max_tentativas}: aguardando {delay_segundos}s...")
                time.sleep(delay_segundos)
            else:
                logger.error(f"❌ FALHA FINAL após {max_tentativas} tentativas")
                raise
```

**Padrão de retry para downloads (exportAtividadesStatus, exportAtividades, exportProducao):**
- 3 tentativas total
- 60 segundos de delay entre tentativas
- Retorna imediatamente se sucesso
- Levanta exception apenas após todas as tentativas falharem
- **Ver:** `docs/ESTRATEGIA_RETRY_DOWNLOADS.md` para detalhes completos

### 6. Logging Estruturado
- Console + arquivo para execução
- JSONL para dados enviados/falhas (NOVO Fase 5: com batch_num, record_num)
- **NOVO: Rastreamento de origem** (file, line_number para cada registro)
  - Cada registro sabe sua linha original no Excel
  - Logs de erro incluem: `arquivo.xlsx linha 42`
  - JSONL inclui field `source: {file, line}` para auditoria
- Screenshots automáticos de elementos
- Resumos de envio com métricas e taxa de sucesso em %
- Emojis para indicadores visuais (✅, ❌, ⚠️, 📊)

## 🛠️ Convenções de Desenvolvimento

### Variáveis de Ambiente
```env
# Sistema alvo
SYS_URL=https://sistema.example.com
SYS_USERNAME=seu_usuario
SYS_PASSWORD=sua_senha
SYS_SECRET_OTP=seu_secret_otp

# Browser e timeouts
BROWSER=chrome                  # chrome ou edge
HEADLESS=false                  # true para modo headless
TIMEOUT_DOWNLOAD=60             # segundos para timeout de download

# SQL Server (substituiu NocoDB)
DB_SERVER=seu_servidor.database.windows.net
DB_DATABASE=nome_database
DB_USERNAME=usuario_sql
DB_PASSWORD=senha_sql
DB_DRIVER=ODBC Driver 17 for SQL Server

# Configurações de envio
BATCH_SIZE=25                   # Registros por batch
POST_RETRIES=3                  # Tentativas de retry
BACKOFF_BASE=1.5                # Base para exponential backoff
```

**🔑 NOVO (Fase 8-14): Carregamento Dinâmico de .env**
- **Entry point:** `scripts/config_embutida.py` (executa antes de `app.py`)
- **Busca automática:** Procura `.env` em múltiplos locais (cwd, raiz do projeto)
- **Carregamento:** Popula `os.environ` com todas as 18 variáveis
- **Fallback:** Se `.env` ausente, tenta `os.environ` (para produção com variáveis de sistema)
- **Segurança:** Credenciais NÃO compiladas no `.exe` (carregadas em runtime)
- **Verificação:** Validação de variáveis críticas com mensagens claras

**Fluxo de Execução:**
```
1. User executa: robo_neo.exe (OU python app.py localmente)
2. scripts/config_embutida.py executa PRIMEIRO
3. Procura .env em: cwd → raiz do projeto
4. Popula os.environ[VAR] = valor
5. Executa app.py (agora com credenciais carregadas)
6. app.py tolerante se .env ausente (usa os.environ como fallback)
```

### Tratamento de Erros
- **ElementClickInterceptedException**: Tentar ESC para fechar overlays
- **StaleElementReferenceException**: Re-encontrar elemento
- **PermissionError**: Log warning e continuar (arquivos em uso)
- **API failures**: Retry com backoff exponencial
- **IntegrityError + PRIMARY KEY (Novo Fase 6):** IGNORA (é duplicata, não retry)
  - Per-record processing: continua batch mesmo se há duplicata
  - Logging: debug level mostra qual duplicata
  - Contadores: batch_success_count, batch_duplicate_count, batch_error_count

### Estrutura de Testes
```python
# tests/test_parse_*.py - Parse Excel -> JSON
# tests/test_post_*.py - JSON -> API com --dry-run
# Usar argparse para flexibilidade
# Gerar timestamps em arquivos de saída
```

## 📊 Tipos de Dados

### Relatórios Suportados
1. **ExportacaoProducao.xlsx**: Dados de pedidos, clientes, produtos
2. **Exportacao Atividade.xlsx**: Atividades operacionais
3. **Exportacao Status.xlsx**: Histórico de status e movimentações

### Mapeamento Flexível
- Headers normalizados (sem acentos, lowercase)
- Matching tolerante por substring
- Campos extras concatenados em "TAGS"
- Valores None/NaN convertidos para string vazia
- Mapeamento SQL em `sql_map.json` com tabelas e colunas
- **JSONs carregados EXCLUSIVAMENTE de `\bases\`** (Novo Fase 4)
  - Sem fallback para raiz do projeto
  - Falha early com mensagem clara se não encontrados

## 🔄 Fluxo de Execução Padrão

1. **Inicialização**: Validar .env, limpar downloads antigos
2. **Login**: Credenciais + OTP com retry automático
3. **Navegação**: Abrir sidebar, acessar painéis específicos
4. **Downloads**: Atividades Status (90d) → Atividades (90d) → Produção (92d, dia 1)
5. **Processamento**: Parse imediato após download
6. **Envio**: Inserts em SQL Server com batches e retry
7. **Agendamento**: Próxima execução em 30min

## 🧪 Estratégia de Testes

### Parse Testing
```python
python tests/test_parse_atividades.py [arquivo_opcional]
# Gera: tests/json/parsed_atividades_YYYYMMDD_HHMMSS.json
```

### API Testing
```python
python tests/test_post_atividades.py --dry-run --batch-size 10
# Valida sem enviar, logs detalhados
```

## 🚨 Pontos de Atenção

### Interface Web (Vaadin)
- Framework Vaadin com elementos customizados
- XPaths podem quebrar com updates da UI
- Overlays/modals podem interceptar clicks
- Sempre usar `ActionChains` para clicks complexos

### Arquivos Excel
- Estrutura pode variar entre versões do sistema
- Headers podem ter pequenas diferenças
- Datas em formatos diversos (DD/MM/YYYY, timestamps)
- Campos vazios devem ser tratados como strings vazias

### SQL Server (Migração de NocoDB)
- Conexão via ODBC com autenticação SQL
- Credenciais no .env: DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD
- Inserts em batches configuráveis (BATCH_SIZE)
- Tratamento de caracteres especiais em strings
- Índices nas tabelas melhoram performance
- Tentativas de conexão com retry + backoff exponencial
- Logging estruturado em JSONL para auditoria
- **NOVO (Fase 6): Tratamento de duplicatas (PRIMARY KEY violations)**
  - Per-record processing evita perda de lote inteiro
  - IntegrityError + PRIMARY KEY = IGNORA (não retry)
  - Taxa de sucesso reflete resultado REAL (não artificialmente baixa)
- **NOVO: Rastreamento de linha do Excel**
  - Cada registro carrega `_line_number` (linha do Excel original)
  - Cada registro carrega `_file_name` (nome do arquivo)
  - Logs de erro mostram: qual linha, qual arquivo, qual dado
  - JSONL inclui `source: {file, line}` para auditoria
  - Permite rastrear facilmente erro até origem no Excel

## 💡 Melhores Práticas para Desenvolvimento

### Ao Modificar XPaths
1. Testar em ambiente real
2. Usar `gerar_xpath_relativo.py` para novos elementos
3. Manter referências organizadas no JSON
4. Salvar screenshots para documentação

### Ao Adicionar Novos Relatórios
1. Criar entrada em `sql_map.json` (não mais nocodb_map.json)
2. Implementar função `parse_*` específica
3. Adicionar URL da tabela no .env
4. Criar testes correspondentes

### Ao Debuggar
1. Verificar `element_screenshots/` para capturas
2. Analisar logs JSONL com `jq` ou similar
3. Usar `--dry-run` para validar sem side effects
4. Screenshots manuais com `salvar_screenshot_elemento()`
5. Verificar conexão SQL Server em `logs/sent_records_*.jsonl`

### Deploy e Manutenção
- Usar `empacotar_robo_neo.bat` para builds
- Incluir todos os JSONs e .env no pacote
- Testar em ambiente similar ao produção
- Monitorar logs de `envios_resumo.jsonl`

### Tratamento de Duplicatas (NOVO - Fase 6)
- **Quando:** INSERT falhar com `pyodbc.IntegrityError` + "PRIMARY KEY"
- **O que fazer:** IGNORA (não tenta retry)
- **O que NÃO fazer:** Não aumentar POST_RETRIES (não resolve)
- **Logging:** Debug level apenas
- **Impacto:** Batch continua (24/25 ao invés de 0/25)
- **Taxa sucesso:** Agora reflete realidade (não artifical 0% ou 100%)

## 📚 Rotina de Atualização de Documentação

### ⚠️ REGRA CRÍTICA: Documentação EXCLUSIVAMENTE em `\docs`

**NUNCA crie arquivos `.md`, `.txt` ou qualquer documentação na RAIZ do projeto!**

Todos os documentos devem estar em: `docs/` (subdiretório)

### Mapeamento Código → Documentação

| Aspecto do Código | Arquivo a Atualizar | Seção/Tópico |
|------------------|-------------------|-------------|
| **Quick start, início rápido** | `docs/00_COMECE_AQUI.md` | Main guide |
| **Novo usuário, first steps** | `docs/1_INICIO.md` | Setup section |
| **Referência rápida** | `docs/2_REFERENCIA.md` | Quick lookup |
| **Detalhes arquitetura** | `docs/3_DETALHES.md` | Architecture section |
| **Build e compilação** | `docs/BUILD_FINAL_CORRIGIDO.md` | Build process |
| **Configuração dinâmica .env** | `docs/CONFIG_DINAMICA_DO_ENV.md` | Dynamic loading |
| **Integração teste config** | `docs/INTEGRACAO_CONFIG_DINAMICA.md` | Testing section |
| **Resumo de alterações** | `docs/RESUMO_ALTERACOES.md` | Current status |
| **Padrões de código** | `.github/copilot-instructions.md` | "Padrões de Código" |

### Rotina Passo-a-Passo

**1️⃣ Você fez mudança no código:**
```
Exemplo: Adicionou novo tipo de retry exponencial em app.py
```

**2️⃣ Identifique qual arquivo `.md` documenta isso:**
```
IMPORTANTE: Procure em `docs/` APENAS
→ Padrão de código = copilot-instructions.md (exceção, fora de docs/)
→ OU Arquitetura = docs/ARQUITETURA_E_API.md
→ OU Erros = docs/TROUBLESHOOTING.md
```

**3️⃣ Procure a seção relevante NO ARQUIVO EXISTENTE:**
```
❌ NUNCA crie novo .md chamado "NOVO_RETRY_EXPONENCIAL.md" na raiz
✅ Procure em docs/ARQUITETURA_E_API.md a seção "Tratamento de Erros"
   ou "Envio de APIs" que fale sobre retry
```

**4️⃣ Atualize a seção encontrada:**
```
Use replace_string_in_file para atualizar a seção EM docs/
Mantenha a estrutura original
Adicione seus detalhes à seção existente
```

**5️⃣ Se nenhuma seção existir:**
```
EXCEÇÃO: Se não houver seção relevante em nenhum arquivo
→ Crie uma NOVA SEÇÃO dentro do arquivo .md apropriado EM docs/
→ NÃO crie um novo arquivo .md
→ Exemplo: Se é novo erro, adicione em docs/TROUBLESHOOTING.md
```

### Exemplos de Aplicação

**Exemplo 1: Novo padrão de logging**
```
Mudança: app.py agora usa logger.info() com emoji 📊
Arquivo: .github/copilot-instructions.md
Seção: "Logging Estruturado"
Ação: Atualizar exemplo de código nessa seção
```

**Exemplo 2: Novo erro de conexão SQL**
```
Mudança: Novo erro `[HY001]` adicionado
Arquivo: docs/3_DETALHES.md
Seção: "Possíveis Problemas"
Ação: Adicionar novo erro com solução nessa seção
```

**Exemplo 3: Nova fase de desenvolvimento**
```
Mudança: Fase 15 implementada com cache
Arquivo: docs/RESUMO_ALTERACOES.md
Seção: "Histórico de Fases"
Ação: Adicionar nova Fase 15 após Fase 14
```

### ⚠️ Regras de Ouro

1. **NUNCA criar arquivo `.md` novo na RAIZ do projeto**
   - Todo arquivo `.md`, `.txt`, ou documentação vai em `docs/`
   - Exceção única: `.github/copilot-instructions.md` (já está fora da raiz)
   - Violação: Criar `NOVO_RECURSO.md` na raiz = ❌ ERRADO

2. **SEMPRE colocar documentação em `docs/` subdiretório**
   - Novo build process? → `docs/BUILD_FINAL_CORRIGIDO.md`
   - Novo padrão de código? → `.github/copilot-instructions.md` ou `docs/3_DETALHES.md`
   - Novo processo? → `docs/1_INICIO.md` ou `docs/2_REFERENCIA.md`

3. **SEMPRE verificar `docs/` existentes** antes de escrever
   - Use `grep` ou leitura para encontrar seção relevante
   - Se não achar, vá para seção "genérica" em arquivo apropriado

4. **Manter estrutura original** dos documentos
   - Não reorganize seções existentes
   - Não remova conteúdo obsoleto (marque como ⚠️ DEPRECATED se necessário)
   - Adicione à seção existente, não crie nova seção desnecessária

5. **Data de atualização** no final do arquivo
   - Exemplo: `**Última atualização:** 29 de outubro de 2025`

### Vantagens dessa Rotina

✅ **Documentação não fica dispersa** em 20+ arquivos  
✅ **Usuários sabem exatamente onde procurar** (mapeamento claro)  
✅ **Fácil manutenção** (tudo organizado em 5 arquivos)  
✅ **Sem duplicação** de informação entre docs  
✅ **Escalável** (crescer sem poluir repositório)  

## 🎯 Objetivos de Qualidade

- **Robustez**: Zero falhas por mudanças menores na UI
- **Observabilidade**: Logs completos para debugging
- **Flexibilidade**: Configuração externa para adaptações
- **Testabilidade**: Suite completa com dry-run
- **Manutenibilidade**: Código modular e bem documentado

---

*Este projeto segue padrões de automação web empresarial com foco em confiabilidade e manutenibilidade. Sempre priorize logging detalhado e tratamento robusto de exceções.*