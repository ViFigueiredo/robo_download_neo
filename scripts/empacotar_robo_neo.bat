@echo off
REM ============================================================================
REM ROBO DOWNLOAD NEO - Empacotador (com CREDENCIAIS EMBUTIDAS)
REM ============================================================================
REM Cria um único arquivo .exe com TUDO embutido
REM - Python e todas dependências
REM - Arquivos de configuração
REM - CREDENCIAIS (usuário final não precisa fazer NADA!)
REM ============================================================================

setlocal enabledelayedexpansion

REM Obter caminhos absolutos
for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
set "SCRIPTS_DIR=%ROOT_DIR%\scripts"
set "SPEC_FILE=%SCRIPTS_DIR%\robo_neo.spec"

echo.
echo ============================================================================
echo ROBO DOWNLOAD NEO - Construindo Executavel com CREDENCIAIS DINAMICAS
echo ============================================================================
echo.
echo Diretorio raiz: %ROOT_DIR%
echo.

REM ============================================================================
REM 1. VERIFICAR PRE-REQUISITOS
REM ============================================================================

echo [1/5] Verificando pre-requisitos...

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.10+ de: https://www.python.org
    pause
    exit /b 1
)
echo   [OK] Python encontrado

REM Verificar PyInstaller
pip list | find "pyinstaller" >nul
if errorlevel 1 (
    echo   [INSTALANDO] PyInstaller...
    pip install pyinstaller --quiet
    if errorlevel 1 (
        echo ERRO ao instalar PyInstaller!
        pause
        exit /b 1
    )
)
echo   [OK] PyInstaller disponivel

REM Verificar estrutura do projeto
if not exist "%ROOT_DIR%\app.py" (
    echo ERRO: app.py nao encontrado em: %ROOT_DIR%\app.py
    pause
    exit /b 1
)
echo   [OK] app.py encontrado

if not exist "%SCRIPTS_DIR%\config_embutida.py" (
    echo ERRO: config_embutida.py nao encontrado em: %SCRIPTS_DIR%\config_embutida.py
    pause
    exit /b 1
)
echo   [OK] config_embutida.py encontrado

if not exist "%SPEC_FILE%" (
    echo ERRO: robo_neo.spec nao encontrado em: %SPEC_FILE%
    pause
    exit /b 1
)
echo   [OK] robo_neo.spec encontrado

echo   [OK] Estrutura do projeto validada

echo.
REM ============================================================================
REM 2. LIMPAR BUILDS ANTERIORES
REM ============================================================================

echo [2/5] Limpando builds anteriores...

if exist "%ROOT_DIR%\dist" (
    echo   [REMOVENDO] dist
    rmdir /S /Q "%ROOT_DIR%\dist" >nul 2>&1
)

if exist "%ROOT_DIR%\build" (
    echo   [REMOVENDO] build
    rmdir /S /Q "%ROOT_DIR%\build" >nul 2>&1
)

echo   [OK] Limpeza concluida

echo.
REM ============================================================================
REM 3. COMPILAR COM PYINSTALLER
REM ============================================================================

echo [3/5] Compilando executavel com credenciais dinamicas (lidas do .env)...
echo   (Este processo pode levar 1-2 minutos)
echo   (Credenciais serao LIDAS DO .env em tempo de execucao)
echo.

cd /d "%ROOT_DIR%"

echo   [...] PyInstaller processando...
echo   Especificacao: %SPEC_FILE%
echo   Destino: %ROOT_DIR%\dist
echo.

pyinstaller "%SPEC_FILE%" --distpath "%ROOT_DIR%\dist" --workpath "%ROOT_DIR%\build" -y

if not exist "%ROOT_DIR%\dist\robo_neo.exe" (
    echo.
    echo [ERRO] Compilacao falhou - robo_neo.exe nao foi criado
    echo.
    echo   Verifique:
    echo   - Todas as dependencias estao instaladas: pip install -r requirements.txt
    echo   - Nao ha erros de sintaxe em app.py ou scripts\config_embutida.py
    echo   - Python esta instalado e acessivel
    echo   - Arquivo spec encontrado: %SPEC_FILE%
    echo.
    pause
    exit /b 1
)

REM Verificar tamanho do arquivo
for %%A in ("%ROOT_DIR%\dist\robo_neo.exe") do set "EXE_SIZE=%%~zA"

echo   [OK] Executavel criado com SUCESSO!
echo   Tamanho: %EXE_SIZE% bytes

echo.
REM ============================================================================
REM 4. EMBUTIR CONFIGURACAO
REM ============================================================================

echo [4/5] Incluindo arquivos complementares...

if not exist "%ROOT_DIR%\dist\logs" (
    mkdir "%ROOT_DIR%\dist\logs"
    echo   [OK] Pasta logs criada
)

if not exist "%ROOT_DIR%\dist\downloads" (
    mkdir "%ROOT_DIR%\dist\downloads"
    echo   [OK] Pasta downloads criada
)

REM Criar arquivo README de instruções
(
echo ROBO DOWNLOAD NEO - PRONTO PARA USAR
echo ====================================
echo.
echo Arquivo: robo_neo.exe
echo Status: Pronto com CREDENCIAIS DINAMICAS do .env
echo.
echo COMO USAR:
echo   1. Coloque o arquivo robo_neo.exe no local desejado
echo   2. Coloque o arquivo .env no MESMO diretorio (com as credenciais reais)
echo   3. Clique no arquivo robo_neo.exe para iniciar
echo   4. O sistema vai carregar as credenciais do .env automaticamente
echo.
echo IMPORTANTE:
echo   - O arquivo .env DEVE estar no mesmo diretorio do .exe
echo   - Credenciais sao lidas do .env em tempo de execucao (nao hardcoded)
echo   - Se .env nao for encontrado, o sistema tenta usar variaveis de ambiente
echo.
echo Nao precisa:
echo   - Instalar Python
echo   - Editar codigo-fonte
echo   - Recompilar
echo.
echo Logs serao salvos em: ./logs/
echo Arquivos baixados em: ./downloads/
echo.
) > "%ROOT_DIR%\dist\LEIA_ME.txt"

echo   [OK] Arquivo LEIA_ME.txt criado

echo.
REM ============================================================================
REM 5. GERAR RESUMO
REM ============================================================================

echo [5/5] Finalizando...

echo   [OK] Empacotamento concluido!

echo.
echo ============================================================================
echo ✅ SUCESSO! Seu executavel esta PRONTO PARA USAR
echo ============================================================================
echo.
echo Arquivo criado: %ROOT_DIR%\dist\robo_neo.exe (Tamanho: %EXE_SIZE% bytes)
echo.
echo SISTEMA DE CREDENCIAIS: DINAMICO (lido do .env)
echo.
echo COMO USAR:
echo   1. Coloque o arquivo .env no mesmo diretorio do robo_neo.exe
echo   2. Edite .env com as credenciais REAIS do seu sistema
echo   3. Clique em robo_neo.exe para iniciar
echo   4. O sistema carrega automaticamente as credenciais do .env
echo.
echo ARQUIVOS NECESSARIOS:
echo   - robo_neo.exe ...................... Aplicacao principal (executavel)
echo   - .env .............................. Arquivo de credenciais (coloque aqui!)
echo   - logs\ ............................ Pasta de logs (criada automaticamente)
echo   - downloads\ ....................... Pasta de downloads (criada automaticamente)
echo.
echo DOCUMENTACAO DISPONIVEL:
echo   - docs\00_COMECE_AQUI.md ........... Guia rapido
echo   - docs\INTEGRACAO_CONFIG_DINAMICA.md . Como funciona o carregamento de env
echo.
echo ============================================================================
echo.

REM Abrir pasta dist
start explorer "%ROOT_DIR%\dist"

echo [INFO] Pasta dist aberta. Arquivo robo_neo.exe esta pronto para usar!
echo.

pause 