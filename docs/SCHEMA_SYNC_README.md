# 🎯 Sistema de Sincronização de Schema - README

**Implementação:** 29 de outubro de 2025  
**Status:** ✅ Completo e Testado  
**Versão:** 1.0.0

---

## 📌 Resumo Executivo

Implementado **sistema automático de sincronização de schema** que mantém modelos ORM (Python/SQLAlchemy) sempre sincronizados com tabelas do SQL Server. Quando você modifica um modelo, a tabela no banco atualiza automaticamente sem perder dados.

```
┌──────────────────┐
│ Modelos ORM      │
│ (models_*.py)    │
└────────┬─────────┘
         │ Mudou?
         ▼
┌──────────────────────────────┐
│ sincronizar_schema.py        │
│ ✅ Detecta diferenças        │
│ ✅ Gera ALTER TABLE          │
│ ✅ Executa no SQL Server     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────┐
│ SQL Server 2022  │
│ (Tabelas)        │
└──────────────────┘
```

---

## 🚀 Uso Rápido

### Para Desenvolvedores

```bash
# 1. Modificar modelo
# Edite models/models_generated.py ou rode gerar_models_dinamicos.py

# 2. Sincronizar schema (padrão)
python migrate_tables.py

# 3. Pronto! Banco está sincronizado
```

### Para DevOps / Produção

```bash
# 1. Verificar diferenças (SEM executar)
python sincronizar_schema.py --check-only

# 2. Gerar SQL para review
python sincronizar_schema.py --generate-sql

# 3. Revisar arquivo em logs/schema_sync_*.sql

# 4. Executar sincronização
python sincronizar_schema.py

# 5. Verificar status
python migrate_tables.py --status
```

---

## 📚 Documentação Principal

| Documento | Descrição |
|-----------|-----------|
| **[SINCRONIZACAO_SCHEMA_AUTOMATICA.md](./SINCRONIZACAO_SCHEMA_AUTOMATICA.md)** | 📖 Guia completo com exemplos práticos |
| **[SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md](./SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md)** | ✅ Relatório final com testes e resultados |

---

## 🎯 Funcionalidades

### ✅ Detectar Diferenças
```bash
python sincronizar_schema.py --check-only
```

Identifica:
- ➕ Colunas novas (no modelo, não no banco)
- ❌ Colunas removidas (no banco, não no modelo)
- ⚠️ Tipos diferentes

### ✅ Gerar Scripts SQL
```bash
python sincronizar_schema.py --generate-sql
```

Salva em `logs/schema_sync_YYYYMMDD_HHMMSS.sql` para review manual.

### ✅ Executar Sincronização
```bash
python sincronizar_schema.py
```

Executa automaticamente:
- ADD COLUMN para colunas novas
- ALTER COLUMN para tipos diferentes
- DROP COLUMN comentado (segurança)

### ✅ Integração Automática
```bash
python migrate_tables.py
```

Fluxo padrão:
1. Cria tabelas (se não existem)
2. **Sincroniza schema automaticamente** ← NOVO!
3. Verifica status

---

## 🔍 Exemplo Prático

### Cenário: Adicionar Coluna ao Modelo

**Passo 1:** Editar modelo
```python
# models/models_generated.py
class ExportacaoStatus(Base):
    __tablename__ = 'EXPORTACAO_STATUS'
    
    # ... colunas existentes ...
    DATA_IMPORTACAO = Column(String)
    
    # ✨ NOVA COLUNA
    USUARIO = Column(String(4000))  # ← Adicionar aqui
```

**Passo 2:** Executar sincronização
```bash
$ python sincronizar_schema.py

Resultado:
🔍 Analisando diferenças...
   📊 Tabela: EXPORTACAO_STATUS
   ➕ NOVA coluna: USUARIO (VARCHAR(4000))

⚙️  Executando alterações...
   ✅ Executado com sucesso

ALTER TABLE EXPORTACAO_STATUS ADD USUARIO VARCHAR(4000) NULL;
```

**Passo 3:** Verificar no banco
```bash
$ python migrate_tables.py --status

EXPORTACAO_STATUS
   Colunas: 13 ← Era 12, agora 13!
```

✅ **Coluna adicionada com sucesso ao SQL Server!**

---

## 📊 Arquivos Principais

```
robo_download_neo/
├── sincronizar_schema.py       ⭐ Script de sincronização (440+ linhas)
├── migrate_tables.py           🔄 Integração automática (atualizado)
├── models/
│   ├── models_generated.py     📋 Modelos gerados dinamicamente
│   └── db_operations.py        🔌 Operações de banco
├── logs/
│   ├── schema_sync_*.sql       📄 Scripts SQL executados
│   └── ...
└── docs/
    ├── SINCRONIZACAO_SCHEMA_AUTOMATICA.md        📖 Guia completo
    └── SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md    ✅ Relatório final
```

---

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# SQL Server
DB_SERVER=192.168.11.200,1434
DB_DATABASE=rpa_neocrm
DB_USERNAME=sa
DB_PASSWORD=sua_senha
DB_DRIVER=ODBC Driver 18 for SQL Server
```

### Requisitos
- Python 3.10+
- SQLAlchemy 2.0+
- pandas (para gerar_sql_map_automatico.py)
- pyodbc (para SQL Server)

---

## 🛡️ Segurança

### Proteções Implementadas

✅ **Backup de Scripts**
- Todos os scripts SQL salvos em `logs/`
- Pode ser reexecutado ou revisado

✅ **Modo Check-Only**
- Nenhuma mudança no banco
- Apenas relatório de diferenças

✅ **Modo Generate-SQL**
- Salva scripts sem executar
- Permite review antes de aplicar

✅ **DROP Comentado**
- Remoção de colunas é comentada
- Requer ativação manual

✅ **Transações**
- Cada ALTER é independente
- Rollback automático em erro

---

## 🧪 Validação

### Testes Realizados

| Teste | Status | Descrição |
|-------|--------|-----------|
| Detecção de diferenças | ✅ PASSOU | 3/3 tabelas detectadas corretamente |
| Sincronização automática | ✅ PASSOU | Coluna USUARIO adicionada com sucesso |
| Verificação pós-sync | ✅ PASSOU | Coluna confirmada no SQL Server (13 cols) |
| Modo check-only | ✅ PASSOU | Nenhuma alteração no banco |
| Geração de SQL | ✅ PASSOU | Scripts salvos corretamente |

---

## 📈 Resultados

### Antes (Dessincronizado)
```
EXPORTACAO_STATUS: 12 colunas
  ❌ Faltava USUARIO
  ❌ Tinha USUARIO_ENTRADA / USUARIO_SAIDA extras
```

### Depois (Sincronizado)
```
EXPORTACAO_STATUS: 13 colunas ✅
  ✅ Tem USUARIO
  ✅ USUARIO_ENTRADA / USUARIO_SAIDA comentadas para remoção manual
```

---

## 🚀 Fluxo de Trabalho Recomendado

### Desenvolvimento Local

```bash
# 1. Modificar modelo
# Edite models/models_generated.py

# 2. Teste com check-only
python sincronizar_schema.py --check-only

# 3. Se OK, sincronizar
python sincronizar_schema.py

# 4. Executar app.py
python app.py
```

### Produção

```bash
# 1. Backup do banco
BACKUP DATABASE rpa_neocrm TO DISK = '...';

# 2. Check-only (sem alterar nada)
python sincronizar_schema.py --check-only

# 3. Gerar SQL para review
python sincronizar_schema.py --generate-sql

# 4. Review humano (importante!)
# Edite logs/schema_sync_*.sql se necessário

# 5. Executar
python sincronizar_schema.py

# 6. Verificar
python migrate_tables.py --status

# 7. Se falhar, restaurar backup
RESTORE DATABASE rpa_neocrm FROM DISK = '...';
```

---

## ❓ FAQ

**P: Posso sincronizar enquanto o app.py está rodando?**
R: Não recomendado. Melhor parar app.py, sincronizar, depois reiniciar.

**P: E se falhar no meio?**
R: Cada SQL é transação. Se um falha, anteriores foram commitados. Verifique logs/schema_sync_*.sql.

**P: Como desfazer uma sincronização?**
R: Restaure backup do banco. Os scripts estão em logs/ para referência.

**P: Preciso atualizar migrate_tables.py?**
R: Não. Já vem integrado. Basta usar `python migrate_tables.py`.

**P: Posso adicionar colunas manualmente no SQL Server?**
R: Não recomendado. Use o modelo Python, depois sincronize.

---

## 📞 Suporte

### Arquivos de Referência
- 📖 [Documentação Completa](./SINCRONIZACAO_SCHEMA_AUTOMATICA.md)
- ✅ [Relatório Final com Testes](./SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md)
- 🔧 [Copilot Instructions](./.github/copilot-instructions.md)

### Logs
```bash
# Ver último sync
cat logs/schema_sync_*.sql

# Ver logs de execução
python sincronizar_schema.py 2>&1 | tee sync.log
```

---

## ✨ Próximas Etapas

### Agora Disponível Para
- ✅ Fase 16: Testes com dados reais (~100k registros)
- ✅ Fase 17: Recuperação de 19.773 registros com erro anterior

### Benefícios
- 🚀 Sincronização automática vs manual
- 🛡️ Proteções contra dados perdidos
- 📖 Documentação clara e exemplos
- 🔄 Schema sempre consistente
- 🧪 Testado com casos reais

---

## 🎉 Conclusão

**Sistema completo de sincronização de schema implementado, testado e pronto para produção!**

Use `sincronizar_schema.py` e `migrate_tables.py` para manter seus modelos e banco de dados sempre sincronizados.

---

**Status:** ✅ **Pronto para Fase 16 - Testes com Dados Reais**

Para mais detalhes, consulte:
- [SINCRONIZACAO_SCHEMA_AUTOMATICA.md](./SINCRONIZACAO_SCHEMA_AUTOMATICA.md)
- [SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md](./SINCRONIZACAO_SCHEMA_ENTREGA_FINAL.md)
