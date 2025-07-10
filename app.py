import requests, time, os, shutil, schedule, json, re
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

# Carrega os XPaths do arquivo map.json
with open('map.json', 'r') as f:
    XPATHS = json.load(f)

# Acessando as variáveis
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")
secret_otp = os.getenv("SYS_SECRET_OTP")


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
        'http://localhost:8001/generate_otp', 
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
    esperar_elemento(driver, XPATHS['atividades']['download_link'])
    time.sleep(10)
    clicar_elemento(driver, XPATHS['atividades']['download_button'])
    clicar_elemento(driver, XPATHS['atividades']['close_button'])
    fechar_modal(driver)
    print("Atividades baixadas com sucesso.")

def realizar_download_producao(driver):
    print("Realizando download de produção...")
    esperar_elemento(driver, XPATHS['producao']['download_link'], 300)
    time.sleep(10)
    clicar_elemento(driver, XPATHS['producao']['download_button'])
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

        sysUser  = os.getenv("USERNAME")
        dirOrigem = f"C:/Users/{sysUser }/Downloads"
        dirDestino = "N:"
        subDiretorio = "histórico"
        nomeArquivo1 = "Exportacao Atividade.xlsx"
        nomeArquivo2 = "Exportacao Status.xlsx"
        nomeArquivo3 = "ExportacaoProducao.xlsx"

        mover_arquivos(dirOrigem, [nomeArquivo1, nomeArquivo2, nomeArquivo3], dirDestino, subDiretorio)

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