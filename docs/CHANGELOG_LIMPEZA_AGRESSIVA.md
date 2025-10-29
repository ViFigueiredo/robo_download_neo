# 📋 Changelog - Limpeza de Logs AGRESSIVA

**Data:** 29 de outubro de 2025  
**Versão:** 2.3.0  
**Mudança:** Limpeza de logs agressiva (remover TUDO)

---

## 🔄 Mudança Realizada

### Arquivo: `app.py` (Linhas 1510-1534)

#### ANTES (Conservador)

```python
def limpar_logs():
    """
    🔧 NOVO (Fase 10): Limpa pasta \logs antes de cada execução
    Mantém arquivo robo_download.log para histórico, remove error_records_*.jsonl e sent_records_*.jsonl
    """
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        return 0
    
    removidos = 0
    
    # Arquivos que SEMPRE podem ser removidos (logs de execução anterior)
    patterns_remover = [
        'error_records_*.jsonl',      # Logs de erros da execução anterior
        'sent_records_*.jsonl',        # Logs de envios da execução anterior
    ]
    
    for pattern in patterns_remover:
        for arquivo in logs_dir.glob(pattern):
            try:
                arquivo.unlink()
                logger.info(f"🗑️  Log removido: {arquivo.name}")
                removidos += 1
            except Exception as e:
                logger.warning(f"⚠️  Não foi possível remover log: {arquivo.name} - {e}")
    
    if removidos > 0:
        logger.info(f"✅ Limpeza de logs: {removidos} arquivo(s) removido(s)")
    
    return removidos
```

**Resultado:**
- Remove: `error_records_*.jsonl`, `sent_records_*.jsonl`
- Mantém: `robo_download.log`, `reprocessar_erros.log`

---

#### DEPOIS (Agressivo - ✅ NOVO)

```python
def limpar_logs():
    """
    🔧 NOVO (Fase 10): Limpa pasta \logs antes de cada execução
    Remove TODOS os arquivos de log (robo_download.log, error_records_*.jsonl, sent_records_*.jsonl, etc)
    """
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        return 0
    
    removidos = 0
    
    # Remove TODOS os arquivos na pasta logs
    for arquivo in logs_dir.glob('*'):
        if arquivo.is_file():
            try:
                arquivo.unlink()
                logger.info(f"🗑️  Log removido: {arquivo.name}")
                removidos += 1
            except Exception as e:
                logger.warning(f"⚠️  Não foi possível remover log: {arquivo.name} - {e}")
    
    if removidos > 0:
        logger.info(f"✅ Limpeza de logs: {removidos} arquivo(s) removido(s)")
    
    return removidos
```

**Resultado:**
- Remove: TUDO (todos os arquivos na pasta `logs/`)
- Mantém: NADA (pasta fica completamente vazia)

---

## 📊 Comparação

| Aspecto | ANTES | DEPOIS |
|---------|-------|--------|
| **Padrão** | `error_records_*.jsonl` + `sent_records_*.jsonl` | `*` (tudo) |
| **robo_download.log** | ✓ Mantém | ❌ Remove |
| **reprocessar_erros.log** | ✓ Mantém | ❌ Remove |
| **Pasta final** | 2 arquivos (0.05 MB) | VAZIA (0 MB) |
| **Chamadas glob** | 2 padrões | 1 padrão simples |
| **Complexidade** | Média | Baixa |

---

## ✅ Teste de Verificação

```bash
python teste_limpeza_agressiva.py
```

**Output:**
```
ANTES:   2 arquivo(s), 0.05 MB
  - reprocessar_erros.log (0.01 MB)
  - robo_download.log (0.03 MB)

DEPOIS:  0 arquivo(s)
  ✅ PASTA COMPLETAMENTE VAZIA!
```

---

## 🚀 Impacto

### Quando Executa
- **Início de cada `executar_rotina()`**
- **Antes de qualquer processamento**
- **Automaticamente**

### O que Vê na Console

```
🧹 LIMPEZA PRÉ-EXECUÇÃO
  🗑️  Log removido: reprocessar_erros.log (0.01 MB)
  🗑️  Log removido: robo_download.log (0.03 MB)
  ✅ Limpeza de logs: 2 arquivo(s) removido(s)

[Execução prossegue...]
```

### Estado Final da Pasta `logs/`

**Primeira execução:** Vazia → Cria novos logs → Próxima execução remove

```
Ciclo:
[VAZIA] → 📥 executa → [COM LOGS] → 🧹 limpa → [VAZIA] → ...
```

---

## 💾 Reverter se Necessário

Se precisar voltar ao comportamento anterior:

```python
def limpar_logs():
    """Versão anterior (conservadora)"""
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        return 0
    
    removidos = 0
    patterns_remover = [
        'error_records_*.jsonl',
        'sent_records_*.jsonl',
    ]
    
    for pattern in patterns_remover:
        for arquivo in logs_dir.glob(pattern):
            try:
                arquivo.unlink()
                logger.info(f"🗑️  Log removido: {arquivo.name}")
                removidos += 1
            except Exception as e:
                logger.warning(f"⚠️  Erro: {e}")
    
    if removidos > 0:
        logger.info(f"✅ Limpeza de logs: {removidos} arquivo(s) removido(s)")
    
    return removidos
```

---

## 📝 Notas

- ✅ **Testado:** Sim, rodou 100% com sucesso
- ✅ **Funcional:** Sim, remove corretamente
- ✅ **Integrado:** Sim, executar_rotina() chama automaticamente
- ⚠️  **Histórico:** Nenhum arquivo é mantido entre execuções
- 💡 **Dica:** Se precisa de histórico, fazer backup manual

---

**Versão anterior:** 2.2.0 (Conservadora)  
**Versão atual:** 2.3.0 (Agressiva)  
**Data:** 29 de outubro de 2025  
**Status:** ✅ LIVE
