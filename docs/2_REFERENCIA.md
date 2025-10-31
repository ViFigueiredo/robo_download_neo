# 📖 GUIA DE REFERÊNCIA RÁPIDA

## 🔍 Encontre o que você quer

### ▶️ Executar aplicação
```bash
python app.py
```
**Faz:** Login → Download → Parse → Insert (60.815+ registros)

---

### ▶️ Criar tabelas do zero
```bash
python migrate_tables.py
```
**Faz:** Cria 3 tabelas no SQL Server

---

### ▶️ Verificar tabelas
```bash
python migrate_tables.py --status
```
**Output:**
```
✅ EXPORTACAO_PRODUCAO - 0 registros, 53 colunas
✅ EXPORTACAO_ATIVIDADE - 0 registros, 25 colunas
✅ EXPORTACAO_STATUS - 0 registros, 13 colunas
```

---

### ▶️ Limpar tabelas (CUIDADO!)
```bash
python migrate_tables.py --drop
```
**Faz:** Deleta todas as 3 tabelas (pergunta confirmação)

---

### ▶️ Regenerar modelos ORM
```bash
python gerar_models_dinamicos.py
```
**Faz:** Lê `sql_map.json` → Cria `models_generated.py`

---

### ▶️ Testar parsing (sem insert)
```bash
python tests/test_parse_producao.py --file downloads/ExportacaoProducao.xlsx
```
**Output:** JSON com dados parseados

---

### ▶️ Testar insert (sem efeitos)
```bash
python tests/test_post_producao.py --dry-run
```
**Output:** Simula insert, sem enviar ao banco

---

## 🐛 Problemas Comuns

### ❓ Problema: SAWarning ao executar
**Causa:** Modelos ORM com constraints incorretos  
**Solução:**
```bash
python gerar_models_dinamicos.py
python migrate_tables.py --drop
python migrate_tables.py
```

---

### ❓ Problema: "NameError: Integer not defined"
**Causa:** Import faltando em `models_generated.py`  
**Solução:** Verificar que `Integer` está em:
```python
from sqlalchemy import Column, String, DateTime, Integer
```

---

### ❓ Problema: Conexão SQL Server falha
**Causa:** Credenciais ou endereço incorreto  
**Verificar .env:**
```ini
DB_SERVER=192.168.11.200:1434
DB_DATABASE=rpa_neocrm
DB_USERNAME=sa
DB_PASSWORD=SUA_SENHA
```

---

### ❓ Problema: Browser não faz login
**Causa:** Credenciais ou 2FA incorreto  
**Verificar .env:**
```ini
SYS_USERNAME=seu_usuario
SYS_PASSWORD=sua_senha
SYS_SECRET_OTP=seu_token
```

---

### ❓ Problema: Download não funciona
**Causa:** Elemento web mudou (Vaadin UI)  
**Solução:**
1. Abra navegador manualmente
2. Veja qual XPath está errado
3. Atualize em `map_relative.json`
4. Execute novamente

---

### ❓ Problema: "Duplicate entry" ao inserir
**Esperado!** Não há constraint UNIQUE  
**Comportamento:** Insere duplicatas, sem erro

---

## 📊 Arquivos Importantes

| Arquivo | Propósito | Editar? |
|---------|-----------|---------|
| `app.py` | Lógica principal | ⚠️ Com cuidado |
| `models_generated.py` | ORM models | ❌ Auto-gerado |
| `gerar_models_dinamicos.py` | Gera models | ⚠️ Com cuidado |
| `migrate_tables.py` | Criar tabelas | ✅ Safe |
| `sql_map.json` | Definição de colunas | ✅ Editar aqui |
| `.env` | Configurações | ✅ Essencial |

---

## 🗂️ Estrutura de Pastas

```
robo_download_neo/
├── app.py ⭐
├── .env (criar com suas credenciais)
│
├── models/ (ORM)
│   ├── models_generated.py (auto-gerado)
│   └── models.py (fallback)
│
├── downloads/ (arquivos Excel baixados)
├── logs/ (tudo que acontece)
├── tests/ (testes)
│
├── docs/ (você está aqui)
│   ├── README.md
│   ├── 1_INICIO.md
│   ├── 2_REFERENCIA.md (este arquivo)
│   └── 3_DETALHES.md
│
└── bases/
    ├── map_relative.json (XPaths)
    └── sql_map.json (mapeamento colunas e tabelas)
```

---

## ⚡ Dica Rápida (TL;DR)

**Quer executar?**
```bash
python app.py
```

**Quer verificar banco?**
```bash
python migrate_tables.py --status
```

**Quer limpar e recomeçar?**
```bash
python migrate_tables.py --drop
python migrate_tables.py
python app.py
```

**Quer entender tudo?**
→ Leia `3_DETALHES.md`

---

**Última atualização:** 30 de outubro de 2025  
**Status:** 🟢 ATUALIZADO
