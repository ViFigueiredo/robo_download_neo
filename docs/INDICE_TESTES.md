# 📑 Índice de Testes SQL Server

**Última atualização:** 28 de outubro de 2025

---

## 🎯 Navegação Rápida

### Quero Usar os Testes
👉 **Comece aqui:** `docs/TESTES_SUMARIO.md` (2 min de leitura)

### Quero Um Guia Completo
👉 **Leia:** `docs/TESTES_SQL_SERVER.md` (10 min de leitura)

### Quero Uma Referência Rápida
👉 **Veja:** `tests/README.md` (5 min de leitura)

### Quero Usar Interativamente
👉 **Execute:** `python tests/quick_start.py`

---

## 📂 Estrutura de Arquivos

### 🧪 Testes (Novos)

```
tests/
├── test_post_sql_atividades.py    # SQL Server: Atividades
├── test_post_sql_status.py        # SQL Server: Status
├── test_post_sql_producao.py      # SQL Server: Produção
└── quick_start.py                 # Menu interativo
```

### 📚 Documentação

```
docs/
├── TESTES_SQL_SERVER.md           # Guia completo (400+ linhas)
├── TESTES_SUMARIO.md              # Resumo (2 páginas)
└── RESUMO_TESTES_SQL_SERVER.md    # Detalhes técnicos
```

---

## 📊 Tabelas de Referência

### Testes Disponíveis

| Nome | Arquivo | Tabela SQL | Status |
|------|---------|-----------|--------|
| Atividades | `test_post_sql_atividades.py` | `EXPORTACAO_ATIVIDADE` | ✅ |
| Status | `test_post_sql_status.py` | `EXPORTACAO_STATUS` | ✅ |
| Produção | `test_post_sql_producao.py` | `EXPORTACAO_PRODUCAO` | ✅ |

### Opções de Linha de Comando

| Opção | Descrição | Exemplo |
|-------|-----------|---------|
| `--file FILE` | Arquivo Excel específico | `--file ./meu.xlsx` |
| `--json FILE` | JSON parseado | `--json ./parsed.json` |
| `--dry-run` | Simular sem enviar | `--dry-run` |
| `--batch-size N` | Tamanho do batch | `--batch-size 50` |
| `--post-retries N` | Tentativas HTTP | `--post-retries 5` |
| `--backoff-base N` | Fator backoff | `--backoff-base 2.0` |
| `--verbose` | Debug detalhado | `--verbose` |
| `--help` | Ajuda completa | `--help` |

---

## 🚀 Exemplos de Uso

### Básico
```bash
python tests/test_post_sql_atividades.py
```

### Com DRY_RUN
```bash
python tests/test_post_sql_atividades.py --dry-run
```

### Com Arquivo Específico
```bash
python tests/test_post_sql_atividades.py --file ./arquivo.xlsx
```

### Com Debug
```bash
python tests/test_post_sql_atividades.py --verbose
```

### Combinado
```bash
python tests/test_post_sql_atividades.py --dry-run --verbose --batch-size 10
```

### Menu Interativo
```bash
python tests/quick_start.py
```

---

## 📈 Workflow Recomendado

### 1️⃣ Testar Conexão
```bash
python tests/sql_connection.py
```

### 2️⃣ Testar com DRY_RUN
```bash
python tests/test_post_sql_atividades.py --dry-run
```

### 3️⃣ Testar Real
```bash
python tests/test_post_sql_atividades.py
```

### 4️⃣ Verificar Logs
```bash
tail -f logs/sent_records_atividades.jsonl
```

---

## 🔍 Troubleshooting

### Problema: "Arquivo não encontrado"
**Solução:** 
- Rode download primeiro: `python tests/download_atividades.py`
- Ou use `--file` com caminho completo

### Problema: "Conexão recusada"
**Solução:**
- Verificar SQL Server rodando
- Verificar `.env` com credenciais
- Teste: `python tests/sql_connection.py`

### Problema: "Tabela não existe"
**Solução:**
- Criar tabela no banco
- Verificar nome em `bases/sql_map.json`

---

## 📊 Docs Disponíveis

| Doc | Foco | Tamanho | Tempo Leitura |
|-----|------|---------|--------------|
| `TESTES_SUMARIO.md` | 🚀 Começar rápido | 2 páginas | 2 min |
| `TESTES_SQL_SERVER.md` | 📚 Guia completo | 10 páginas | 10 min |
| `RESUMO_TESTES_SQL_SERVER.md` | 📋 Detalhes técnicos | 8 páginas | 8 min |
| `tests/README.md` | 🔍 Referência rápida | 5 páginas | 5 min |
| **Este arquivo** | 📑 Índice/Navegação | 2 páginas | 2 min |

---

## ✅ Checklist: Pronto para Usar?

- [ ] Leu `TESTES_SUMARIO.md`?
- [ ] Executou `python tests/test_post_sql_atividades.py --dry-run`?
- [ ] Verificou conexão SQL: `python tests/sql_connection.py`?
- [ ] Tem arquivo em `downloads/Exportacao*.xlsx`?
- [ ] Credenciais em `.env` estão certas?
- [ ] Tabelas existem no banco SQL?

Se sim em tudo, **está pronto para enviar dados!** 🚀

---

## 💡 Dicas Úteis

### Dica 1: Use DRY_RUN Sempre Primeiro
```bash
python tests/test_post_sql_atividades.py --dry-run
```

### Dica 2: Veja Logs Estruturados
```bash
# Ver registros enviados
cat logs/sent_records_atividades.jsonl | jq '.'

# Ver apenas erros
cat logs/sent_records_atividades.jsonl | jq 'select(.status=="failed")'
```

### Dica 3: Teste com Batch Pequeno
```bash
# Útil para debug
python tests/test_post_sql_atividades.py --batch-size 5 --verbose
```

### Dica 4: Use Menu Interativo
```bash
python tests/quick_start.py
```

---

## 📞 Suporte

### Próximos Passos

1. **Leia:** `docs/TESTES_SUMARIO.md`
2. **Execute:** `python tests/quick_start.py`
3. **Teste:** `python tests/test_post_sql_atividades.py --dry-run`
4. **Valide:** Dados no SQL Server

### Documentação Completa

Veja `docs/TESTES_SQL_SERVER.md` para:
- Exemplos detalhados
- Troubleshooting
- Cases de uso
- Configurações avançadas

---

**Status:** ✅ Testes SQL Server Implementados e Documentados  
**Versão:** 2.0.9  
**Data:** 28 de outubro de 2025

---

*Para retomar a navegação, veja o topo deste arquivo.*
