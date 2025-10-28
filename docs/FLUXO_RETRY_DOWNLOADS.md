# 🔄 Diagrama de Fluxo - Retry de Downloads (Fase 8)

---

## Fluxo Geral da Aplicação (Com Retry)

```
┌─ executar_rotina()
│
├─ FASE 1: Downloads com Retry Automático
│  │
│  ├─ exportAtividadesStatus() ─┬─ Tentativa 1 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                            │                └─ ❌ Erro → Aguarda 60s
│  │                            ├─ Tentativa 2 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                            │                └─ ❌ Erro → Aguarda 60s
│  │                            └─ Tentativa 3 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                                             └─ ❌ Erro → 💥 FALHA
│  │
│  ├─ exportAtividades() ─┬─ Tentativa 1 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                      │                └─ ❌ Erro → Aguarda 60s
│  │                      ├─ Tentativa 2 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                      │                └─ ❌ Erro → Aguarda 60s
│  │                      └─ Tentativa 3 ─┬─ ✅ Sucesso → PRÓXIMO
│  │                                       └─ ❌ Erro → 💥 FALHA
│  │
│  └─ exportProducao() ─┬─ Tentativa 1 ─┬─ ✅ Sucesso → PRÓXIMO
│                       │                └─ ❌ Erro → Aguarda 60s
│                       ├─ Tentativa 2 ─┬─ ✅ Sucesso → PRÓXIMO
│                       │                └─ ❌ Erro → Aguarda 60s
│                       └─ Tentativa 3 ─┬─ ✅ Sucesso → PRÓXIMO
│                                        └─ ❌ Erro → 💥 FALHA
│
├─ FASE 2: Processamento (SEM RETRY)
│  │
│  ├─ Processar Status ─┬─ ✅ Sucesso
│  │                    └─ ❌ Erro → Log + PRÓXIMO
│  │
│  ├─ Processar Atividades ─┬─ ✅ Sucesso
│  │                        └─ ❌ Erro → Log + PRÓXIMO
│  │
│  └─ Processar Produção ─┬─ ✅ Sucesso
│                         └─ ❌ Erro → Log + PRÓXIMO
│
├─ Geração de Relatórios
│  ├─ envios_resumo.jsonl (com métricas)
│  ├─ sent_records_*.jsonl (com detalhes)
│  └─ logs/robo_download.log (com tudo)
│
└─ FIM (Próxima execução em 30 min)
```

---

## Fluxo Detalhado de 1 Tentativa de Download

```
┌─ Tentativa 1/3
│
├─ Esperar elemento carregar
│  └─ if timeout: ❌ Exception → Captura no try-except
│
├─ Clicar em painel
│  └─ if não encontrado: ❌ Exception → Captura no try-except
│
├─ Selecionar data (últimos 90 dias)
│  └─ if erro: ❌ Exception → Captura no try-except
│
├─ Clicar botão buscar
│  └─ if falha: ❌ Exception → Captura no try-except
│
├─ Realizar download
│  ├─ if sucesso: ✅ Arquivo criado em downloads/
│  └─ if falha: ❌ Exception → Captura no try-except
│
├─ Fechar modal
│  └─ if erro: ❌ Exception → Captura no try-except
│
└─ return ✅ SUCESSO (função termina aqui)
   OU
   ❌ ERRO CAPTURADO (vai para try-except abaixo)
   │
   ├─ if tentativa < 3:
   │  ├─ Log: "⚠️ Tentativa 1/3 falhou"
   │  ├─ Aguarda 60 segundos
   │  └─ Volta para Tentativa 2/3
   │
   └─ elif tentativa == 3:
      ├─ Log: "❌ FALHA FINAL"
      └─ raise (exceção propagada)
```

---

## Timeline de Execução

### Cenário 1: Sucesso Imediato

```
[08:00:00] Iniciar downloads
[08:00:02] ✅ Status baixado com sucesso!
[08:00:14] ✅ Atividades baixado com sucesso!
[08:00:26] ✅ Produção baixado com sucesso!
[08:00:26] Iniciar processamento
[08:00:40] ✅ Routine completa em ~40 segundos
```

**Total:** ~40 segundos

---

### Cenário 2: Falha na 1ª, Sucesso na 2ª

```
[08:00:00] Iniciar downloads
[08:00:02] ❌ Status falhou (tentativa 1/3): Connection timeout
[08:00:02] ⚠️  Aguardando 60 segundos...
[08:01:02] ✅ Status baixado com sucesso! (tentativa 2/3)
[08:01:14] ✅ Atividades baixado com sucesso! (sem falha)
[08:01:26] ✅ Produção baixado com sucesso! (sem falha)
[08:01:26] Iniciar processamento
[08:01:40] ✅ Routine completa em ~100 segundos (~1m40s)
```

**Total:** ~100 segundos (1 minuto de delay)

---

### Cenário 3: Falha em Todas (3 Tentativas)

```
[08:00:00] Iniciar downloads
[08:00:02] ❌ Status falhou (tentativa 1/3): SSLError
[08:00:02] ⚠️  Aguardando 60 segundos...
[08:01:02] ❌ Status falhou (tentativa 2/3): SSLError
[08:01:02] ⚠️  Aguardando 60 segundos...
[08:02:02] ❌ Status falhou (tentativa 3/3): SSLError
[08:02:02] ❌ FALHA FINAL: Não consegui baixar Status após 3 tentativas
[08:02:02] 💥 Exception levantada
[08:02:03] Rotina interrompida
```

**Total:** ~120 segundos (2 minutos de delay)  
**Resultado:** Falha total, nenhum arquivo processado

---

## Logs Esperados

### Log completo de sucesso (cenário 2)

```ini
[INFO] [FASE 1/2] Iniciando downloads com retry automático...
[INFO] ════════════════════════════════════════════════════
[INFO] [1/3] Exportando Status de Atividades...
[WARNING] ⚠️ Erro ao baixar Status (tentativa 1/3): [SSL: EOF_OCCURRED] EOF occurred in violation of protocol
[INFO]    Aguardando 60s antes de tentar novamente...
[INFO] [Aguardando...] Tempo decorrido: 30s
[INFO] [Aguardando...] Tempo decorrido: 60s
[INFO] ✅ Status de Atividades baixado com sucesso!
[INFO] [2/3] Exportando Atividades...
[INFO] ✅ Atividades baixado com sucesso!
[INFO] [3/3] Exportando Produção...
[INFO] ✅ Produção baixado com sucesso!
[INFO] ════════════════════════════════════════════════════
[INFO] ✅ FASE 1 completa: Todos os 3 arquivos baixados!
[INFO]
[INFO] [FASE 2/2] Processando arquivos baixados...
[INFO] ════════════════════════════════════════════════════
[INFO] [status] Parsed 127 registros
[INFO] [status] 📊 ESTATÍSTICAS - Processamento concluído (127/127 - 100%)
[INFO] [status] ✅ Enviado: 127 registros com sucesso
[INFO] [atividades] Parsed 45 registros
[INFO] [atividades] 📊 ESTATÍSTICAS - Processamento concluído (45/45 - 100%)
[INFO] [atividades] ✅ Enviado: 45 registros com sucesso
[INFO] [producao] Parsed 234 registros
[INFO] [producao] 📊 ESTATÍSTICAS - Processamento concluído (234/234 - 100%)
[INFO] [producao] ✅ Enviado: 234 registros com sucesso
[INFO] ════════════════════════════════════════════════════
[INFO] ✅ ROTINA COMPLETA COM SUCESSO!
[INFO] Total processado: 406 registros
```

---

## Fluxo de Erro

```
┌─ Exceção capturada no try-except
│
├─ Analisar tipo de erro
│  ├─ SSLError → Problema de rede (retry pode ajudar)
│  ├─ TimeoutError → Servidor lento (retry pode ajudar)
│  ├─ ConnectionError → Sem conexão (retry pode ajudar)
│  └─ Outro erro → Talvez não seja rede (mas tenta mesmo assim)
│
├─ if tentativa < 3:
│  ├─ Log warning: "⚠️ Tentativa X/3: aguardando 60s..."
│  ├─ time.sleep(60)
│  └─ Volta para top do loop (tenta novamente)
│
└─ else (tentativa == 3):
   ├─ Log error: "❌ FALHA FINAL após 3 tentativas"
   ├─ Mostra último erro
   └─ raise (propagada para quem chamou)
```

---

## Estados Possíveis

```
┌─────────────────────────────────────────┐
│  ESTADO INICIAL: Aguardando 08:00-22:00 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ FASE 1: Downloading (com retry)         │
│ - exportAtividadesStatus (3 tentativas) │
│ - exportAtividades (3 tentativas)       │
│ - exportProducao (3 tentativas)         │
└────────┬─────────────────────┬──────────┘
         │                     │
         ▼ (Sucesso)           ▼ (Falha após 3)
┌──────────────────────┐  ┌─────────────────────┐
│ FASE 2: Processing   │  │ ERROR STATE         │
│ - Parse + Insert     │  │ App para completamente
│ - Per-record logic   │  │ Exception em log
└────────┬─────────────┘  └─────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ SUCESSO: Resumo enviado                 │
│ - envios_resumo.jsonl                   │
│ - sent_records_*.jsonl                  │
│ - robo_download.log                     │
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ AGENDAMENTO: Próxima em 30 minutos      │
│ App em espera até próxima execução       │
└─────────────────────────────────────────┘
```

---

## Matriz de Decisão: Quando Retry Ajuda?

```
┌──────────────────────────┬─────────────────┬──────────────┐
│ Tipo de Erro             │ Causa Provável  │ Retry Ajuda? │
├──────────────────────────┼─────────────────┼──────────────┤
│ SSLError, SSLEOFError    │ Rede instável   │ ✅ SIM       │
│ ConnectionError          │ Firewall/proxy  │ ✅ SIM       │
│ TimeoutError             │ Servidor lento  │ ✅ SIM       │
│ ConnectionResetError     │ Reset rede      │ ✅ SIM       │
│ 500 Internal Error       │ Servidor bug    │ ✅ SIM       │
│ 503 Service Unavailable  │ Servidor down   │ ✅ SIM (depois volta) │
├──────────────────────────┼─────────────────┼──────────────┤
│ 404 Not Found            │ URL inválida    │ ❌ NÃO       │
│ 401 Unauthorized         │ Credencial erro │ ❌ NÃO       │
│ 403 Forbidden            │ Permissão erro  │ ❌ NÃO       │
│ XPath não encontrado     │ UI mudou        │ ❌ NÃO       │
│ Parse error              │ Formato errado  │ ❌ NÃO       │
└──────────────────────────┴─────────────────┴──────────────┘
```

---

## Comparação: Antes vs Depois

```
╔═══════════════════════════════════════════════════════════╗
║                    ANTES (v1.9)                           ║
╠═══════════════════════════════════════════════════════════╣
║ Falha de rede → Exception → App para                      ║
║ Resultado: 0 arquivos, nenhuma tentativa adicional       ║
║ Usuário: "Por que parou?"                                ║
║ Ação necessária: Reiniciar manualmente                   ║
╚═══════════════════════════════════════════════════════════╝

                              ⬇️ MELHORIA ⬇️

╔═══════════════════════════════════════════════════════════╗
║                     DEPOIS (v2.0)                         ║
╠═══════════════════════════════════════════════════════════╣
║ Falha de rede → Aguarda 60s → Tenta novamente            ║
║ Sucesso: Download continua 2 outros arquivos             ║
║ Resultado: 3 arquivos processados normalmente             ║
║ Usuário: Tudo OK, não percebeu o erro transitório        ║
║ Ação necessária: NENHUMA (automático!)                   ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Referências Rápidas

- **Implementação:** `app.py` linhas 1073-1187
- **Documentação:** `docs/ESTRATEGIA_RETRY_DOWNLOADS.md`
- **Resumo:** `docs/RESUMO_FASE_8_RETRY.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

**Versão:** 2.0  
**Status:** ✅ IMPLEMENTADO  
**Última atualização:** 28 de outubro de 2025
