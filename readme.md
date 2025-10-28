# 🤖 ROBO DOWNLOAD NEO

**Sistema de automação web para download e processamento de relatórios com integração SQL Server**

---

## 📚 Documentação

Toda a documentação está em **`/docs`**. Comece por aqui:

### 🚀 Instalação & Setup
- **[docs/INSTALACAO_E_DEPLOY.md](./docs/INSTALACAO_E_DEPLOY.md)** - Guia passo-a-passo (Fases 1-6)
- **[.env.example](./.env.example)** - Template de configuração

### 🏗️ Técnico & Desenvolvimento
- **[docs/ARQUITETURA_E_API.md](./docs/ARQUITETURA_E_API.md)** - Arquitetura & fluxo de dados
- **[.github/copilot-instructions.md](./.github/copilot-instructions.md)** - Padrões de código & convenções

### 🐛 Troubleshooting & Debugging
- **[docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** - 13+ erros comuns com soluções
- **[docs/TRATAMENTO_DUPLICATAS.md](./docs/TRATAMENTO_DUPLICATAS.md)** - Guia de duplicatas (Fase 6)

### � Navegação
- **[docs/INDICE_DOCUMENTACAO.md](./docs/INDICE_DOCUMENTACAO.md)** - Mapa de navegação completo

---

## � Estrutura do Projeto

```
robo_download_neo/
├── README.md                          ← Você está aqui!
├── .env.example                       ← Template de configuração
├── app.py                             ← Aplicação principal
├── requirements.txt                   ← Dependências Python
├── .env                               ← Configuração (não versionado)
├── .github/
│   └── copilot-instructions.md       ← Instruções para IA/Devs
├── bases/                             ← Configuração JSON (OBRIGATÓRIO)
│   ├── map_relative.json             ← XPaths Selenium
│   ├── nocodb_map.json               ← Mapeamento Excel
│   └── sql_map.json                  ← Mapeamento SQL
├── downloads/                         ← Excel baixados
├── logs/                              ← Logs estruturados
├── tests/                             ← Suite de testes
└── docs/                              ← 📁 DOCUMENTAÇÃO ESSENCIAL
    ├── ARQUITETURA_E_API.md          ← Arquitetura & fluxo
    ├── INSTALACAO_E_DEPLOY.md        ← Setup passo-a-passo
    ├── TROUBLESHOOTING.md            ← Erros & soluções
    ├── TRATAMENTO_DUPLICATAS.md      ← Guia de duplicatas
    └── INDICE_DOCUMENTACAO.md        ← Mapa de navegação
```

---

## ⚡ Quick Start

### 1️⃣ Setup Rápido
```bash
# Copiar template
copy .env.example .env

# Editar variáveis
code .env

# Criar pastas
mkdir bases downloads logs

# Instalar dependências
pip install -r requirements.txt

# Teste seguro
set DRY_RUN=true
python app.py
```

### 2️⃣ Migrar JSONs para \bases\
```bash
mkdir bases
move map_relative.json bases/
move nocodb_map.json bases/
move sql_map.json bases/
```

### 3️⃣ Deploy
```bash
set DRY_RUN=false
python app.py
```

---

## 📖 Documentação por Tipo

### Para Iniciantes
1. [docs/INSTALACAO_E_DEPLOY.md](./docs/INSTALACAO_E_DEPLOY.md) - Setup passo-a-passo
2. [docs/INDICE_DOCUMENTACAO.md](./docs/INDICE_DOCUMENTACAO.md) - Mapa de navegação

### Para Developers
1. [.github/copilot-instructions.md](./.github/copilot-instructions.md) - Padrões de código & **Rotina de atualização de docs**
2. [docs/ARQUITETURA_E_API.md](./docs/ARQUITETURA_E_API.md) - Fluxo de dados

### Para Troubleshooting
1. [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) - Erros e soluções (inclui duplicatas)

---

## 📚 Filosofia de Documentação

**Nossa abordagem:** Documentação **centrada** e **manutenível**
- ✅ **5 arquivos essenciais** em `/docs` (nunca mudam)
- ✅ **NÃO criamos novo `.md`** para cada mudança
- ✅ **ATUALIZAMOS docs existentes** conforme código muda
- ✅ **Mapeamento explícito:** Código → Doc (veja seção "📚 Rotina de Atualização" em [.github/copilot-instructions.md](./.github/copilot-instructions.md))

**Resultado:** Documentação organizada, sem dispersão, escalável

---

## 🎯 Principais Mudanças (Fases 1-6)

### 📌 Fase 4: \bases\ Folder (Obrigatório!)
```
JSONs DEVEM estar em \bases\
├─ map_relative.json
├─ nocodb_map.json
└─ sql_map.json
```

### 📌 Fase 5: Enhanced Logging
```
Taxa de sucesso em %
Emojis: ✅ ❌ ⚠️ 📊
Contadores: success, duplicate, error
```

### 📌 Fase 6: Tratamento de Duplicatas
```
❌ ANTES: 1 duplicata → batch falha (0/25)
✅ DEPOIS: 1 duplicata → batch continua (24/25)

Ver: docs/TRATAMENTO_DUPLICATAS.md
```

---

---

## � Próximas Ações

**Você é novo?**
→ Leia [docs/INSTALACAO_E_DEPLOY.md](./docs/INSTALACAO_E_DEPLOY.md)

**Quer entender a arquitetura?**
→ Veja [docs/ARQUITETURA_E_API.md](./docs/ARQUITETURA_E_API.md)

**Tem erro?**
→ Consulte [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)

**Quer desenvolver?**
→ Leia [.github/copilot-instructions.md](./.github/copilot-instructions.md)

---

## 📋 Status

- ✅ Documentação: 5 arquivos essenciais em `/docs`
- ✅ Código: Pronto para produção (Fases 1-6)
- ✅ Testes: Suite completa em `/tests`
- ✅ Estrutura: Organizada e manutenível

---

## 📄 Informações do Projeto

**Autor:** ViFigueiredo  
**Branch:** sql_server  
**Última atualização:** 28 de outubro de 2025  
**Versão:** 1.0
