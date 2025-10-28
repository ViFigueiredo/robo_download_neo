# GitHub Copilot Instructions - Robô de Download Neo

## 📋 Contexto do Projeto

Este é um sistema de automação web empresarial que realiza downloads automatizados de relatórios de um sistema corporativo e os processa para envio a APIs do NocoDB. O projeto utiliza Selenium para automação web, pandas para processamento de dados, e tem um sistema robusto de agendamento e retry.

## 🎯 Objetivos Principais

- **Automação Web**: Login automatizado com 2FA/OTP e navegação por interface Vaadin
- **Download de Relatórios**: Extração de dados de Produção, Atividades e Status de Atividades
- **Processamento de Dados**: Parse flexível de arquivos Excel com mapeamento dinâmico
- **Integração API**: Envio em batches para NocoDB com retry e logging detalhado
- **Execução Agendada**: Runs a cada 30 minutos entre 8h-22h

## 🏗️ Arquitetura e Componentes

### Estrutura Principal
```
app.py              # Aplicação principal com toda a lógica
bases/              # 📁 NOVO (Fase 4): Pasta obrigatória para JSONs
  ├── map_relative.json
  ├── nocodb_map.json
  ├── sql_map.json
downloads/          # 📁 Arquivos Excel baixados
logs/               # 📁 Logs estruturados em JSONL
tests/              # Suite completa de testes
.env                # Configurações sensíveis
```

**Importante (Fase 4):** Todos os JSONs **DEVEM** estar em `\bases\`. Sem fallback para raiz do projeto.

### Tecnologias Core
- **Selenium WebDriver** (Chrome/Edge)
- **Pandas** para processamento Excel
- **Requests** para APIs HTTP
- **Schedule** para agendamento
- **PyInstaller** para empacotamento

## 🔧 Padrões de Código

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
    # Mapeamento tolerante com nocodb_map.json
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
SYS_URL, SYS_USERNAME, SYS_PASSWORD, SYS_SECRET_OTP

# Browser e timeouts
BROWSER=chrome, HEADLESS=false, TIMEOUT_DOWNLOAD=60

# SQL Server
DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD, DB_DRIVER

# Configurações de envio
BATCH_SIZE=25, POST_RETRIES=3, BACKOFF_BASE=1.5
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
1. Criar entrada em `nocodb_map.json`
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

### Quando Modificar Código
**IMPORTANTE:** Toda mudança no código `app.py` ou arquivos-chave **DEVE** ser documentada. Porém, **NÃO crie novo `.md`** - atualize os arquivos existentes!

### Mapeamento Código → Documentação

| Aspecto do Código | Arquivo a Atualizar | Seção/Tópico |
|------------------|-------------------|-------------|
| **Arquitetura, fluxo, padrões** | `docs/ARQUITETURA_E_API.md` | Seção correspondente |
| **Instalação, setup, deploy** | `docs/INSTALACAO_E_DEPLOY.md` | "Fase X" ou "Setup" |
| **Erros, exceptions, bugs** | `docs/TROUBLESHOOTING.md` | "Problemas Comuns" |
| **Navegação, índice de tópicos** | `docs/INDICE_DOCUMENTACAO.md` | Índice principal |
| **Padrões de código, convenções** | `.github/copilot-instructions.md` | "Padrões de Código" |

### Rotina Passo-a-Passo

**1️⃣ Você fez mudança no código:**
```
Exemplo: Adicionou novo tipo de retry exponencial em app.py
```

**2️⃣ Identifique qual `.md` documenta isso:**
```
→ Padrão de código = copilot-instructions.md
→ OU Arquitetura = ARQUITETURA_E_API.md
```

**3️⃣ Procure a seção relevante NO ARQUIVO EXISTENTE:**
```
NÃO crie novo .md chamado "NOVO_RETRY_EXPONENCIAL.md"
↓
Procure em ARQUITETURA_E_API.md a seção "Tratamento de Erros"
ou "Envio de APIs" que fale sobre retry
```

**4️⃣ Atualize a seção encontrada:**
```
Use replace_string_in_file para atualizar a seção
Mantenha a estrutura original
Adicione seus detalhes à seção existente
```

**5️⃣ Se nenhuma seção existir:**
```
EXCEÇÃO: Se não houver seção relevante em nenhum .md
→ Crie uma NOVA SEÇÃO dentro do .md mais apropriado
→ NÃO crie um novo arquivo .md
→ Exemplo: Se é novo erro, adicione em TROUBLESHOOTING.md
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
Arquivo: docs/TROUBLESHOOTING.md
Seção: "Problemas Comuns"
Ação: Adicionar novo erro com solução nessa seção
```

**Exemplo 3: Nova fase de desenvolvimento**
```
Mudança: Fase 7 implementada com cache
Arquivo: docs/INSTALACAO_E_DEPLOY.md
Seção: "Fase 7: [Nome]"
Ação: Adicionar nova seção Fase 7 após Fase 6
```

### ⚠️ Regras de Ouro

1. **NÃO criar arquivo `.md` novo** por mudança de código
   - Exceção: Documentação completamente fora do escopo atual (muito rara)

2. **SEMPRE verificar docs existentes** antes de escrever
   - Use `grep` ou leitura para encontrar seção relevante
   - Se não achar, vá para seção "genérica" (ex: Troubleshooting)

3. **Manter estrutura original** do documento
   - Não reorganize seções existentes
   - Não remova conteúdo obsoleto (marque como ⚠️ DEPRECATED se necessário)

4. **Links internos** devem apontar para arquivo e seção corretos
   - Exemplo: `[Ver em TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)`

5. **Data de atualização** no final do arquivo
   - Exemplo: `**Última atualização:** 28 de outubro de 2025`

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