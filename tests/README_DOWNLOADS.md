# 🧪 Testes de Download Individual

Este diretório contém testes para download individual de cada relatório **sem precisar passar por todos os 3 relatórios**.

⚠️ **IMPORTANTE:** Os testes **APENAS BAIXAM OS ARQUIVOS** - eles **NÃO FAZEM INSERÇÃO NO BANCO DE DADOS**.

Para enviar os dados para o banco, veja a seção "Enviar para Banco de Dados" abaixo.

---

## 📋 Testes Disponíveis

### 1. Download de Status de Atividades
```bash
python tests/test_download_status.py
```
**Opções:**
- `--headless` - Executar sem UI visual
- `--timeout 120` - Timeout customizado em segundos

**Exemplo:**
```bash
# Modo normal (com navegador visível)
python tests/test_download_status.py

# Modo headless (sem UI)
python tests/test_download_status.py --headless

# Com timeout de 120 segundos
python tests/test_download_status.py --timeout 120
```

**Resultado:**
```
✅ downloads/Exportacao Status.xlsx (baixado)
```

---

### 2. Download de Atividades
```bash
python tests/test_download_atividades.py
```
**Opções:**
- `--headless` - Executar sem UI visual
- `--timeout 120` - Timeout customizado em segundos

**Exemplo:**
```bash
# Modo normal (com navegador visível)
python tests/test_download_atividades.py

# Modo headless (sem UI)
python tests/test_download_atividades.py --headless

# Com timeout de 120 segundos
python tests/test_download_atividades.py --timeout 120
```

**Resultado:**
```
✅ downloads/Exportacao Atividades.xlsx (baixado)
```

---

### 3. Download de Produção
```bash
python tests/test_download_producao.py
```
**Opções:**
- `--headless` - Executar sem UI visual
- `--timeout 120` - Timeout customizado em segundos

**Exemplo:**
```bash
# Modo normal (com navegador visível)
python tests/test_download_producao.py

# Modo headless (sem UI)
python tests/test_download_producao.py --headless

# Com timeout de 120 segundos
python tests/test_download_producao.py --timeout 120
```

**Resultado:**
```
✅ downloads/ExportacaoProducao.xlsx (baixado)
```

---

## 🔄 Baixar os 3 Arquivos Sequencialmente

Você pode executar os 3 testes um após o outro (sem executar a rotina principal):

**Exemplo com headless (recomendado para rapidez):**
```bash
python tests/test_download_status.py --headless
python tests/test_download_atividades.py --headless
python tests/test_download_producao.py --headless
```

**Resultado:** 
- ✅ `downloads/Exportacao Status.xlsx`
- ✅ `downloads/Exportacao Atividades.xlsx`
- ✅ `downloads/ExportacaoProducao.xlsx`

---

## 📊 O Que Cada Teste Faz

```
1. ✓ Carrega variáveis de ambiente (.env)
2. ✓ Inicia navegador (Chrome ou Edge conforme .env)
3. ✓ Acessa URL do sistema
4. ✓ Realiza login com OTP
5. ✓ Abre sidebar
6. ✓ Baixa o relatório específico
7. ✓ Lista arquivos baixados em /downloads
8. ✓ Fecha navegador

❌ NÃO faz:
  - Parse dos dados
  - Inserção no banco de dados
  - Envio para APIs
```

---

## 💾 Enviar para Banco de Dados

Se você já tem os arquivos baixados e quer enviar para o SQL Server:

### Passo 1: Parse do Arquivo
```bash
# Parse Status
python tests/test_parse_atividades.py downloads/Exportacao\ Status.xlsx

# Parse Atividades
python tests/test_parse_atividades.py downloads/Exportacao\ Atividades.xlsx

# Parse Produção
python tests/test_parse_atividades.py downloads/ExportacaoProducao.xlsx
```

Isso gera um JSON em: `tests/json/parsed_*.json`

### Passo 2: Enviar para Banco (DRY RUN - Simular)
```bash
# Testar sem enviar de verdade
python tests/test_post_atividades.py --dry-run --batch-size 10
```

### Passo 3: Enviar de Verdade
```bash
# Realmente enviar para o banco
python tests/test_post_atividades.py --batch-size 25
```

---

## 🎯 Casos de Uso

### Desenvolvimento & Debug
```bash
# Testar download com UI visível para ver o que acontece
python tests/test_download_status.py
```

### CI/CD & Automação
```bash
# Testar sem UI (mais rápido)
python tests/test_download_status.py --headless
```

### Debugging de Timeout
```bash
# Se estiver falhando, aumentar timeout
python tests/test_download_producao.py --timeout 180
```

### Apenas Baixar (Sem Enviar ao Banco)
```bash
# Baixar os 3 arquivos sem fazer inserção
python tests/test_download_status.py --headless
python tests/test_download_atividades.py --headless
python tests/test_download_producao.py --headless

# Arquivos estarão em: downloads/
```

### Baixar + Parse (Sem Enviar ao Banco)
```bash
# 1. Baixar
python tests/test_download_status.py --headless

# 2. Parse para JSON
python tests/test_parse_atividades.py downloads/Exportacao\ Status.xlsx

# 3. Ver resultado em: tests/json/parsed_*.json
```

---

## ✅ Sucesso vs ❌ Erro

**Sucesso (✅):**
```
2025-10-28 14:30:00 [INFO] ========================================================================
2025-10-28 14:30:00 [INFO] 🧪 TESTE: Download Individual - Status de Atividades
2025-10-28 14:30:00 [INFO] ========================================================================
...
2025-10-28 14:35:00 [INFO] ========================================================================
2025-10-28 14:35:00 [INFO] ✅ SUCESSO: Download de Status concluído!
2025-10-28 14:35:00 [INFO] ========================================================================
2025-10-28 14:35:00 [INFO] 📁 Arquivos em downloads/:
2025-10-28 14:35:00 [INFO]    📄 Exportacao Status.xlsx (1250.5 KB)
```

**Erro (❌):**
```
2025-10-28 14:30:00 [ERROR] ========================================================================
2025-10-28 14:30:00 [ERROR] ❌ ERRO: Teste falhou!
2025-10-28 14:30:00 [ERROR] Detalhes: Connection timeout...
2025-10-28 14:30:00 [ERROR] ========================================================================
```

---

## 🔧 Troubleshooting

### Teste falhando com "Elemento não encontrado"
```bash
# Tentar com headless=false para ver o navegador
python tests/test_download_status.py
```

### Timeout excedido
```bash
# Aumentar timeout para 180 segundos
python tests/test_download_status.py --timeout 180
```

### Arquivo não baixado
```bash
# Verificar pasta de downloads
ls -la downloads/
# ou
dir downloads\
```

### OTP inválido
```
Verifique:
1. .env - SYS_SECRET_OTP está correto?
2. .env - OTP_URL está acessível?
3. Relógio do servidor está sincronizado?
```

---

## 📝 Logs

Todos os testes geram logs em:
- **Console:** Saída em tempo real (INFO, WARNING, ERROR)
- **Arquivo:** `logs/robo_download.log` (histórico completo)

---

## 📚 Referência Rápida

| Tarefa | Comando |
|--------|---------|
| Baixar Status | `python tests/test_download_status.py --headless` |
| Baixar Atividades | `python tests/test_download_atividades.py --headless` |
| Baixar Produção | `python tests/test_download_producao.py --headless` |
| Baixar Todos os 3 | Rodar os 3 acima sequencialmente |
| Parse (JSON) | `python tests/test_parse_atividades.py downloads/<arquivo>` |
| Enviar (Simular) | `python tests/test_post_atividades.py --dry-run` |
| Enviar (Real) | `python tests/test_post_atividades.py` |

---

**Última atualização:** 28 de outubro de 2025  
**Status:** ✅ Testes apenas baixam, sem inserção no banco
