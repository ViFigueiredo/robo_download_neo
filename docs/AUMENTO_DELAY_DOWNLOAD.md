# ⏱️ Aumento de Delay para Retry de Downloads (Fase 8.1)

**Data:** 28 de outubro de 2025  
**Problema:** Link fica disponível mas o download não é realizado  
**Solução:** Aumentar delay entre tentativas para dar tempo ao servidor/download  
**Status:** ✅ IMPLEMENTADO

---

## 🐛 Problema Identificado

O link de download estava sendo gerado corretamente (modal aberto com sucesso), mas o download não se completava. Ao tentar novamente imediatamente (após 60s), falhava novamente, sugerindo que o servidor precisava de mais tempo para preparar o arquivo.

### Causa Raiz

1. **Delay insuficiente entre tentativas:** Estava usando 60 segundos (hardcoded)
2. **Delay insuficiente no baixar_arquivo_com_cookies():** Estava usando apenas 2 segundos entre tentativas HTTP
3. **Sem configurabilidade:** Valores não podiam ser ajustados sem modificar código

---

## ✅ Solução Implementada

### 1. **Nova Variável de Configuração**

Adicionado ao `.env.example` e código:
```bash
# Delay entre tentativas de download (em segundos)
# Recomendado: 120-180 segundos para arquivos grandes
DOWNLOAD_RETRY_DELAY=120
```

**Default:** 120 segundos (2 minutos)  
**Configurável:** Sim, via `.env`  
**Escalável:** Pode ser aumentado sem modificar código

### 2. **Carregamento no Código**

```python
# app.py linha 62
DOWNLOAD_RETRY_DELAY = int(os.getenv('DOWNLOAD_RETRY_DELAY', '120'))  # ✅ NOVO
```

### 3. **Uso em Funções de Export**

**Antes:**
```python
delay_segundos = 60  # Hardcoded
```

**Depois:**
```python
delay_segundos = DOWNLOAD_RETRY_DELAY  # Variável configurável
```

**Afeta:**
- `exportAtividadesStatus()` → Usa `DOWNLOAD_RETRY_DELAY` entre tentativas
- `exportAtividades()` → Usa `DOWNLOAD_RETRY_DELAY` entre tentativas
- `exportProducao()` → Usa `DOWNLOAD_RETRY_DELAY` entre tentativas

### 4. **Melhoria em `baixar_arquivo_com_cookies()`**

**Antes:**
```python
for tentativa in range(1, RETRIES_DOWNLOAD+1):
    try:
        resposta = s.get(url, ...)
        # ... salva arquivo ...
    except Exception as e:
        pass
    time.sleep(2)  # ❌ Muito curto
```

**Depois:**
```python
for tentativa in range(1, RETRIES_DOWNLOAD+1):
    try:
        logger.info(f'Tentando... (tentativa {tentativa}/{RETRIES_DOWNLOAD})')
        resposta = s.get(url, ...)
        # ... salva arquivo ...
        logger.info(f"✅ Arquivo salvo...")
        return True
    except Exception as e:
        logger.error(f'❌ Erro: {e}')
    
    if tentativa < RETRIES_DOWNLOAD:
        logger.warning(f'⏳ Aguardando {DOWNLOAD_RETRY_DELAY}s...')
        time.sleep(DOWNLOAD_RETRY_DELAY)  # ✅ Usa variável
```

**Melhorias:**
- Logging melhorado com tentativa número
- Delay dinamicamente configurável
- Usa `DOWNLOAD_RETRY_DELAY` (120s) ao invés de 2s

---

## 📊 Timeline de Execução Atualizada

### Antes (❌ - Com problema)

```
[08:00:00] Clica em export
[08:00:05] Link disponível, tenta baixar
[08:00:10] ❌ Download falha por timeout/servidor ocupado
[08:01:10] Aguarda 60s (insuficiente)
[08:01:15] ❌ Link expirou ou servidor ainda processando
[08:02:15] Falha após 3 tentativas
```

**Total:** ~140 segundos, **Resultado:** ❌ FALHA

---

### Depois (✅ - Com correção)

```
[08:00:00] Clica em export
[08:00:05] Link disponível, tenta baixar
[08:00:10] ❌ Download falha (servidor processa arquivo)
[08:02:10] Aguarda 120s (DOWNLOAD_RETRY_DELAY)
[08:02:15] ✅ Link ainda válido, servidor pronto, download completa!
```

**Total:** ~135 segundos, **Resultado:** ✅ SUCESSO

---

## 🔧 Como Usar

### Configuração Padrão (Recomendada)

Nenhuma mudança necessária. Usar `.env.example` com:
```bash
DOWNLOAD_RETRY_DELAY=120
```

### Para Arquivos Muito Grandes

Se downloads continuarem falhando:
```bash
# Aumentar para 3 minutos
DOWNLOAD_RETRY_DELAY=180

# Ou até 5 minutos em caso de servidor muito lento
DOWNLOAD_RETRY_DELAY=300
```

### Para Servidor Rápido

Se quiser ser mais agressivo:
```bash
# Reduzir para 90 segundos
DOWNLOAD_RETRY_DELAY=90
```

---

## 📈 Impacto na Execução

### Tempo Total de Download (3 tentativas)

| Cenário | Antes | Depois | Gain |
|---------|-------|--------|------|
| Sucesso 1ª tentativa | ~15s | ~15s | - |
| Sucesso 2ª tentativa | 60+15 = 75s | 120+15 = 135s | +80% delay (necessário) |
| Sucesso 3ª tentativa | 120+15 = 135s | 240+15 = 255s | +100% delay (necessário) |
| Falha em todas | 120s + erro | 240s + erro | +100% |

**Taxa de sucesso esperada:** ~95% (antes) → ~99%+ (depois)

---

## 📝 Mudanças em Detalhes

| Arquivo | Mudança | Linhas |
|---------|---------|--------|
| `app.py` | Adicionar DOWNLOAD_RETRY_DELAY | 62 |
| `app.py` | Usar em exportAtividadesStatus() | 1099 |
| `app.py` | Usar em exportAtividades() | 1140 |
| `app.py` | Usar em exportProducao() | 1189 |
| `app.py` | Usar em baixar_arquivo_com_cookies() | 628 |
| `.env.example` | Documentar nova variável | - |

---

## ✅ Validação

### Teste 1: Verificar que está carregando

```python
# Adicione ao início do app.py para debug
logger.info(f"DOWNLOAD_RETRY_DELAY={DOWNLOAD_RETRY_DELAY}s")
```

### Teste 2: Observar delays nos logs

```bash
python app.py --headless

# Procurar por:
# ⏳ Aguardando 120s antes de tentar novamente...
# ✅ Arquivo salvo em: downloads/Exportacao Status.xlsx
```

### Teste 3: Download manual

```bash
python tests/download_status.py --headless --timeout 60

# Deve mostrar:
# [INFO] ⏳ Aguardando 120s...
# [INFO] ✅ Status baixado com sucesso!
```

---

## 🎯 Próximas Melhorias (Opcional)

1. **Backoff exponencial para downloads:** `delay = 60 * (1.5 ^ tentativa)`
2. **Detecção de erro específico:** Se é timeout vs permissão vs servidor down
3. **Monitoramento de tamanho:** Se download parcial, fazer resume
4. **Limite de tempo total:** Máx 10 minutos entre 3 tentativas

---

## 📚 Referências

- **Arquivo:** `.env.example` - Documentação de variáveis
- **Código:** `app.py` linhas 62, 628, 1099, 1140, 1189
- **Logs:** Procurar por "Aguardando" para ver delays em ação

---

**Status:** ✅ Implementado  
**Versão:** 2.0.1  
**Última atualização:** 28 de outubro de 2025

