@echo off
REM === Empacotamento do robo_neo ===

REM 0. Limpar a pasta dist se já existir
if exist dist (
    rmdir /S /Q dist
)

REM 1. Gerar o executável com PyInstaller
pyinstaller --onefile --name robo_neo app.py

REM 2. Copiar arquivos de configuração e drivers para a pasta dist
copy /Y .env dist\
copy /Y map.json dist\
if exist geckodriver.exe copy /Y geckodriver.exe dist\
if exist chromedriver.exe copy /Y chromedriver.exe dist\
if exist msedgedriver.exe copy /Y msedgedriver.exe dist\

REM 3. Mensagem final
cd dist
@echo =====================================
@echo Empacotamento concluído!
@echo Para rodar em produção, use apenas os arquivos desta pasta.
@echo =====================================
pause 