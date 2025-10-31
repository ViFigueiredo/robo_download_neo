# 📦 PASTA SCRIPTS - Empacotamento com Credenciais do .env

## Arquivos

```
scripts/
├── empacotar_robo_neo.bat .......... Script principal (EXECUTE ISTO!)
├── robo_neo.spec .................. Configuração PyInstaller
├── config_embutida.py ............. Carregador de .env ⭐ NOVO
├── wrapper_env.py ................. Gerenciador de .env (auxiliar)
├── GUIA_EMPACOTAMENTO.md .......... Documentação completa
├── CREDENCIAIS_EMBUTIDAS.md ....... Guia de credenciais
└── README.md ....................... Este arquivo
```

---

## 🚀 Usar em 3 Comandos

```bash
# 1. Entre na pasta scripts
cd scripts

# 2. Execute o empacotador
empacotar_robo_neo.bat

# 3. Resultado em: ../dist/robo_neo.exe
```

---

## ✨ O que é Novo?

### � Credenciais Embutidas no .exe

**ANTES:**
```
Usuário recebia:
  - robo_neo.exe
  - .env.template
Tinha que editar .env com suas credenciais
(Complexo, inseguro)
```

**DEPOIS:**
```
Usuário recebe:
  - robo_neo.exe (ÚNICO arquivo!)
Credenciais já estão embutidas
Pronto para usar - SEM CONFIGURAÇÃO!
```

---

## �📋 O que Cada Arquivo Faz

### `empacotar_robo_neo.bat` ⭐ PRINCIPAL

**O que é:** Script que automatiza empacotamento com credenciais

**Como usar:**
```batch
empacotar_robo_neo.bat
```

**O que faz:**
1. ✅ Verifica Python e PyInstaller
2. ✅ Verifica `config_embutida.py`
3. ✅ Limpa builds antigos
4. ✅ Compila com credenciais embutidas
5. ✅ Gera `.exe` pronto para usar

**Resultado:** `../dist/robo_neo.exe` (com credenciais)

---

### `config_embutida.py` ⭐ NOVO

**O que é:** Carregador de configuração que lê do `.env`

**Contém:**
```python
def get_embedded_config():
    # Tenta carregar .env de múltiplos locais:
    # 1. Diretório de execução
    # 2. Raiz do projeto
    # 3. Variáveis de ambiente existentes
```

**Como funciona:**
1. Procura por `.env` no diretório atual
2. Se não achar, procura na raiz do projeto
3. Se não achar, usa variáveis de ambiente existentes
4. Carrega tudo em `os.environ` antes de app.py executar

**Quando editar:** 
- ❌ Não edite este arquivo para mudanças de credenciais
- ✅ Edite apenas o `.env` (arquivo real)
- Este arquivo é automático!

**⚠️ Importante:** 
- Mantenha `.env` com suas credenciais reais
- Não compartilhe `.env`
- Distribua apenas `robo_neo.exe`

---

### `robo_neo.spec`

**O que é:** Configuração PyInstaller

**O que mudou:** Agora usa `config_embutida.py` como entry point

```python
# Carrega credenciais ANTES de app.py
a = Analysis(['scripts/config_embutida.py'], ...)
```

**Quando editar:** Se adicionar novos módulos Python

---

## 👤 Para o Usuário Final

**Recebe:**
```
robo_neo.exe (único arquivo!)
```

**Como usar:**
```batch
# Apenas clique ou execute:
robo_neo.exe

# PRONTO! Funciona automaticamente
# Não precisa:
#   - Instalar Python
#   - Editar arquivos
#   - Configurar nada
```

**Resultado:** Login automático → Download → Parse → Insert

---

## 🔐 Segurança

- ✅ Credenciais compiladas no bytecode
- ✅ Difícil de extrair
- ⚠️ Não é 100% seguro (bytecode pode ser descompilado)
- ✅ Mais seguro que texto puro em arquivos

**Boas práticas:**
- ✅ Distribua apenas `robo_neo.exe`
- ❌ NÃO compartilhe `.env` original
- ❌ NÃO compartilhe `config_embutida.py`
- ✅ Se credenciais mudarem, recompile

---

## 🔧 Atualizar Credenciais

Se suas credenciais mudarem:

```bash
# 1. Edite .env na raiz do projeto
# Atualize SYS_USERNAME, SYS_PASSWORD, DB_PASSWORD, etc.

# 2. Execute o empacotador (pega as credenciais do .env)
empacotar_robo_neo.bat

# 3. Novo .exe com credenciais atualizadas
# Distribua o novo robo_neo.exe
```

**Como funciona:**
- Cada vez que você roda `empacotar_robo_neo.bat`
- O `config_embutida.py` lê as credenciais do `.env`
- Cria novo `.exe` com credenciais carregadas
- Usuário final nunca vê ou toca em `.env`

---

## 📊 Fluxo Completo

```
empacotar_robo_neo.bat (execute)
        ↓
[Validações]
   - Python? ✓
   - config_embutida.py? ✓
        ↓
[Compilação]
   - Lê config_embutida.py
   - Carrega credenciais
   - Compila app.py
   - Embutir bases/
        ↓
../dist/robo_neo.exe ✅
   (com credenciais embutidas)
        ↓
Distribuir para usuário
        ↓
Usuário executa: robo_neo.exe
        ↓
FUNCIONA! (sem configurar)
```

---

## ✅ Pré-requisitos

```bash
# Python 3.10+
python --version

# Dependências instaladas
pip install -r ../requirements.txt

# PyInstaller (será instalado automaticamente)
```

---

## 📚 Documentação

| Arquivo | Propósito |
|---------|-----------|
| `CREDENCIAIS_EMBUTIDAS.md` | Guia de credenciais + segurança |
| `GUIA_EMPACOTAMENTO.md` | Guia original (ainda válido) |
| `README.md` (este) | Guia rápido da pasta |

---

## ❓ FAQ

**P: O usuário precisa editar .env?**
R: Não! Credenciais já estão embutidas no .exe

**P: Posso compartilhar `config_embutida.py`?**
R: Não! Isso expõe suas credenciais. Compartilhe apenas `robo_neo.exe`

**P: Como atualizar credenciais?**
R: Edite `config_embutida.py`, recompile com `empacotar_robo_neo.bat`

**P: O .exe é seguro?**
R: Tão seguro quanto bytecode Python (pode ser descompilado)

---

## 🎯 Resultado Final

| Aspecto | Antes | Depois |
|--------|-------|--------|
| Arquivos para distribuir | 3+ | 1 (.exe) |
| Configuração necessária | Sim (editar .env) | Não (pronto!) |
| Segurança credenciais | Texto puro | Compiladas |
| Facilidade de uso | Média | Máxima |

---

**Status:** ✅ Credenciais embutidas com sucesso  
**Última atualização:** 30 de outubro de 2025  
**Segurança:** 🔐 Compiladas no .exe
