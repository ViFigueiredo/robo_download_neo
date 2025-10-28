# 🔄 Estratégia de Retry para Downloads - Fase 8

**Para:** Desenvolvedores e Operadores  
**Objetivo:** Explicar mecanismo de retry automático para downloads de relatórios  
**Status:** ✅ Implementado em v2.0

---

## 🎯 O Problema

Downloads de relatórios podem falhar por razões transitórias:
- **Problemas de rede:** Timeouts, packet loss, reconexão
- **Servidor temporariamente sobrecarregado:** Responde com 503 Service Unavailable
- **SSL/TLS issues:** EOF errors em conexão HTTPS
- **Firewall/proxy:** Reconexões necessárias

**Antes (v1.9):**
```
❌ Download falha → Aplicação inteira falha → 0 arquivos
```

**Depois (v2.0):**
```
⚠️ Tentativa 1 falha → Aguarda 1 min → Tenta novamente
⚠️ Tentativa 2 falha → Aguarda 1 min → Tenta novamente
✅ Tentativa 3 sucesso → Continua execução
```

---

## ⚙️ Como Funciona

### Arquitetura de Retry

```
FASE 1: Downloads (COM RETRY)
├─ [Tentativa 1/3] Baixar Status
│  ├─ Falha → Aguarda 60s
│  └─ Sucesso → Próximo arquivo
├─ [Tentativa 2/3] Baixar Status
│  ├─ Falha → Aguarda 60s
│  └─ Sucesso → Próximo arquivo
├─ [Tentativa 3/3] Baixar Status
│  ├─ Falha → ❌ ERRO FINAL (não continua)
│  └─ Sucesso → Próximo arquivo
├─ Baixar Atividades (mesmo padrão)
└─ Baixar Produção (mesmo padrão)

FASE 2: Processamento (SEM RETRY)
├─ Processar Status
├─ Processar Atividades
└─ Processar Produção
```

### Função de Retry (Padrão em Todas as Funções)

```python
def exportAtividadesStatus(driver):
    """Exporta Status de Atividades com retry automático (3 tentativas, 1 min delay)."""
    max_tentativas = 3
    delay_segundos = 60
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            # LÓGICA ORIGINAL DE DOWNLOAD
            esperar_elemento(driver, XPATHS['atividades']['panel'], ...)
            clicar_elemento(driver, XPATHS['atividades']['panel'], ...)
            selecionar_data(driver, XPATHS['atividades']['date_picker'], ...)
            clicar_elemento(driver, XPATHS['atividades']['search_button'], ...)
            realizar_download_atividades(driver, XPATHS['atividades']['export_status_button'])
            
            logger.info("✅ Status de Atividades baixado com sucesso!")
            return  # ← EXIT IMEDIATO se sucesso
            
        except Exception as e:
            if tentativa < max_tentativas:
                # Ainda há tentativas restantes
                logger.warning(
                    f"⚠️ Erro ao baixar Status (tentativa {tentativa}/{max_tentativas}): {str(e)[:80]}"
                )
                logger.info(f"   Aguardando {delay_segundos}s antes de tentar novamente...")
                time.sleep(delay_segundos)
            else:
                # Todas as 3 tentativas falharam
                logger.error(
                    f"❌ FALHA FINAL ao baixar Status após {max_tentativas} tentativas!"
                )
                logger.error(f"   Último erro: {str(e)}")
                raise  # ← LEVANTA EXCEPTION (não silencia erro)
```

**Pontos-chave:**
1. **Loop 3 vezes:** `for tentativa in range(1, 4):`
2. **Delay entre tentativas:** `time.sleep(60)` = 1 minuto
3. **Exit rápido se sucesso:** `return` imediato
4. **Raise apenas após todas as tentativas:** Exception propagada após 3º fracasso

---

## 📊 Comportamento Esperado

### Cenário 1: Sucesso na Primeira Tentativa

```log
[INFO] [FASE 1/2] Iniciando downloads com retry automático...
[INFO] ════════════════════════════════════════════════════
[INFO] [1/3] Exportando Status de Atividades...
[INFO] ✅ Status de Atividades baixado com sucesso!
[INFO] [2/3] Exportando Atividades...
[INFO] ✅ Atividades baixado com sucesso!
[INFO] [3/3] Exportando Produção...
[INFO] ✅ Produção baixado com sucesso!
[INFO] ════════════════════════════════════════════════════
[INFO] ✅ FASE 1 completa: Todos os 3 arquivos baixados!
```

**Tempo total:** ~10-15 segundos (sem delay desnecessário)

---

### Cenário 2: Falha na Primeira, Sucesso na Segunda

```log
[INFO] [1/3] Exportando Status de Atividades...
[WARNING] ⚠️ Erro ao baixar Status (tentativa 1/3): SSLEOFError
[INFO]    Aguardando 60s antes de tentar novamente...
[INFO] [Aguardando...] Tempo decorrido: 30s
[INFO] [Aguardando...] Tempo decorrido: 60s
[INFO] ✅ Status de Atividades baixado com sucesso!
[INFO] [2/3] Exportando Atividades...
[INFO] ✅ Atividades baixado com sucesso!
```

**Tempo total:** ~60-75 segundos (1 min de delay)

---

### Cenário 3: Falha em Todas as 3 Tentativas

```log
[INFO] [1/3] Exportando Status de Atividades...
[WARNING] ⚠️ Erro ao baixar Status (tentativa 1/3): Connection timeout
[INFO]    Aguardando 60s...
[WARNING] ⚠️ Erro ao baixar Status (tentativa 2/3): Connection timeout
[INFO]    Aguardando 60s...
[WARNING] ⚠️ Erro ao baixar Status (tentativa 3/3): Connection timeout
[ERROR] ❌ FALHA FINAL ao baixar Status após 3 tentativas!
[ERROR]    Último erro: Connection timeout

Traceback (most recent call last):
  File "app.py", line 1080, in exportAtividadesStatus
    ...
ConnectionError: Connection timeout
```

**Tempo total:** ~120-140 segundos (2 min de delay total)
**Comportamento:** Aplicação para, exception é logada

---

## 🔧 Configuração

### Padrão Atual (Hardcoded)

```python
max_tentativas = 3         # Sempre 3 tentativas
delay_segundos = 60        # Sempre 60 segundos (1 minuto)
```

### Tornar Configurável (Opcional - Fase 9)

Se necessário, adicionar ao `.env`:

```properties
# Retry para downloads
DOWNLOAD_MAX_ATTEMPTS=3
DOWNLOAD_RETRY_DELAY=60
```

E carregar em `app.py`:

```python
max_tentativas = int(os.getenv('DOWNLOAD_MAX_ATTEMPTS', 3))
delay_segundos = int(os.getenv('DOWNLOAD_RETRY_DELAY', 60))
```

**Recomendação:** Manter hardcoded por enquanto (valores provados em produção).

---

## 📋 Funções com Retry

| Função | Arquivo | Linhas | Status |
|--------|---------|--------|--------|
| `exportAtividadesStatus()` | app.py | 1073-1108 | ✅ v2.0 |
| `exportAtividades()` | app.py | 1110-1145 | ✅ v2.0 |
| `exportProducao()` | app.py | 1150-1187 | ✅ v2.0 |

**OBS:** Processamento de arquivos (FASE 2) **NÃO** faz retry:
- Se parse falhar: log de erro e continua para próximo arquivo
- Se inserção falhar: erro é registrado por registro (ver `TROUBLESHOOTING.md`)

---

## 🧪 Testando Retry

### Teste 1: Simular Falha com DRY_RUN

```bash
set DRY_RUN=true
python app.py
```

Log mostrará tentativas mesmo em DRY_RUN (simula lógica).

### Teste 2: Download Real com Headless

```bash
python tests/test_download_status.py --headless
```

Monitorar logs:
```bash
tail -f logs/robo_download.log
```

Procurar por:
- ✅ Sucesso na 1ª tentativa (sem delay)
- ⚠️ Tentar outra vez se falhar

### Teste 3: Forçar Falha (Testing)

*(Não recomendado em produção)*

Se quiser testar retry mechanism mesmo quando download sucede:

```python
# Adicionar no início da função (apenas para teste):
if TEST_FORCE_RETRY:
    raise Exception("TESTE: Forçando retry")
```

Depois remover após verificação.

---

## 📈 Métricas e Logs

### Onde Verificar Tentativas

**Arquivo:** `logs/robo_download.log`

```bash
# Procurar por tentativas
grep "tentativa" logs/robo_download.log

# Procurar por sucessos
grep "✅.*baixado com sucesso" logs/robo_download.log

# Procurar por falhas finais
grep "❌ FALHA FINAL" logs/robo_download.log
```

### Estatísticas Esperadas

Executar 10 rotinas, esperado:

- **~99% sucesso sem delay:** Tentativas 1 com sucesso (rede boa)
- **~0.9% sucesso com delay:** Tentativa 2 ou 3 (rede instável)
- **~0.1% falha após 3:** Servidor offline ou firewall (raro)

---

## 🚨 Tratamento de Erros

### Se Download Falhar Após 3 Tentativas

**Logs mostram:**
```
❌ FALHA FINAL ao baixar Status após 3 tentativas!
   Último erro: [HY000] Connection refused
```

**Possíveis causas:**
1. **Servidor offline:** Verificar se sistema corporativo está disponível
2. **Firewall/proxy:** Verificar conectividade
3. **Credenciais expiradas:** Verificar token OTP

**Ações:**
1. Verificar conectividade: `ping seu_servidor`
2. Verificar firewall: `telnet seu_servidor 443`
3. Reexecutar aplicação (próxima execução pode suceder)

### Se Houver Timeout em Todas as 3 Tentativas

**Timing esperado:**
- Tentativa 1: ~10s (falha)
- Delay 1: 60s
- Tentativa 2: ~10s (falha)
- Delay 2: 60s
- Tentativa 3: ~10s (falha)
- **Total:** ~150 segundos (~2.5 minutos)

Se timeout total exceder 5 minutos, possível problema com servidor web (não conexão).

---

## ✅ Checklist de Validação

Após deploy, verificar:

- [ ] Download sucede na 1ª tentativa (sem delay desnecessário)
- [ ] Logs mostram `✅ arquivo baixado com sucesso!`
- [ ] 3 tentativas aparecem em log se houver falha
- [ ] Delay de 60s entre tentativas
- [ ] Erro final é propagado (não silenciado)
- [ ] FASE 2 (processamento) só executa após TODOS os downloads
- [ ] Arquivo `sent_records_*.jsonl` contém dados corretos

---

## 🔍 Troubleshooting

### Pergunta: Por que 60 segundos de delay?

**Resposta:** 
- Curto demais (~10s): Servidor pode ainda estar recuperando
- Longo demais (~5min): Usuário fica esperando demais
- 60s é sweet spot: Tempo suficiente para recuperação, sem espera excessiva

### Pergunta: Por que 3 tentativas?

**Resposta:**
- 1 tentativa: Sem retry (estado anterior)
- 2 tentativas: Pode ser coincidência, não confiável
- 3 tentativas: Aumenta confiabilidade sem tempo excessivo (~2.5min máximo)
- 4+ tentativas: Tempo demais esperando servidor offline

### Pergunta: E se o servidor estiver OFFLINE durante 3 tentativas?

**Resposta:** 
Após 3 falhas, `app.py` falha com exception. Próxima execução (em 30 min) tentará novamente automaticamente.

Agendamento (cron/Task Scheduler) pode ser configurado para alertar se 3 execuções consecutivas falharem.

### Pergunta: Isso afeta envio para SQL Server?

**Resposta:**
**NÃO.** Retry é apenas para downloads (FASE 1). Envio para SQL (FASE 2) usa estratégia diferente:
- Por-record processing (não todo batch)
- IntegrityError + PRIMARY KEY = ignora (não retry)
- Outro erro = retry com backoff exponencial
- Ver `TROUBLESHOOTING.md` seção "Violation of PRIMARY KEY constraint"

---

## 📚 Referências

- **Ver completo:** `app.py` linhas 1073-1187
- **Troubleshooting geral:** `docs/TROUBLESHOOTING.md`
- **Inserts para SQL:** `docs/ARQUITETURA_E_API.md` seção "Envio de APIs"
- **Instruções de operação:** `.github/copilot-instructions.md`

---

## 📝 Histórico de Versões

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | Out 2025 | Sem retry (falha única) |
| 1.9 | Out 2025 | Duas fases (download + processing) |
| 2.0 | Out 2025 | **Retry automático (3x, 1 min delay)** ← ATUAL |

---

**Última atualização:** 28 de outubro de 2025  
**Mantido por:** GitHub Copilot (Projeto RoboDownloadNeo)

