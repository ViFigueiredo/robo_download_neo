import requests, time, os, shutil, schedule, json, re
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains

# Carrega as variáveis do arquivo .env
load_dotenv()

# Carrega os XPaths do arquivo map.json
with open('map.json', 'r') as f:
    XPATHS = json.load(f)

# Acessando as variáveis
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")
secret_otp = os.getenv("SYS_SECRET_OTP")
destino_final_dir = os.getenv("DESTINO_FINAL_DIR")


def iniciar_driver():
    print("Iniciando driver do navegador...")
    options = Options()
    # options.add_argument("--headless")
    # Definir diretório de download para a pasta Downloads do usuário
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(user_download_dir, exist_ok=True)
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.dir", user_download_dir)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,application/vnd.ms-excel")
    profile.set_preference("pdfjs.disabled", True)
    options.profile = profile
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

def clicar_elemento_real(driver, xpath):
    elemento = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
    ActionChains(driver).move_to_element(elemento).click().perform()

def gerar_otp():
    print("Gerando OTP...")
    response = requests.post(
        'http://192.168.0.129:8001/generate_otp', 
        json={"secret": secret_otp}
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

def esperar_download_pronto(driver, xpath, timeout=60):
    """Espera até o link de download estar realmente pronto (href válido)."""
    for _ in range(timeout):
        try:
            elemento = driver.find_element(By.XPATH, xpath)
            href = elemento.get_attribute("href")
            if href and href.endswith(".xlsx"):
                print(f"Link pronto no DOM: {href}")
                return elemento
        except Exception:
            pass
        time.sleep(1)
    raise Exception("Link de download não ficou pronto a tempo.")

def baixar_arquivo_com_cookies(driver, url, caminho_destino):
    import requests
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    resposta = s.get(url, stream=True)
    if resposta.status_code == 200:
        with open(caminho_destino, 'wb') as f:
            for chunk in resposta.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Arquivo salvo em: {caminho_destino}")
    else:
        print(f"Erro ao baixar arquivo: {resposta.status_code}")

def realizar_download_atividades(driver, button_xpath):
    print("Realizando download de atividades...")
    clicar_elemento(driver, button_xpath)
    esperar_elemento(driver, XPATHS['atividades']['input_code_field'])

    codigo_elemento = esperar_elemento(driver, XPATHS['atividades']['code_field'])
    codigo_texto = codigo_elemento.text
    # Extrair o número do texto usando regex
    match = re.search(r"(\d+)", codigo_texto)
    if match:
        numero_atividades = int(match.group(1))
    else:
        raise ValueError(f"Não foi possível extrair o número de atividades do texto: {codigo_texto}")

    inserir_texto(driver, XPATHS['atividades']['input_code_field'], numero_atividades)
    clicar_elemento(driver, XPATHS['atividades']['confirm_button'])
    elemento_download = esperar_download_pronto(driver, XPATHS['atividades']['download_link'])
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'Exportacao Atividades.xlsx'
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_destino = os.path.join(user_download_dir, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['atividades']['close_button'])
    fechar_modal(driver)
    print("Atividades baixadas com sucesso.")

def realizar_download_producao(driver):
    print("Realizando download de produção...")
    esperar_elemento(driver, XPATHS['producao']['download_link'], 300)
    elemento_download = esperar_download_pronto(driver, XPATHS['producao']['download_link'])
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'ExportacaoProducao.xlsx'
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_destino = os.path.join(user_download_dir, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['producao']['close_button'])
    print("Produção baixado com sucesso.")

def fechar_modal(driver):
    # print("Fechando modal...")
    try:
        overlay = driver.find_element(By.XPATH, XPATHS['common']['modal_overlay'])
        if overlay.is_displayed():
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.XPATH, XPATHS['common']['modal_overlay'])))
            # print("Modal fechado.")
    except Exception:
        print("Nenhum modal aberto.")

def exportAtividadesStatus(driver):
    print("Exportando atividades<>status...")
    esperar_elemento(driver, XPATHS['atividades']['panel'])
    clicar_elemento(driver, XPATHS['atividades']['panel'])
    
    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=90) # Subtrai 90 dias da data atual
    data_inicial = data_90_dias_atras.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    
    selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial)
    clicar_elemento(driver, XPATHS['atividades']['search_button'])
    realizar_download_atividades(driver, XPATHS['atividades']['export_status_button'])

def exportAtividades(driver):
    print("Exportando atividades...")
    esperar_elemento(driver, XPATHS['atividades']['panel'])
    clicar_elemento(driver, XPATHS['atividades']['panel'])
    
    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=90) # Subtrai 90 dias da data atual
    data_inicial = data_90_dias_atras.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    
    selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial)
    clicar_elemento(driver, XPATHS['atividades']['search_button'])
    realizar_download_atividades(driver, XPATHS['atividades']['export_atividades_button'])

def exportProducao(driver):
    print("Exportando produção...")
    esperar_elemento(driver, XPATHS['producao']['panel'])
    clicar_elemento(driver, XPATHS['producao']['panel'])

    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=92) # Subtrai 90 dias da data atual
    data_inicial_ajustada = data_90_dias_atras.replace(day=1) # Define o dia como 1
    data_inicial = data_inicial_ajustada.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    texto = "Painel de Produção Vivo"

    selecionar_data(driver, XPATHS['producao']['date_picker'], data_inicial)
    selecionar_texto(driver, XPATHS['producao']['combo_box'], texto)
    clicar_elemento(driver, XPATHS['producao']['radio_button'])
    clicar_elemento(driver, XPATHS['producao']['search_button'])
    realizar_download_producao(driver)
    fechar_modal(driver)

def login(driver):
    acessar_pagina(driver, url)
    print("Realizando login...")
    esperar_elemento(driver, XPATHS['login']['username_field'])
    
    inserir_texto(driver, XPATHS['login']['username_field'], username)
    inserir_texto(driver, XPATHS['login']['password_field'], password)
    
    while True:
        otp = gerar_otp()
        clicar_elemento(driver, XPATHS['login']['otp_radio'])
        clicar_elemento(driver, XPATHS['login']['otp_field'])
        inserir_texto(driver, XPATHS['login']['otp_field'], otp)
        clicar_elemento(driver, XPATHS['login']['login_button'])
        
        time.sleep(2) 
        
        try:
            mensagem = driver.find_element(By.XPATH, XPATHS['login']['error_message']).text
            
            if mensagem in ["Usuário não encontrado", "Código autenticador inválido", "Usuário inexistente ou senha inválida"]:
                print("Erro detectado, tentando novamente...")
                continue
        except:
            break
    
    print("Login realizado com sucesso!")

def logout(driver):
    print("Realizando logout...")
    esperar_elemento(driver, XPATHS['logout']['logout_button'])
    clicar_elemento(driver, XPATHS['logout']['logout_button'])
    esperar_elemento(driver, XPATHS['logout']['logout_option'])
    clicar_elemento(driver, XPATHS['logout']['logout_option'])

def mover_arquivos(diretorio_origem, arquivos, diretorio_destino, subdiretorio):
    print("Iniciando movimentação segura de arquivos...")    
    os.makedirs(diretorio_destino, exist_ok=True) # Garantir estrutura de diretórios
    historico_path = os.path.join(diretorio_destino, subdiretorio)
    os.makedirs(historico_path, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for arquivo in arquivos:
        dest_file = os.path.join(diretorio_destino, arquivo)
        orig_file = os.path.join(diretorio_origem, arquivo)        

        if os.path.exists(orig_file): # Verifica se o arquivo de origem existe
            if os.path.exists(dest_file): # Gerenciar conflitos no destino
                print(f"💥 Conflito detectado: {arquivo}")
                nome, ext = os.path.splitext(arquivo) # Gerar novo nome único
                nome_salvo = f"{nome}_BACKUP_{timestamp}{ext}"
                shutil.move(dest_file, os.path.join(historico_path, nome_salvo)) # Mover arquivo conflitante para histórico
                print(f"✅ Backup criado: {nome_salvo}")            

            shutil.move(orig_file, dest_file) # Mover arquivo original para o destino
            print(f"➡️ {arquivo} movido para destino")
        else:
            print(f"⚠️ Arquivo ausente: {orig_file}")
    print("Operação concluída com segurança!\n")

def executar_rotina():
    try:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Iniciando execução em {data_atual}")

        # Limpar a pasta de downloads antes de iniciar os downloads
        # (opcional: pode remover esta limpeza se não quiser apagar arquivos do usuário)
        user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        # Limpar arquivos antigos na pasta Downloads do usuário que contenham palavras-chave
        palavras_chave = ["atividades", "status", "produção"]
        for f in os.listdir(user_download_dir):
            if any(palavra in f.lower() for palavra in palavras_chave):
                file_path = os.path.join(user_download_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Arquivo antigo removido: {f}")

        driver = iniciar_driver()
        login(driver)
        exportAtividadesStatus(driver)
        # logout(driver)
        # time.sleep(5)
        # driver.quit()
        time.sleep(10)

        # driver = iniciar_driver()
        # login(driver)
        exportAtividades(driver)
        # logout(driver)
        # time.sleep(5)
        # driver.quit()
        time.sleep(10)

        # driver = iniciar_driver()
        # login(driver)
        exportProducao(driver)
        # logout(driver)
        # time.sleep(5)
        driver.quit()
        time.sleep(10)

        dirOrigem = user_download_dir
        dirDestino = destino_final_dir
        os.makedirs(dirDestino, exist_ok=True)
        subDiretorio = "histórico"

        # Listar arquivos encontrados na pasta de download
        print("Arquivos encontrados na pasta de download:", os.listdir(dirOrigem))

        # Mover todos arquivos .xlsx encontrados
        arquivos_xlsx = [f for f in os.listdir(dirOrigem) if f.lower().endswith('.xlsx')]
        mover_arquivos(dirOrigem, arquivos_xlsx, dirDestino, subDiretorio)

        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Finalizado em {data_atual}")
        print("⏳ Agendando a execução a cada 30 minutos...")

    except Exception as e:
        print(f"Erro: {e}")  # Registra o erro no log

# Função para agendar a execução
def agendar_execucao():
    schedule.every(30).minutes.do(executar_rotina)

# Iniciar o agendamento
agendar_execucao()

# Executar a rotina uma vez antes de agendar
executar_rotina()

while True:
    agora = datetime.now().hour
    if 8 <= agora < 22:
        schedule.run_pending()  # Executa as tarefas agendadas
        if not schedule.get_jobs():  # Verifica se não há tarefas agendadas
            print("Aguardando a próxima execução...")
    time.sleep(30)  # Aguarda 30 segundos antes de verificar novamente