# 🔄 Sincronização Automática de Schema

**Última atualização:** 29 de outubro de 2025

## 📋 Visão Geral

O sistema de sincronização automática de schema mantém os modelos ORM (em `models_generated.py`) sempre sincronizados com as tabelas do SQL Server. Quando você:

1. ✅ **Modifica os modelos** → Novas colunas são adicionadas automaticamente
2. ✅ **Remove colunas dos modelos** → Script sugere remoção (comentado para segurança)
3. ✅ **Altera tipos de dados** → Colunas são alteradas automaticamente
4. ✅ **Adiciona novas colunas** → SQL Server atualizado sem perder dados

---

## 🚀 Uso Rápido

### Sincronização Automática (Padrão)
```bash
python migrate_tables.py
```
Cria tabelas (se não existem) + sincroniza schema automaticamente.

### Apenas Detectar Diferenças
```bash
python sincronizar_schema.py --check-only
```
Mostra quais alterações são necessárias **sem executar**.

### Gerar Scripts SQL (Sem Executar)
```bash
python sincronizar_schema.py --generate-sql
```
Salva scripts em `logs/schema_sync_YYYYMMDD_HHMMSS.sql` para review manual.

### Sincronizar Especificamente
```bash
python migrate_tables.py --sync-schema
```
Executa apenas sincronização de schema.

### Apenas Verificar Status
```bash
python migrate_tables.py --status
```
Mostra status das tabelas e colunas.

---

## 📊 Exemplo: Adicionando Nova Coluna

### 1️⃣ Modificar Modelo
Edite `models/models_generated.py` ou `gerar_models_dinamicos.py`:

```python
class ExportacaoStatus(Base):
    __tablename__ = 'EXPORTACAO_STATUS'
    
    # ... colunas existentes ...
    DATA_IMPORTACAO = Column(String, nullable=False, default='')
    
    # ✨ NOVA COLUNA
    NOVO_CAMPO = Column(String(4000))  # ← Adicionar aqui
```

### 2️⃣ Executar Sincronização
```bash
python sincronizar_schema.py --check-only
```

Saída esperada:
```
📊 Tabela: EXPORTACAO_STATUS
   ➕ NOVA coluna: NOVO_CAMPO (VARCHAR(4000))
   ✅ ADD: NOVO_CAMPO
```

### 3️⃣ Aplicar Alteração
```bash
python sincronizar_schema.py
```

Resultado:
```
⚙️  Executando alterações no SQL Server...
   📝 Tabela: EXPORTACAO_STATUS
   ✅ Executado com sucesso
   
ALTER TABLE EXPORTACAO_STATUS ADD NOVO_CAMPO VARCHAR(4000) NULL;
```

### 4️⃣ Verificar
```bash
python migrate_tables.py --status
```

SQL Server agora tem a coluna NOVO_CAMPO! ✅

---

## 🔍 Como Funciona Internamente

### Fluxo de Sincronização

```
┌─────────────────────┐
│ Modelos ORM         │  models_generated.py
│ (Python Classes)    │
└──────────┬──────────┘
           │
           ▼ Ler estrutura
┌─────────────────────┐
│ SchemaSynchronizer  │  sincronizar_schema.py
│ - Detecta diffs     │
│ - Gera ALTER TABLE  │
│ - Executa no SQL    │
└──────────┬──────────┘
           │
           ▼ Executar
┌─────────────────────┐
│ SQL Server 2022     │
│ (Tabelas)           │
└─────────────────────┘
```

### Algoritmo de Detecção

Para cada tabela no SQL Server:

1. **Colunas Novas** (no modelo, não no banco)
   - ✅ Gera: `ALTER TABLE ... ADD COLUNA ...`
   - 📊 Tipo: Sempre VARCHAR(4000) por padrão
   - 📌 Nullable: SIM (para não quebrar dados existentes)

2. **Colunas Removidas** (no banco, não no modelo)
   - ⚠️ Gera: `-- ALTER TABLE ... DROP COLUNA ...` (COMENTADO)
   - 🛡️ Segurança: Não deleta automaticamente
   - 🔔 Requer revisão manual

3. **Tipos Diferentes**
   - 🔄 Gera: `ALTER TABLE ... ALTER COLUMN ...`
   - ✨ Ignore: COLLATE (SQL Server) = VARCHAR (Python)
   - 📊 Compatível: varchar(8000) ≈ VARCHAR(4000)

---

## 📁 Arquivos Envolvidos

| Arquivo | Função |
|---------|--------|
| `sincronizar_schema.py` | 📜 Script de sincronização (classe `SchemaSynchronizer`) |
| `migrate_tables.py` | 🏗️ Integração com migrate_tables |
| `models/models_generated.py` | 🧬 Modelos ORM gerados dinamicamente |
| `logs/schema_sync_*.sql` | 📄 Scripts SQL executados |
| `bases/sql_map.json` | 🗂️ Mapeamento de colunas |

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

### Timeout de Conexão
```python
# Em models_generated.py
create_engine(
    connection_string,
    echo=False,
    pool_pre_ping=True,  # ← Valida conexão antes de usar
    connect_args={
        'timeout': 30,
        'fast_failover': True
    }
)
```

---

## 🛡️ Segurança & Backup

### Antes de Sincronizar em Produção

1. **Backup de Segurança**
   ```sql
   BACKUP DATABASE [rpa_neocrm] 
   TO DISK = 'C:\backups\rpa_neocrm_20251029.bak';
   ```

2. **Modo Check-Only**
   ```bash
   python sincronizar_schema.py --check-only
   ```
   Revise saída antes de executar.

3. **Gerar SQL para Review**
   ```bash
   python sincronizar_schema.py --generate-sql
   ```
   Edite `logs/schema_sync_*.sql` antes de executar.

4. **Executar com Logging**
   ```bash
   python sincronizar_schema.py > schema_sync.log 2>&1
   ```

---

## 🚨 Tratamento de Erros

### Erro: "Tabela não existe"
```
❌ Tabela EXPORTACAO_PRODUCAO não existe no banco
```
**Solução:** Execute `python migrate_tables.py` para criar tabelas.

### Erro: "Cannot ALTER COLUMN com dados existentes"
```
❌ Error converting data type VARCHAR to...
```
**Solução:** 
- Crie nova coluna temporária
- Copie dados transformados
- Renomeie

### Erro: "PRIMARY KEY violation"
```
❌ Cannot add NOT NULL column without default...
```
**Solução:** Adicione `default=''` ou `nullable=True` ao modelo.

---

## 📊 Relatório de Sincronização

Após cada execução, o script gera relatório:

```
================================================================================
RELATÓRIO DE SINCRONIZAÇÃO DE SCHEMA
================================================================================

Data: 2025-10-29 17:38:58
Banco: 192.168.11.200,1434/rpa_neocrm

📊 Alterações detectadas: 1 tabela(s)

  📋 EXPORTACAO_STATUS:
     ➕ Colunas para adicionar: 1
        • USUARIO
     ❌ Colunas para remover: 2 (comentadas)
        • USUARIO_ENTRADA
        • USUARIO_SAIDA

⚠️  Avisos (1):
  • EXPORTACAO_STATUS: Colunas removidas detectadas (podem ser deletadas)

================================================================================
```

---

## 🔗 Integração com Workflow

### Workflow Completo: Excel → Modelos → Schema → Banco

```bash
# 1. Gerar sql_map do Excel
python gerar_sql_map_automatico.py

# 2. Gerar models do sql_map
python gerar_models_dinamicos.py

# 3. Sincronizar schema no banco
python migrate_tables.py

# 4. Executar app.py
python app.py
```

### Usando em CI/CD

```bash
#!/bin/bash
set -e

# Check
python sincronizar_schema.py --check-only

# Gerar SQL
python sincronizar_schema.py --generate-sql

# Review (manual step in CI)
# ... code review logs/schema_sync_*.sql ...

# Execute
python sincronizar_schema.py

echo "✅ Schema sincronizado com sucesso!"
```

---

## 💡 Boas Práticas

### ✅ Fazer

- Executar `--check-only` antes de produção
- Manter backups regulares
- Revisar scripts SQL em `logs/`
- Usar `--generate-sql` para documentação
- Rodar automaticamente no start do app

### ❌ Não Fazer

- Deletar colunas manualmente no SQL Server
- Modificar scripts gerados sem entender
- Sincronizar sem backup
- Executar em tabelas com 100M+ registros sem planejar

---

## 🐛 Debug & Verbose

### Modo Verbose
```bash
python sincronizar_schema.py --verbose
```

Mostra:
- SQL executado linha por linha
- Timestamps de cada operação
- Detalhes de conexão

### Logs Salvos
```
logs/
├── schema_sync_20251029_173858.sql  ← Scripts SQL
├── sent_records_*.jsonl              ← Registros enviados
└── envios_resumo.jsonl               ← Resumo de envios
```

---

## 📚 Referências

- **Documentação SQLAlchemy:** [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- **SQL Server ALTER TABLE:** [Microsoft Docs](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-table-transact-sql)
- **Copilot Instructions:** Ver `.github/copilot-instructions.md` seção "Sincronização de Schema"

---

## ❓ FAQ

**P: Posso sincronizar durante execução do app?**
R: Não recomendado. O app pode ter locks nas tabelas. Melhor executar antes/depois.

**P: E se a sincronização falhar no meio?**
R: Cada SQL é executado em transação. Se um falha, os anteriores já foram commitados.

**P: Preciso atualizar migrate_tables.py manualmente?**
R: Não. `sincronizar_schema.py` é auto-contido e chamado por `migrate_tables.py`.

**P: Como remover colunas do banco?**
R: Edite `models_generated.py` removendo a coluna. Sincronize. O script comentará o DROP.

**P: Funciona com dados em produção?**
R: Sim! Usa ALTER TABLE sem DELETE. Dados preservados.

---

**✨ Sistema completo de sincronização automática implementado com sucesso!**
