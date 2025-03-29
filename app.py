import requests, time, os, shutil, schedule
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Acessando as variáveis
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")


def iniciar_driver():
    print("Iniciando driver do navegador...")
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    return driver

def acessar_pagina(driver, url):
    driver.get(url)
    print(f"Acessando {url}")

def esperar_elemento(driver, xpath, tempo=300):
    # print("Elemento em espera...")
    return WebDriverWait(driver, tempo).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )

def inserir_texto(driver, xpath, texto):
    # print("Inserindo texto...")
    esperar_elemento(driver, xpath)
    elemento = driver.find_element(By.XPATH, xpath)
    elemento.click()
    elemento.clear()
    elemento.send_keys(texto)

def clicar_elemento(driver, xpath):
    # print(f"Clicando no elemento...")
    driver.find_element(By.XPATH, xpath).click()

def gerar_otp():
    print("Gerando OTP...")
    response = requests.post(
        'http://localhost:8000/generate_otp', 
        json={"secret": "GZRDMZTGMFSWILLDGMZTALJUGQ2DQLJYGQYWMLJQGA4GCMZWGBRWGMZUMQ======"}
    )
    if response.status_code == 200:
        return response.json().get("otp")
    else:
        print(f"Erro ao gerar OTP: {response.status_code} - {response.text}")
        exit(1)

def selecionar_data(driver, xpath, data):
    print("Computando datas...")
    elemento = esperar_elemento(driver, xpath)
    elemento.clear()
    elemento.click()
    elemento.send_keys(data)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)

def selecionar_texto(driver, xpath, text):
    # print("Selecionando textos...")
    elemento = esperar_elemento(driver, xpath)
    elemento.click()
    elemento.clear()
    elemento.send_keys(text)
    time.sleep(5)
    driver.find_element(By.XPATH, xpath).send_keys(Keys.ENTER)

def realizar_download_atividades(driver, button_xpath):
    print("Realizando download de atividades...")
    clicar_elemento(driver, button_xpath)
    esperar_elemento(driver, '//*[contains(@id, "input-vaadin-number-field-")]')
    
    xpath_codigo = '//vaadin-vertical-layout//div/span/b[not(contains(text(), "EXPORTAR")) and normalize-space()]'
    codigo_elemento = esperar_elemento(driver, xpath_codigo)
    codigo_texto = codigo_elemento.text
    
    inserir_texto(driver, "//vaadin-number-field//input[contains(@id, 'input-vaadin-number-field-')]", int(codigo_texto))
    clicar_elemento(driver, "//vaadin-button[text()='Sim, Tenho certeza']")
    esperar_elemento(driver, "//vaadin-dialog-overlay[@id='overlay']//a[@href]")
    time.sleep(10)
    clicar_elemento(driver, "//vaadin-vertical-layout//a[contains(@title, 'Baixar arquivo processado')]")
    clicar_elemento(driver, "//vaadin-button[text()='Fechar']")
    fechar_modal(driver)
    print("Atividades baixadas com sucesso sucesso.")

def realizar_download_producao(driver):
    print("Realizando download de produção...")
    esperar_elemento(driver, "//vaadin-dialog-overlay[@id='overlay']//a[@href]", 300)
    time.sleep(10)
    clicar_elemento(driver, "//vaadin-vertical-layout//a[contains(@title, 'Baixar arquivo processado')]")
    clicar_elemento(driver, "/html/body/vaadin-dialog-overlay/vaadin-vertical-layout/vaadin-button")
    print("Produção baixado com sucesso.")

def fechar_modal(driver):
    # print("Fechando modal...")
    try:
        overlay = driver.find_element(By.XPATH, "//vaadin-dialog-overlay[contains(@id, 'overlay')]")
        if overlay.is_displayed():
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, "//vaadin-dialog-overlay[contains(@id, 'overlay')]")))
            # print("Modal fechado.")
    except Exception:
        print("Nenhum modal aberto.")

def exportAtividadesStatus(driver):
    print("Exportando atividades<>status...")
    esperar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    data_inicial = f"01/{mes_atual}/{ano_atual}"
    
    selecionar_data(driver, '//*[@id="input-vaadin-date-picker-158"]', data_inicial)
    clicar_elemento(driver, '//*[@id="btnPesquisar"]')
    realizar_download_atividades(driver, '//*[contains(@id, "btnExportarStatus")]')

def exportAtividades(driver):
    print("Exportando atividades...")
    esperar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    data_inicial = f"01/{mes_atual}/{ano_atual}"
    
    selecionar_data(driver, '//*[@id="input-vaadin-date-picker-158"]', data_inicial)
    clicar_elemento(driver, '//*[@id="btnPesquisar"]')
    realizar_download_atividades(driver, '//*[contains(@id, "btnExportarAtividades")]')

def exportProducao(driver):
    print("Exportando produção...")
    esperar_elemento(driver, '//*[contains(@id, "Painel_Produção")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Produção")]')

    data_inicial = (datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y")
    texto = "Painel de Produção Vivo"   

    selecionar_data(driver, '//*[@id="input-vaadin-date-picker-53"]', data_inicial)
    selecionar_texto(driver, '//*[@id="input-vaadin-combo-box-56"]', texto)
    clicar_elemento(driver, '//*[@id="input-vaadin-radio-button-71"]')
    clicar_elemento(driver, "//vaadin-button[contains(text(), 'Pesquisar') and @role='button']")
    realizar_download_producao(driver)
    fechar_modal(driver)

def login(driver):
    acessar_pagina(driver, url)
    print("Realizando login...")
    esperar_elemento(driver, '//*[contains(@id, "input-vaadin-text-field-")]')
    
    inserir_texto(driver, '//*[contains(@id, "input-vaadin-text-field-")]', username)
    inserir_texto(driver, '//*[contains(@id, "input-vaadin-password-field-")]', password)
    
    while True:
        otp = gerar_otp()
        clicar_elemento(driver, '//*[contains(@id, "input-vaadin-radio-button-")]')
        clicar_elemento(driver, '//*[@id="input-vaadin-text-field-19"]')
        inserir_texto(driver, '//*[@id="input-vaadin-text-field-19"]', otp)
        clicar_elemento(driver, '//*[contains(@id, "btnLogar")]')
        
        time.sleep(2) 
        
        try:
            mensagem = driver.find_element(By.XPATH, '/html/body/div[1]/flow-container-root-2521314/vaadin-vertical-layout/vaadin-vertical-layout/vaadin-vertical-layout/div/span/center').text
            
            if mensagem in ["Usuário não encontrado", "Código autenticador inválido", "Usuário inexistente ou senha inválida"]:
                print("Erro detectado, tentando novamente...")
                continue
        except:
            break
    
    print("Login realizado com sucesso!")

def logout(driver):
    print("Realizando logout...")
    btn_logout_xpath = "/html/body/div[1]/flow-container-root-2521314/vaadin-app-layout/vaadin-horizontal-layout/footer/vaadin-menu-bar/vaadin-menu-bar-button[1]"
    option_logout_xpath = "/html/body/vaadin-menu-bar-overlay/vaadin-menu-bar-list-box/vaadin-menu-bar-item[4]"
    esperar_elemento(driver, btn_logout_xpath)
    clicar_elemento(driver, btn_logout_xpath)
    esperar_elemento(driver, option_logout_xpath)
    clicar_elemento(driver, option_logout_xpath)

def renomear_arquivos(arquivos, diretorio_origem):
    print("Renomeando arquivos...")
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivos_renomeados = {}
    
    for arquivo in arquivos:
        caminho_original = os.path.join(diretorio_origem, arquivo)
        if os.path.exists(caminho_original):
            nome, ext = os.path.splitext(arquivo)
            novo_nome = f"{nome}_{data_atual}{ext}"
            novo_caminho = os.path.join(diretorio_origem, novo_nome)
            os.rename(caminho_original, novo_caminho)
            arquivos_renomeados[arquivo] = novo_nome
        else:
            print(f"Arquivo não encontrado: {arquivo}")
    
    return arquivos_renomeados

def mover_arquivos(diretorio_origem, arquivos, diretorio_destino, subdiretorio):
    print("Movendo arquivos de histórico...")
    
    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)
    
    caminho_subdiretorio = os.path.join(diretorio_destino, subdiretorio)
    if not os.path.exists(caminho_subdiretorio):
        os.makedirs(caminho_subdiretorio)
    
    arquivos_renomeados = renomear_arquivos(arquivos, diretorio_origem)
    
    for arquivo, novo_nome in arquivos_renomeados.items():
        caminho_origem = os.path.join(diretorio_origem, novo_nome)
        caminho_destino = os.path.join(diretorio_destino, novo_nome)
        caminho_subdestino = os.path.join(caminho_subdiretorio, novo_nome)
        
        if not os.path.exists(caminho_origem):
            print(f"Arquivo {novo_nome} não encontrado na origem. Verificando no destino...")
            if os.path.exists(caminho_destino):
                print(f"Arquivo {novo_nome} já existe no destino. Não será movido para o subdiretório.")
            continue
        
        if os.path.exists(caminho_destino):
            nome, ext = os.path.splitext(novo_nome)
            novo_nome_sub = f"{nome}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            caminho_subdestino = os.path.join(caminho_subdiretorio, novo_nome_sub)
            print(f"Arquivo {novo_nome} já existe no destino. Renomeando e movendo para o subdiretório...")
            os.rename(caminho_destino, caminho_subdestino)
        
        shutil.move(caminho_origem, caminho_destino)

def executar_rotina():
    try:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Iniciando em {data_atual}")

        driver = iniciar_driver()
        login(driver)
        exportAtividadesStatus(driver)
        logout(driver)
        time.sleep(5)
        driver.quit()
        time.sleep(10)

        driver = iniciar_driver()
        login(driver)
        exportAtividades(driver)
        logout(driver)
        time.sleep(5)
        driver.quit()
        time.sleep(10)

        driver = iniciar_driver()
        login(driver)
        exportProducao(driver)
        logout(driver)
        time.sleep(5)
        driver.quit()
        time.sleep(10)

        sysUser = os.getenv("USERNAME")
        dirOrigem = f"C:/Users/{sysUser}/Downloads"
        dirDestino = "N:"
        subDiretorio = "histórico"
        nomeArquivo1 = "Exportacao Atividade.xlsx"
        nomeArquivo2 = "Exportacao Status.xlsx"
        nomeArquivo3 = "ExportacaoProducao.xlsx"

        mover_arquivos(dirOrigem, [nomeArquivo1, nomeArquivo2, nomeArquivo3], dirDestino, subDiretorio)

        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Finalizado em {data_atual}")

    except Exception as e:
        print(e) # Registra o erro no log

# Agendar a função para rodar a cada 30 minutos dentro do intervalo
print("Aguardando a próxima execução...")
schedule.every(30).minutes.do(executar_rotina)
# executar_rotina()


while True:
    agora = datetime.now().hour
    if 8 <= agora < 22:
        schedule.run_pending()  # Executa as tarefas agendadas
    time.sleep(30)  # Aguarda 30 segundos antes de verificar novamente
