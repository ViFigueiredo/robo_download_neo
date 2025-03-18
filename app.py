from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests, time, os, shutil

# Carrega as variáveis do arquivo .env
load_dotenv()

# Acessando as variáveis
url = os.getenv("URL")
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

def iniciar_driver():
    """Inicializa o WebDriver do Firefox."""
    return webdriver.Firefox()

def acessar_pagina(driver, url):
    """Acessa a URL especificada."""
    driver.get(url)

def esperar_elemento(driver, xpath, tempo=10):
    """Aguarda um elemento estar presente na página."""
    return WebDriverWait(driver, tempo).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )

def inserir_texto(driver, xpath, texto):
    """Insere um texto em um campo de input identificado pelo XPath."""
    esperar_elemento(driver, xpath)
    elemento = driver.find_element(By.XPATH, xpath)
    elemento.click()
    elemento.clear()
    elemento.send_keys(texto)

def clicar_elemento(driver, xpath):
    """Clica em um elemento identificado pelo XPath."""
    driver.find_element(By.XPATH, xpath).click()

def gerar_otp():
    """Gera um código OTP via requisição para API."""
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
    """Define uma data em um campo de input date-picker."""
    elemento = esperar_elemento(driver, xpath)
    elemento.clear()
    elemento.click()
    elemento.send_keys(data)
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)

def selecionar_texto(driver, xpath, text):
    """Insere um valor de texto em um campo de input."""
    elemento = esperar_elemento(driver, xpath)
    elemento.click()
    elemento.clear()
    elemento.send_keys(text)
    time.sleep(5)
    # driver.find_element(By.XPATH, xpath).send_keys(Keys.RETURN)
    driver.find_element(By.XPATH, xpath).send_keys(Keys.ENTER)

def realizar_download_atividades(driver, button_xpath):
    """Realiza o download de um arquivo após confirmação de código OTP."""
    clicar_elemento(driver, button_xpath)
    esperar_elemento(driver, '//*[contains(@id, "input-vaadin-number-field-")]')
    
    # Obter código de verificação
    xpath_codigo = '//vaadin-vertical-layout//div/span/b[not(contains(text(), "EXPORTAR")) and normalize-space()]'
    codigo_elemento = esperar_elemento(driver, xpath_codigo)
    codigo_texto = codigo_elemento.text
    
    inserir_texto(driver, "//vaadin-number-field//input[contains(@id, 'input-vaadin-number-field-')]", int(codigo_texto))
    clicar_elemento(driver, "//vaadin-button[text()='Sim, Tenho certeza']")
    esperar_elemento(driver, "//vaadin-dialog-overlay[@id='overlay']//a[@href]")
    clicar_elemento(driver, "//vaadin-vertical-layout//a[contains(@title, 'Baixar arquivo processado')]")
    clicar_elemento(driver, "//vaadin-button[text()='Fechar']")
    fechar_modal(driver)

def realizar_download_producao(driver):
    """Realiza o download de um arquivo."""    
    esperar_elemento(driver, "//vaadin-dialog-overlay[@id='overlay']//a[@href]", 300)
    clicar_elemento(driver, "//vaadin-vertical-layout//a[contains(@title, 'Baixar arquivo processado')]")
    clicar_elemento(driver, "/html/body/vaadin-dialog-overlay/vaadin-vertical-layout/vaadin-button")

def fechar_modal(driver):
    """Fecha o modal se estiver presente"""
    try:
        overlay = driver.find_element(By.XPATH, "//vaadin-dialog-overlay[contains(@id, 'overlay')]")
        if overlay.is_displayed():
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)  # Pressiona ESC
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, "//vaadin-dialog-overlay[contains(@id, 'overlay')]")))
            print("Modal fechado.")
    except Exception:
        print("Nenhum modal aberto.")

""" Painel de Atividades > Exportar Status"""
def exportAtividadesStatus(driver):
    esperar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    data_inicial = f"01/{mes_atual}/{ano_atual}"
    
    selecionar_data(driver, '//*[contains(@id, "input-vaadin-date-picker-160")]', data_inicial)
    clicar_elemento(driver, '//*[contains(@id, "btnPesquisar")]')
    realizar_download_atividades(driver, '//*[contains(@id, "btnExportarStatus")]')

""" Painel de Atividades > Exportar Atividades"""
def exportAtividades(driver):
    esperar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Atividades")]')
    
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    data_inicial = f"01/{mes_atual}/{ano_atual}"
    
    selecionar_data(driver, '//*[contains(@id, "input-vaadin-date-picker-160")]', data_inicial)
    clicar_elemento(driver, '//*[contains(@id, "btnPesquisar")]')
    realizar_download_atividades(driver, '//*[contains(@id, "btnExportarAtividades")]')

def exportProducao(driver):
    """ Painel de Produção """
    esperar_elemento(driver, '//*[contains(@id, "Painel_Produção")]')
    clicar_elemento(driver, '//*[contains(@id, "Painel_Produção")]')

    data_inicial = (datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y")
    texto = "Painel de Produção Vivo"   

    selecionar_data(driver, '//*[contains(@id, "input-vaadin-date-picker-55")]', data_inicial)
    selecionar_texto(driver, '//*[contains(@id, "input-vaadin-combo-box-58")]', texto)
    clicar_elemento(driver, '//*[contains(@id, "input-vaadin-radio-button-73")]')
    clicar_elemento(driver, "//vaadin-button[contains(text(), 'Pesquisar') and @role='button']")
    realizar_download_producao(driver)
    fechar_modal(driver)

def login(driver):
    acessar_pagina(driver, url)
    esperar_elemento(driver, '//*[contains(@id, "input-vaadin-text-field-")]')
    
    inserir_texto(driver, '//*[contains(@id, "input-vaadin-text-field-")]', username)
    inserir_texto(driver, '//*[contains(@id, "input-vaadin-password-field-")]', password)
    
    while True:
        otp = gerar_otp()
        clicar_elemento(driver, '//*[contains(@id, "input-vaadin-radio-button-")]')
        inserir_texto(driver, '//vaadin-text-field//input[contains(@id, "input-vaadin-text-field-21")]', otp)
        clicar_elemento(driver, '//*[contains(@id, "btnLogar")]')
        
        # Aguarda um curto período para a mensagem de erro aparecer (se houver)
        time.sleep(2) 
        
        # Verifica se a mensagem de erro está presente
        try:
            mensagem = driver.find_element(By.XPATH, '/html/body/div[1]/flow-container-root-2521314/vaadin-vertical-layout/vaadin-vertical-layout/vaadin-vertical-layout/div/span/center').text
            
            if mensagem in ["Usuário não encontrado", "Código autenticador inválido", "Usuário inexistente ou senha inválida"]:
                print("Erro detectado, tentando novamente...")
                continue  # Repete o processo de OTP
        except:
            break  # Sai do loop se a mensagem de erro não for encontrada
    
    print("Login realizado com sucesso!")


def logout(driver):
    btn_logout_xpath = "/html/body/div[1]/flow-container-root-2521314/vaadin-app-layout/vaadin-horizontal-layout/footer/vaadin-menu-bar/vaadin-menu-bar-button[1]"
    option_logout_xpath = "/html/body/vaadin-menu-bar-overlay/vaadin-menu-bar-list-box/vaadin-menu-bar-item[4]"
    esperar_elemento(driver, btn_logout_xpath)
    clicar_elemento(driver, btn_logout_xpath)
    esperar_elemento(driver, option_logout_xpath)
    clicar_elemento(driver, option_logout_xpath)

def renomear_arquivos(arquivos, diretorio_origem):
    data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivos_renomeados = {}
    
    for arquivo in arquivos:
        caminho_original = os.path.join(diretorio_origem, arquivo)
        if os.path.exists(caminho_original):
            nome, ext = os.path.splitext(arquivo)
            novo_nome = f"{nome}_{data_atual}{ext}"
            arquivos_renomeados[arquivo] = novo_nome
        else:
            print(f"Arquivo não encontrado: {arquivo}")
    
    return arquivos_renomeados

def mover_arquivos(diretorio_origem, arquivos, diretorio_destino, subdiretorio):
    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)
    
    caminho_subdiretorio = os.path.join(diretorio_destino, subdiretorio)
    if not os.path.exists(caminho_subdiretorio):
        os.makedirs(caminho_subdiretorio)
    
    # Mover arquivos existentes na raiz do diretório de destino para o subdiretório
    for item in os.listdir(diretorio_destino):
        caminho_item = os.path.join(diretorio_destino, item)
        if os.path.isfile(caminho_item):
            shutil.move(caminho_item, os.path.join(caminho_subdiretorio, item))
    
    # Renomear e mover os novos arquivos para o diretório de destino
    arquivos_renomeados = renomear_arquivos(arquivos, diretorio_origem)
    for original, novo_nome in arquivos_renomeados.items():
        caminho_origem = os.path.join(diretorio_origem, original)
        caminho_destino = os.path.join(diretorio_destino, novo_nome)
        if os.path.exists(caminho_origem):
            shutil.move(caminho_origem, caminho_destino)
        else:
            print(f"Arquivo não encontrado para mover: {original}")

# Execução principal
driver = iniciar_driver()
try:
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Iniciando download de arquivos em {data_atual}")

    login(driver)
    exportAtividadesStatus(driver)
    logout(driver)
    driver.refresh()
    time.sleep(5)
    
    login(driver)
    exportAtividades(driver)
    logout(driver)
    driver.refresh()
    time.sleep(5)
    
    login(driver)
    exportProducao(driver)
    logout(driver)
    time.sleep(5)

    dirOrigem = "C:/Users/Dev/Downloads"
    dirDestino = "C:/Users/Dev/Downloads/baixados"
    subDiretorio = "movidos"
    nomeArquivo1 = "Exportacao Atividade.xlsx"
    nomeArquivo2 = "Exportacao Status.xlsx"
    nomeArquivo3 = "ExportacaoProducao.xlsx"

    mover_arquivos(dirOrigem, [nomeArquivo1, nomeArquivo2, nomeArquivo3], dirDestino, subDiretorio)
finally:
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Finalizado em {data_atual}")
    driver.quit()
    # time.sleep(1800)
