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
import logging
import sys
from pathlib import Path
from selenium.common.exceptions import ElementClickInterceptedException

# Configuração de logging
logging.basicConfig(
    filename='robo_download.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
# Adicionar handler para logar no console também
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Função para notificação (placeholder)
def send_notification(msg):
    # Aqui você pode implementar envio por e-mail, Telegram, etc.
    logger.warning(f'NOTIFICAÇÃO: {msg}')

# Carrega as variáveis do arquivo .env
if not Path('.env').exists():
    print('Arquivo .env não encontrado!')
    sys.exit(1)
load_dotenv('.env', override=True)

# Função para checar variáveis obrigatórias
def checar_variaveis_obrigatorias(vars_list):
    faltando = [v for v in vars_list if not os.getenv(v)]
    if faltando:
        print(f"Variáveis obrigatórias faltando no .env: {', '.join(faltando)}")
        sys.exit(1)

checar_variaveis_obrigatorias([
    'SYS_URL', 'SYS_USERNAME', 'SYS_PASSWORD', 'SYS_SECRET_OTP', 'DESTINO_FINAL_DIR',
    'BROWSER', 'RETRIES_DOWNLOAD', 'TIMEOUT_DOWNLOAD', 'HEADLESS', 'OTP_URL'
])

# Timeouts configuráveis
TIMEOUT_DOWNLOAD = int(os.getenv('TIMEOUT_DOWNLOAD', '60'))
RETRIES_DOWNLOAD = int(os.getenv('RETRIES_DOWNLOAD', '3'))

# Carrega os XPaths do arquivo map.json
with open('map.json', 'r') as f:
    XPATHS = json.load(f)

# Acessando as variáveis
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")
secret_otp = os.getenv("SYS_SECRET_OTP")
destino_final_dir = os.getenv("DESTINO_FINAL_DIR")
browser = os.getenv("BROWSER")
print(f"Valor lido de BROWSER no .env: {browser!r}")
browser = browser.strip().replace('"','').replace("'","").lower()
headless = os.getenv("HEADLESS", "false").lower() == "true"
otp_url = os.getenv("OTP_URL", "http://localhost:8000/generate_otp")

logger.info(f"Valor de url: {url!r}")

def iniciar_driver():
    logger.info(f"Iniciando driver do navegador... ({browser})")
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(user_download_dir, exist_ok=True)
    driver = None
    if browser == "chrome":
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--log-level=3")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        prefs = {
            "download.default_directory": user_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
    elif browser == "edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        prefs = {
            "download.default_directory": user_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Edge(options=options)
    else:
        raise ValueError(f"Navegador não suportado: {browser}")
    return driver

def acessar_pagina(driver, url):
    logger.info(f"Tentando acessar: {url!r}")
    driver.get(url)
    logger.info(f"Acessou: {url!r}")

def encontrar_elemento(driver, xpath, referencia_map=None, tempo=10):
    try:
        elemento = WebDriverWait(driver, tempo).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return elemento
    except Exception:
        msg = f"Elemento não encontrado para XPath: {xpath}"
        if referencia_map:
            msg += f" (referência map.json: {referencia_map})"
        logger.error(msg)
        send_notification(msg)
        return None

def esperar_elemento(driver, xpath, referencia_map=None, tempo=300):
    elemento = encontrar_elemento(driver, xpath, referencia_map, tempo)
    if not elemento:
        raise Exception(f"Elemento não encontrado: {xpath} (referência map.json: {referencia_map})")
    return elemento

def salvar_screenshot_elemento(driver, elemento, referencia_map=None):
    from pathlib import Path
    import datetime
    screenshots_dir = Path('element_screenshots')
    screenshots_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    ref = referencia_map.replace('.', '_') if referencia_map else 'elemento'
    filename = f'{ref}_{timestamp}.png'
    filepath = screenshots_dir / filename
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
        elemento.screenshot(str(filepath))
        logger.info(f"Screenshot do elemento salvo em: {filepath}")
    except Exception as e:
        logger.warning(f"Falha ao salvar screenshot do elemento: {e}")

def clicar_elemento(driver, xpath, referencia_map=None):
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map)
        if elemento:
            salvar_screenshot_elemento(driver, elemento, referencia_map)
            elemento.click()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath} (referência map.json: {referencia_map}). Tentando pressionar ESC para fechar overlay.")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        try:
            elemento = encontrar_elemento(driver, xpath, referencia_map)
            if elemento:
                salvar_screenshot_elemento(driver, elemento, referencia_map)
                elemento.click()
        except Exception as e2:
            logger.error(f"Falha ao clicar após ESC: {e2}")
            raise


def clicar_elemento_real(driver, xpath, referencia_map=None):
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
        if elemento:
            salvar_screenshot_elemento(driver, elemento, referencia_map)
            driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
            ActionChains(driver).move_to_element(elemento).click().perform()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath} (referência map.json: {referencia_map}). Tentando pressionar ESC para fechar overlay.")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        try:
            elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
            if elemento:
                salvar_screenshot_elemento(driver, elemento, referencia_map)
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                ActionChains(driver).move_to_element(elemento).click().perform()
        except Exception as e2:
            logger.error(f"Falha ao clicar após ESC: {e2}")
            raise

def gerar_otp():
    print("Gerando OTP...")
    response = requests.post(
        otp_url, 
        json={"secret": secret_otp}
    )
    if response.status_code == 200:
        return response.json().get("otp")
    else:
        print(f"Erro ao gerar OTP: {response.status_code} - {response.text}")
        exit(1)

def selecionar_data(driver, xpath, data, referencia_map=None):
    elemento = esperar_elemento(driver, xpath, referencia_map)
    if elemento:
        try:
            elemento.clear()
        except Exception:
            pass  # Alguns campos customizados não suportam clear()
        elemento.click()
        # Simular digitação lenta
        for char in data:
            elemento.send_keys(char)
            time.sleep(0.05)
        # Tentar ENTER para fechar o datepicker
        elemento.send_keys(Keys.ENTER)
        time.sleep(0.5)
        valor = elemento.get_attribute('value')
        if valor != data:
            # Tentar clicar no body para fechar o datepicker
            try:
                driver.find_element(By.TAG_NAME, 'body').click()
                time.sleep(0.5)
            except Exception:
                pass
            valor = elemento.get_attribute('value')
            if valor != data:
                logger.warning(f"Campo de data não foi preenchido corretamente: esperado {data}, obtido {valor}")

def selecionar_texto(driver, xpath, text, referencia_map=None):
    # print("Selecionando textos...")
    elemento = esperar_elemento(driver, xpath, referencia_map)
    elemento.click()
    elemento.clear()
    elemento.send_keys(text)
    time.sleep(5)
    driver.find_element(By.XPATH, xpath).send_keys(Keys.ENTER)

def esperar_download_pronto(driver, xpath, referencia_map=None, timeout=60):
    """Espera até o link de download estar realmente pronto (href válido)."""
    for _ in range(timeout):
        try:
            elemento = encontrar_elemento(driver, xpath, referencia_map)
            if elemento:
                href = elemento.get_attribute("href")
                if href and href.endswith(".xlsx"):
                    logger.info(f"Link pronto no DOM: {href}")
                    return elemento
        except Exception:
            pass
        time.sleep(1)
    msg = f"Link de download não ficou pronto a tempo: {xpath} (referência map.json: {referencia_map})"
    logger.error(msg)
    send_notification(msg)
    raise Exception(msg)

def baixar_arquivo_com_cookies(driver, url, caminho_destino):
    import requests
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    for tentativa in range(1, RETRIES_DOWNLOAD+1):
        try:
            logger.info(f'Tentando baixar arquivo: {url} (tentativa {tentativa})')
            resposta = s.get(url, stream=True, timeout=TIMEOUT_DOWNLOAD)
            if resposta.status_code == 200:
                with open(caminho_destino, 'wb') as f:
                    for chunk in resposta.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Arquivo salvo em: {caminho_destino}")
                return True
            else:
                logger.error(f'Erro ao baixar arquivo: {resposta.status_code}')
        except Exception as e:
            logger.error(f'Erro ao baixar arquivo: {e}')
        time.sleep(2)
    send_notification(f'Falha ao baixar arquivo após {RETRIES_DOWNLOAD} tentativas: {url}')
    return False

def inserir_texto(driver, xpath, texto, referencia_map=None):
    elemento = esperar_elemento(driver, xpath, referencia_map)
    if elemento:
        salvar_screenshot_elemento(driver, elemento, referencia_map)
        elemento.click()
        elemento.clear()
        elemento.send_keys(texto)

def realizar_download_atividades(driver, button_xpath):
    logger.info("Realizando download de atividades...")
    clicar_elemento(driver, button_xpath, 'atividades.export_atividades_button')
    esperar_elemento(driver, XPATHS['atividades']['input_code_field'], 'atividades.input_code_field')
    codigo_elemento = esperar_elemento(driver, XPATHS['atividades']['code_field'], 'atividades.code_field')
    codigo_texto = codigo_elemento.text
    match = re.search(r"(\d+)", codigo_texto)
    if match:
        numero_atividades = int(match.group(1))
    else:
        raise ValueError(f"Não foi possível extrair o número de atividades do texto: {codigo_texto}")
    inserir_texto(driver, XPATHS['atividades']['input_code_field'], numero_atividades, 'atividades.input_code_field')
    clicar_elemento(driver, XPATHS['atividades']['confirm_button'], 'atividades.confirm_button')
    elemento_download = esperar_download_pronto(driver, XPATHS['atividades']['download_link'], 'atividades.download_link')
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'Exportacao Atividades.xlsx'
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_destino = os.path.join(user_download_dir, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['atividades']['close_button'], 'atividades.close_button')
    fechar_modal(driver)
    logger.info("Atividades baixadas com sucesso.")

def realizar_download_producao(driver):
    logger.info("Realizando download de produção...")
    esperar_elemento(driver, XPATHS['producao']['download_link'], 'producao.download_link', 300)
    elemento_download = esperar_download_pronto(driver, XPATHS['producao']['download_link'], 'producao.download_link')
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'ExportacaoProducao.xlsx'
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_destino = os.path.join(user_download_dir, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['producao']['close_button'], 'producao.close_button')
    logger.info("Produção baixado com sucesso.")

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
    logger.info("Exportando atividades<>status...")
    esperar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
    clicar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
    
    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=90) # Subtrai 90 dias da data atual
    data_inicial = data_90_dias_atras.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    
    selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial, 'atividades.date_picker')
    clicar_elemento(driver, XPATHS['atividades']['search_button'], 'atividades.search_button')
    realizar_download_atividades(driver, XPATHS['atividades']['export_status_button'])

def exportAtividades(driver):
    logger.info("Exportando atividades...")
    esperar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
    clicar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
    
    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=90) # Subtrai 90 dias da data atual
    data_inicial = data_90_dias_atras.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    
    selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial, 'atividades.date_picker')
    clicar_elemento(driver, XPATHS['atividades']['search_button'], 'atividades.search_button')
    realizar_download_atividades(driver, XPATHS['atividades']['export_atividades_button'])

def exportProducao(driver):
    logger.info("Exportando produção...")
    esperar_elemento(driver, XPATHS['producao']['panel'], 'producao.panel')
    clicar_elemento(driver, XPATHS['producao']['panel'], 'producao.panel')

    data_atual = datetime.now() # Obtém a data atual
    data_90_dias_atras = data_atual - timedelta(days=92) # Subtrai 90 dias da data atual
    data_inicial_ajustada = data_90_dias_atras.replace(day=1) # Define o dia como 1
    data_inicial = data_inicial_ajustada.strftime("%d/%m/%Y") # Formata a data para o padrão dd/mm/aaaa
    texto = "Painel de Produção Vivo"

    selecionar_data(driver, XPATHS['producao']['date_picker'], data_inicial, 'producao.date_picker')
    selecionar_texto(driver, XPATHS['producao']['combo_box'], texto, 'producao.combo_box')
    clicar_elemento(driver, XPATHS['producao']['radio_button'], 'producao.radio_button')
    clicar_elemento(driver, XPATHS['producao']['search_button'], 'producao.search_button')
    realizar_download_producao(driver)
    fechar_modal(driver)

def login(driver):
    acessar_pagina(driver, url)
    logger.info("Realizando login...")
    esperar_elemento(driver, XPATHS['login']['username_field'], 'login.username_field')
    inserir_texto(driver, XPATHS['login']['username_field'], username, 'login.username_field')
    inserir_texto(driver, XPATHS['login']['password_field'], password, 'login.password_field')
    while True:
        otp = gerar_otp()
        clicar_elemento(driver, XPATHS['login']['otp_radio'], 'login.otp_radio')
        clicar_elemento(driver, XPATHS['login']['otp_field'], 'login.otp_field')
        inserir_texto(driver, XPATHS['login']['otp_field'], otp, 'login.otp_field')
        clicar_elemento(driver, XPATHS['login']['login_button'], 'login.login_button')
        time.sleep(2)
        try:
            mensagem = driver.find_element(By.XPATH, XPATHS['login']['error_message']).text
            if mensagem in ["Usuário não encontrado", "Código autenticador inválido", "Usuário inexistente ou senha inválida"]:
                logger.warning("Erro detectado, tentando novamente...")
                continue
        except:
            break
    logger.info("Login realizado com sucesso!")

def logout(driver):
    logger.info("Realizando logout...")
    esperar_elemento(driver, XPATHS['logout']['logout_button'], 'logout.logout_button')
    clicar_elemento(driver, XPATHS['logout']['logout_button'], 'logout.logout_button')
    esperar_elemento(driver, XPATHS['logout']['logout_option'], 'logout.logout_option')
    clicar_elemento(driver, XPATHS['logout']['logout_option'], 'logout.logout_option')

def mover_arquivos(diretorio_origem, arquivos, diretorio_destino, subdiretorio):
    logger.info("Iniciando movimentação segura de arquivos...")    
    os.makedirs(diretorio_destino, exist_ok=True) # Garantir estrutura de diretórios
    historico_path = os.path.join(diretorio_destino, subdiretorio)
    os.makedirs(historico_path, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for arquivo in arquivos:
        dest_file = os.path.join(diretorio_destino, arquivo)
        orig_file = os.path.join(diretorio_origem, arquivo)        

        if os.path.exists(orig_file): # Verifica se o arquivo de origem existe
            if os.path.exists(dest_file): # Gerenciar conflitos no destino
                logger.warning(f"💥 Conflito detectado: {arquivo}")
                nome, ext = os.path.splitext(arquivo) # Gerar novo nome único
                nome_salvo = f"{nome}_BACKUP_{timestamp}{ext}"
                shutil.move(dest_file, os.path.join(historico_path, nome_salvo)) # Mover arquivo conflitante para histórico
                logger.info(f"✅ Backup criado: {nome_salvo}")            

            shutil.move(orig_file, dest_file) # Mover arquivo original para o destino
            logger.info(f"➡️ {arquivo} movido para destino")
        else:
            logger.warning(f"⚠️ Arquivo ausente: {orig_file}")
    logger.info("Operação concluída com segurança!\n")

def executar_rotina():
    etapas = []
    try:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Iniciando execução em {data_atual}")
        etapas.append(f"Execução iniciada em {data_atual}")
        user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        palavras_chave = ["atividades", "status", "produção"]
        for f in os.listdir(user_download_dir):
            if any(palavra in f.lower() for palavra in palavras_chave):
                file_path = os.path.join(user_download_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Arquivo antigo removido: {f}")
        etapas.append("Driver iniciado")
        driver = iniciar_driver()
        etapas.append("Login realizado")
        login(driver)
        # Exportação Atividades Status
        data_atual_dt = datetime.now()
        data_90_dias_atras = data_atual_dt - timedelta(days=90)
        data_inicial_atividades = data_90_dias_atras.strftime("%d/%m/%Y")
        etapas.append(f"Exportação Atividades Status (data inicial: {data_inicial_atividades})")
        exportAtividadesStatus(driver)
        time.sleep(10)
        # Exportação Atividades
        etapas.append(f"Exportação Atividades (data inicial: {data_inicial_atividades})")
        exportAtividades(driver)
        time.sleep(10)
        # Exportação Produção
        data_90_dias_atras_producao = data_atual_dt - timedelta(days=92)
        data_inicial_ajustada = data_90_dias_atras_producao.replace(day=1)
        data_inicial_producao = data_inicial_ajustada.strftime("%d/%m/%Y")
        etapas.append(f"Exportação Produção (data inicial: {data_inicial_producao})")
        exportProducao(driver)
        driver.quit()
        etapas.append("Driver finalizado")
        time.sleep(10)
        dirOrigem = user_download_dir
        dirDestino = destino_final_dir
        os.makedirs(dirDestino, exist_ok=True)
        subDiretorio = "histórico"
        logger.info(f"Arquivos encontrados na pasta de download: {os.listdir(dirOrigem)}")
        arquivos_xlsx = [f for f in os.listdir(dirOrigem) if f.lower().endswith('.xlsx')]
        mover_arquivos(dirOrigem, arquivos_xlsx, dirDestino, subDiretorio)
        etapas.append("Arquivos movidos para destino final")
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Finalizado em {data_atual}")
        etapas.append(f"Finalizado em {data_atual}")
        logger.info("⏳ Agendando a execução a cada 30 minutos...")
    except Exception as e:
        etapas.append(f"Erro: {e}")
        logger.error(f"Erro: {e}")
        send_notification(f"Erro crítico na execução: {e}")
    finally:
        print("\nResumo das etapas executadas:")
        for etapa in etapas:
            print(f"- {etapa}")

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