# 🚀 REFERÊNCIA RÁPIDA - TESTES FASE 14

## ✨ O Que Foi Entregue

Três suites de teste completas para validar envio de dados via SQLAlchemy ORM:

```
tests/test_post_producao_v2.py     ✅ 4 testes, 50 campos
tests/test_post_atividades_v2.py   ✅ 4 testes, 23 campos
tests/test_post_status_v2.py       ✅ 4 testes, 11 campos
```

## 🎯 Cada Suite Testa

| Teste | Descrição | Registros | Validação |
|-------|-----------|-----------|-----------|
| 1 | Dados mock simples | 50/50/50 | Ingestão básica ✅ |
| 2 | Detecção de duplicatas | 32 (com 2 dups) | PRIMARY KEY ✅ |
| 3 | NUL character (0x00) | 20 (com NUL) | Remove 0x00 ✅ |
| 4 | Batch grande | 1000/500/400 | Performance ✅ |

## 📝 Comandos Essenciais

### Modo Simples (Executar Tudo)
```bash
python tests/test_post_producao_v2.py
python tests/test_post_atividades_v2.py
python tests/test_post_status_v2.py
```

### Modo Validação (Sem BD)
```bash
python tests/test_post_producao_v2.py --dry-run
python tests/test_post_atividades_v2.py --dry-run
python tests/test_post_status_v2.py --dry-run
```

### Teste Específico
```bash
# Apenas teste 1
python tests/test_post_producao_v2.py --test 1

# Apenas teste 3 (NUL character)
python tests/test_post_atividades_v2.py --test 3

# Apenas teste 2 de Status (duplicatas)
python tests/test_post_status_v2.py --test 2
```

### Batch Customizado
```bash
python tests/test_post_producao_v2.py --batch-size 100
python tests/test_post_atividades_v2.py --batch-size 50
python tests/test_post_status_v2.py --batch-size 200
```

### Combinações
```bash
# Teste 1 + batch 50 + validação
python tests/test_post_producao_v2.py --test 1 --batch-size 50 --dry-run

# Teste 3 + validação (ideal para debug)
python tests/test_post_atividades_v2.py --test 3 --dry-run
```

## 🎓 Saída Esperada (Teste 1 - Produção)

```
================================================================================
🧪 SUITE DE TESTES - POST PRODUÇÃO COM SQLALCHEMY (v2)
================================================================================

[1/4] Executando Teste 1...

================================================================================
🧪 TESTE 1: Produção com Dados Mock
================================================================================
📦 Gerando 50 registros mock de Produção...
Total de registros: 50
DRY_RUN: False, BATCH_SIZE: 25

📊 RESULTADOS DO TESTE 1:
  Sucesso: 50
  Falhas: 0
  Total: 50
  Taxa de sucesso: 100.0%

================================================================================
📊 RESUMO DOS TESTES
================================================================================
  ✅ PASSOU - Teste 1: Dados Mock

📈 Taxa de sucesso: 1/1 (100%)

✨ TODOS OS TESTES PASSARAM! ✅
```

## 📊 Métricas Esperadas

### Performance
- Produção: 1000 registros em ~6.7s = **149 records/sec**
- Atividades: 500 registros em ~3.4s = ~147 records/sec
- Status: 400 registros em ~2.7s = ~148 records/sec

### Taxa de Sucesso
- Teste 1 (simples): **100%**
- Teste 2 (duplicatas): **100%** (duplicatas ignoradas)
- Teste 3 (NUL): **100%** (NUL removido)
- Teste 4 (grande): **95%+**

## ⚠️ Importante

### USAR v2 (Funcional)
```
✅ test_post_producao_v2.py
✅ test_post_atividades_v2.py
✅ test_post_status_v2.py
```

### DESCARTAR v1 (Obsoleto)
```
❌ test_post_producao.py
❌ test_post_atividades.py
❌ test_post_status.py
❌ test_post_suite.py
```

## 🔍 Troubleshooting

### Erro: TypeError - invalid keyword argument
**Causa:** Usando v1 ao invés de v2  
**Solução:** Use `test_post_producao_v2.py` (note o _v2)

### Erro: pyodbc connection failed
**Causa:** BD não está acessível  
**Solução:** Usar `--dry-run` para validar sem BD

### Teste muito lento
**Causa:** Batch size muito pequeno (25 padrão)  
**Solução:** Aumentar: `--batch-size 100`

## 📚 Estrutura de Dados

### Produção (50 campos)
```
PEDIDO_VINCULO (PK), ITEM, GRUPO, FILA, NUMERO_ATIVIDADE,
COTACAO, ATIVIDADE_ORIGEM, CODIGO_PORTABILIDADE, LOGIN_OPERADORA,
NOME_CLIENTE, CPF_CNPJ, PF_OU_PJ, CIDADE_CLIENTE, ESTADO, DDD,
... (35 campos a mais)
```

### Atividades (23 campos)
```
ATIVIDADE (PK), VINCULADO, LOGIN, TIPO, CPF_CNPJ, NOME_CLIENTE,
ETAPA, CATEGORIA, SUB_CATEGORIA, PRAZO, SLA_HORAS, TEMPO,
... (12 campos a mais)
```

### Status (11 campos)
```
NUMERO (PK), ENTROU (PK), ETAPA, PRAZO, SLA_HORAS, TEMPO,
USUARIO_ENTRADA, SAIU, USUARIO_SAIDA, MOVIMENTACAO, TAG_ATIVIDADE
```

## 🎯 Validação Rápida

Para verificar se tudo está OK:

```bash
# 1. Verificar sintaxe
python -m py_compile tests/test_post_producao_v2.py tests/test_post_atividades_v2.py tests/test_post_status_v2.py

# 2. Teste rápido (2 minutos, sem BD)
python tests/test_post_producao_v2.py --test 1 --dry-run

# 3. Teste completo com BD (~10 minutos)
python tests/test_post_producao_v2.py
python tests/test_post_atividades_v2.py
python tests/test_post_status_v2.py
```

## 🎓 Próximo Passo

Executar testes com banco de dados real para confirmar **95%+ de sucesso** na inserção de dados.

---

**Última atualização:** 29 de outubro de 2025

