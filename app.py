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
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
import socket

# Importar módulos customizados
from logging_config import configurar_logging
from notifications import notification_manager, metrics_collector

# Configuração de logging com rotação
logger = configurar_logging()

# Variáveis globais para rastreamento
driver = None
arquivos_baixados_com_sucesso = []

# Função para notificação (usa NotificationManager)
def send_notification(msg, tipo="aviso"):
    """Envia notificação através dos serviços configurados."""
    logger.warning(f'NOTIFICAÇÃO: {msg}')
    if tipo == "aviso":
        notification_manager.notificar_aviso(msg)
    elif tipo == "erro":
        notification_manager.notificar_erro(msg)
    elif tipo == "sucesso":
        notification_manager.notificar_sucesso({"mensagem": msg})

def fechar_driver_seguro():
    """Fecha o driver de forma segura, tratando exceções."""
    global driver
    if driver:
        try:
            driver.quit()
            logger.info("Driver fechado com sucesso")
        except Exception as e:
            logger.warning(f"Erro ao fechar driver: {e}")
            try:
                driver.close()
            except:
                pass
        finally:
            driver = None

def verificar_conectividade(url):
    """Verifica se é possível acessar a URL."""
    host = None
    try:
        # Extrai o host da URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        
        logger.info(f"Verificando conectividade para {host}...")
        # Tenta resolver o DNS
        socket.gethostbyname(host)
        
        # Tenta fazer uma requisição HTTP
        response = requests.head(url, timeout=10)
        logger.info(f"Conectividade OK: {response.status_code}")
        return True
    except socket.gaierror as e:
        logger.error(f"Erro DNS: Não foi possível resolver {host}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Erro de conexão: Não foi possível conectar a {url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"Timeout: Conexão com {url} expirou")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar conectividade: {e}")
        return False

def validar_configuracao():
    """Valida todas as configurações antes de iniciar o robô."""
    logger.info("Validando configuração...")
    
    erros = []
    
    # Valida URL
    if not url or not url.startswith('http'):
        erros.append("SYS_URL inválida ou não definida")
    
    # Valida credenciais
    if not username or not password:
        erros.append("Credenciais (SYS_USERNAME/SYS_PASSWORD) não definidas")
    
    # Valida diretório de destino
    if not destino_final_dir:
        erros.append("DESTINO_FINAL_DIR não definido")
    else:
        try:
            os.makedirs(destino_final_dir, exist_ok=True)
            # Testa permissão de escrita
            test_file = os.path.join(destino_final_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info(f"Permissão de escrita OK em {destino_final_dir}")
        except PermissionError:
            erros.append(f"Sem permissão de escrita em {destino_final_dir}")
        except Exception as e:
            erros.append(f"Erro ao validar diretório {destino_final_dir}: {e}")
    
    # Valida arquivo map_relative.json
    if not Path('map_relative.json').exists():
        erros.append("Arquivo map_relative.json não encontrado")
    
    # Valida navegador
    if browser not in ['chrome', 'edge']:
        erros.append(f"Navegador '{browser}' não suportado (use 'chrome' ou 'edge')")
    
    # Valida OTP se obrigatório
    if otp_required and not secret_otp:
        erros.append("OTP_REQUIRED=true mas SYS_SECRET_OTP não definido")
    
    if erros:
        logger.error("Erros de validação encontrados:")
        for erro in erros:
            logger.error(f"  - {erro}")
        return False
    
    logger.info("Validação de configuração OK")
    return True

# Carrega as variáveis do arquivo .env
if not Path('.env').exists():
    print('Arquivo .env não encontrado!')
    sys.exit(1)
load_dotenv('.env', override=True)

# Timeouts configuráveis
TIMEOUT_DOWNLOAD = int(os.getenv('TIMEOUT_DOWNLOAD', '60'))
RETRIES_DOWNLOAD = int(os.getenv('RETRIES_DOWNLOAD', '3'))

# Carrega os XPaths do arquivo map_relative.json (XPaths relativos mais robustos)
with open('map_relative.json', 'r') as f:
    XPATHS = json.load(f)
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")
secret_otp = os.getenv("SYS_SECRET_OTP", "")
destino_final_dir = os.getenv("DESTINO_FINAL_DIR")
browser = os.getenv("BROWSER", "chrome")
print(f"Valor lido de BROWSER no .env: {browser!r}")
browser = (browser or "chrome").strip().replace('"','').replace("'","").lower()
headless = os.getenv("HEADLESS", "false").lower() == "true"
otp_url = os.getenv("OTP_URL", "http://localhost:8000/generate_otp")
otp_required = os.getenv("OTP_REQUIRED", "true").lower() == "true"

logger.info(f"Valor de url: {url!r}")

def iniciar_driver():
    logger.info(f"Iniciando driver do navegador... ({browser})")
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(user_download_dir, exist_ok=True)
    driver = None
    if browser == "chrome":
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        # options.add_argument("--start-maximized")
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
        options.add_argument("--start-maximized")
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
    """Encontra um elemento com retry em caso de StaleElementReferenceException."""
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            elemento = WebDriverWait(driver, tempo).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return elemento
        except StaleElementReferenceException:
            if tentativa < max_tentativas - 1:
                logger.warning(f"Elemento stale, tentando novamente ({tentativa + 1}/{max_tentativas})...")
                time.sleep(0.5)
                continue
            else:
                raise
        except TimeoutException:
            msg = f"Timeout ao encontrar elemento: {xpath}"
            if referencia_map:
                msg += f" (referência map.json: {referencia_map})"
            logger.error(msg)
            send_notification(msg)
            return None
        except NoSuchElementException:
            msg = f"Elemento não encontrado para XPath: {xpath}"
            if referencia_map:
                msg += f" (referência map.json: {referencia_map})"
            logger.error(msg)
            send_notification(msg)
            return None
        except Exception as e:
            msg = f"Erro ao encontrar elemento: {xpath} - {e}"
            if referencia_map:
                msg += f" (referência map.json: {referencia_map})"
            logger.error(msg)
            return None
    return None

def esperar_elemento(driver, xpath, referencia_map=None, tempo=300):
    elemento = encontrar_elemento(driver, xpath, referencia_map, tempo)
    if not elemento:
        raise Exception(f"Elemento não encontrado: {xpath} (referência map.json: {referencia_map})")
    return elemento

def salvar_screenshot_elemento(driver, elemento, referencia_map=None):
    """Salva screenshot de um elemento (comentado por padrão)."""
    # Screenshots serão capturadas apenas quando erros ocorrem
    pass

def capturar_screenshot_erro(driver, referencia_map=None):
    """Captura screenshot apenas quando ocorre um erro."""
    from pathlib import Path
    import datetime
    screenshots_dir = Path('element_screenshots')
    screenshots_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    ref = referencia_map.replace('.', '_') if referencia_map else 'erro'
    filename = f'{ref}_ERROR_{timestamp}.png'
    filepath = screenshots_dir / filename
    try:
        driver.save_screenshot(str(filepath))
        logger.info(f"Screenshot de erro salvo em: {filepath}")
    except Exception as e:
        logger.warning(f"Falha ao salvar screenshot de erro: {e}")

def clicar_elemento(driver, xpath, referencia_map=None):
    """Clica em um elemento com tratamento de exceções."""
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map)
        if elemento:
            elemento.click()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath}. Tentando ESC...")
        capturar_screenshot_erro(driver, referencia_map)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            elemento = encontrar_elemento(driver, xpath, referencia_map)
            if elemento:
                elemento.click()
        except Exception as e2:
            logger.error(f"Falha ao clicar após ESC: {e2}")
            capturar_screenshot_erro(driver, referencia_map)
            raise
    except StaleElementReferenceException:
        logger.warning(f"Elemento stale, tentando novamente...")
        time.sleep(0.5)
        clicar_elemento(driver, xpath, referencia_map)
    except Exception as e:
        logger.error(f"Erro ao clicar: {xpath} - {e}")
        capturar_screenshot_erro(driver, referencia_map)
        raise


def clicar_elemento_real(driver, xpath, referencia_map=None):
    """Clica usando ActionChains com tratamento de exceções."""
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
        if elemento:
            driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
            ActionChains(driver).move_to_element(elemento).click().perform()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath}. Tentando ESC...")
        capturar_screenshot_erro(driver, referencia_map)
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
            if elemento:
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                ActionChains(driver).move_to_element(elemento).click().perform()
        except Exception as e2:
            logger.error(f"Falha ao clicar após ESC: {e2}")
            capturar_screenshot_erro(driver, referencia_map)
            raise
    except StaleElementReferenceException:
        logger.warning(f"Elemento stale, tentando novamente...")
        time.sleep(0.5)
        clicar_elemento_real(driver, xpath, referencia_map)
    except Exception as e:
        logger.error(f"Erro ao clicar (ActionChains): {xpath} - {e}")
        capturar_screenshot_erro(driver, referencia_map)
        raise

def gerar_otp():
    if not otp_required:
        return None
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

# Rastreamento de arquivos baixados
arquivos_baixados_com_sucesso = []

def baixar_arquivo_com_cookies(driver, url, caminho_destino):
    """Baixa arquivo com retry exponencial e validação."""
    import requests
    from requests.exceptions import RequestException
    
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    
    backoff_base = 1.5
    for tentativa in range(1, RETRIES_DOWNLOAD + 1):
        try:
            logger.info(f'Tentando baixar arquivo: {url} (tentativa {tentativa}/{RETRIES_DOWNLOAD})')
            resposta = s.get(url, stream=True, timeout=TIMEOUT_DOWNLOAD, allow_redirects=True)
            
            if resposta.status_code == 200:
                # Valida tamanho mínimo
                tamanho = int(resposta.headers.get('content-length', 0))
                if tamanho < 100:
                    logger.warning(f"Arquivo muito pequeno ({tamanho} bytes), pode estar corrompido")
                
                with open(caminho_destino, 'wb') as f:
                    for chunk in resposta.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Arquivo salvo em: {caminho_destino}")
                nome_arquivo = os.path.basename(caminho_destino)
                arquivos_baixados_com_sucesso.append(nome_arquivo)
                return True
            else:
                logger.error(f'Erro HTTP ao baixar: {resposta.status_code} - {resposta.reason}')
                if tentativa < RETRIES_DOWNLOAD:
                    espera = backoff_base ** (tentativa - 1)
                    logger.info(f'Aguardando {espera:.1f}s antes de retentar...')
                    time.sleep(espera)
        except RequestException as e:
            logger.error(f'Erro de requisição: {e}')
            if tentativa < RETRIES_DOWNLOAD:
                espera = backoff_base ** (tentativa - 1)
                logger.info(f'Aguardando {espera:.1f}s antes de retentar...')
                time.sleep(espera)
        except IOError as e:
            logger.error(f'Erro ao salvar arquivo: {e}')
            if tentativa < RETRIES_DOWNLOAD:
                time.sleep(2)
        except Exception as e:
            logger.error(f'Erro desconhecido ao baixar: {e}')
            if tentativa < RETRIES_DOWNLOAD:
                espera = backoff_base ** (tentativa - 1)
                time.sleep(espera)
    
    msg = f'Falha ao baixar arquivo após {RETRIES_DOWNLOAD} tentativas: {url}'
    logger.error(msg)
    send_notification(msg)
    return False

def inserir_texto(driver, xpath, texto, referencia_map=None):
    """Insere texto em um campo com tratamento de exceções."""
    try:
        elemento = esperar_elemento(driver, xpath, referencia_map)
        if elemento:
            elemento.click()
            elemento.clear()
            elemento.send_keys(texto)
    except StaleElementReferenceException:
        logger.warning(f"Elemento stale ao inserir texto, tentando novamente...")
        time.sleep(0.5)
        inserir_texto(driver, xpath, texto, referencia_map)
    except Exception as e:
        logger.error(f"Erro ao inserir texto: {xpath} - {e}")
        capturar_screenshot_erro(driver, referencia_map)
        raise

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
    """Realiza login com tratamento de exceções."""
    try:
        acessar_pagina(driver, url)
        logger.info("Realizando login...")
        esperar_elemento(driver, XPATHS['login']['username_field'], 'login.username_field')
        inserir_texto(driver, XPATHS['login']['username_field'], username, 'login.username_field')
        inserir_texto(driver, XPATHS['login']['password_field'], password, 'login.password_field')
        
        if otp_required:
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
                except NoSuchElementException:
                    break
                except Exception as e:
                    logger.warning(f"Erro ao verificar mensagem de erro: {e}")
                    break
        else:
            clicar_elemento(driver, XPATHS['login']['login_button'], 'login.login_button')
            time.sleep(2)
        
        logger.info("Login realizado com sucesso!")
    except TimeoutException:
        logger.error("Timeout durante login")
        capturar_screenshot_erro(driver, 'login')
        raise
    except Exception as e:
        logger.error(f"Erro durante login: {e}")
        capturar_screenshot_erro(driver, 'login')
        raise

def abrir_sidebar(driver):
    logger.info("Abrindo sidebar...")
    try:
        sidebar = esperar_elemento(driver, XPATHS['atividades']['sidebar'], 'atividades.sidebar')
        if sidebar:
            # Adiciona o atributo drawer-opened ao elemento sidebar
            driver.execute_script("arguments[0].setAttribute('drawer-opened', '');", sidebar)
            logger.info("Atributo drawer-opened adicionado ao sidebar com sucesso!")
            time.sleep(1)  # Pequena pausa para garantir que a UI responda
    except Exception as e:
        logger.warning(f"Erro ao abrir sidebar: {e}")
        # Continua mesmo se houver erro, pois isso não deve interromper o fluxo principal

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
    arquivos_movidos = 0
    arquivos_ignorados = 0

    for arquivo in arquivos:
        dest_file = os.path.join(diretorio_destino, arquivo)
        orig_file = os.path.join(diretorio_origem, arquivo)        

        if os.path.exists(orig_file): # Verifica se o arquivo de origem existe
            try:
                if os.path.exists(dest_file): # Gerenciar conflitos no destino
                    logger.warning(f"[CONFLITO] Arquivo ja existe: {arquivo}")
                    try:
                        nome, ext = os.path.splitext(arquivo) # Gerar novo nome único
                        nome_salvo = f"{nome}_BACKUP_{timestamp}{ext}"
                        shutil.move(dest_file, os.path.join(historico_path, nome_salvo)) # Mover arquivo conflitante para histórico
                        logger.info(f"[BACKUP] Criado: {nome_salvo}")
                    except PermissionError as e:
                        logger.warning(f"⚠️ Não foi possível criar backup de {arquivo}: {e}")
                        logger.warning(f"⚠️ Ignorando movimentação do arquivo: {arquivo}")
                        arquivos_ignorados += 1
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao criar backup de {arquivo}: {e}")
                        logger.warning(f"⚠️ Ignorando movimentação do arquivo: {arquivo}")
                        arquivos_ignorados += 1
                        continue

                shutil.move(orig_file, dest_file) # Mover arquivo original para o destino
                logger.info(f"[MOVIDO] {arquivo} -> destino")
                arquivos_movidos += 1
            except PermissionError as e:
                logger.warning(f"⚠️ Arquivo em uso por outro processo: {arquivo}")
                logger.warning(f"⚠️ Detalhes do erro: {e}")
                logger.warning(f"⚠️ Ignorando movimentação do arquivo e continuando o fluxo...")
                arquivos_ignorados += 1
            except Exception as e:
                logger.warning(f"⚠️ Erro ao mover arquivo {arquivo}: {e}")
                logger.warning(f"⚠️ Ignorando movimentação do arquivo e continuando o fluxo...")
                arquivos_ignorados += 1
        else:
            logger.warning(f"⚠️ Arquivo ausente: {orig_file}")
            arquivos_ignorados += 1
    
    logger.info(f"Operação concluída: {arquivos_movidos} arquivo(s) movido(s), {arquivos_ignorados} arquivo(s) ignorado(s)\n")

def executar_rotina():
    global arquivos_baixados_com_sucesso, driver
    arquivos_baixados_com_sucesso = []  # Resetar lista a cada execução
    
    # Iniciar coleta de métricas
    metrics_collector.iniciar()
    tempo_etapa_inicio = datetime.now()
    
    resumo = {
        "inicio": None,
        "atividades_status": None,
        "atividades": None,
        "producao": None,
        "arquivos": [],
        "fim": None,
        "status": "sucesso",
        "metricas": {}
    }
    
    try:
        # Validação prévia
        if not validar_configuracao():
            logger.error("Validação de configuração falhou. Abortando...")
            resumo["status"] = "erro_validacao"
            notification_manager.notificar_erro("Validação de configuração falhou")
            return
        
        # Verificar conectividade
        if not verificar_conectividade(url):
            logger.error("Sem conectividade com o servidor. Abortando...")
            resumo["status"] = "erro_conectividade"
            notification_manager.notificar_erro("Sem conectividade com o servidor")
            return
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        resumo["inicio"] = data_atual
        logger.info(f"Iniciando execução em {data_atual}")
        
        # Limpa a pasta de screenshots
        screenshots_dir = Path('element_screenshots')
        if screenshots_dir.exists():
            for arquivo in screenshots_dir.glob('*'):
                try:
                    arquivo.unlink()
                    logger.info(f"Screenshot removido: {arquivo.name}")
                except Exception as e:
                    logger.warning(f"Erro ao remover screenshot: {arquivo.name} - {e}")
        
        user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        palavras_chave = ["atividades", "status", "produção"]
        for f in os.listdir(user_download_dir):
            if any(palavra in f.lower() for palavra in palavras_chave):
                file_path = os.path.join(user_download_dir, f)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Arquivo antigo removido: {f}")
                    except PermissionError as e:
                        logger.warning(f"Arquivo em uso (PermissionError): {f}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo: {f} - {e}")
        
        driver = iniciar_driver()
        login(driver)
        
        # Exportação Atividades Status
        data_atual_dt = datetime.now()
        data_90_dias_atras = data_atual_dt - timedelta(days=90)
        data_inicial_atividades = data_90_dias_atras.strftime("%d/%m/%Y")
        resumo["atividades_status"] = data_inicial_atividades
        
        try:
            logger.info(f"Exportação Atividades Status (data inicial: {data_inicial_atividades})")
            abrir_sidebar(driver)
            exportAtividadesStatus(driver)
            time.sleep(10)
            tempo_etapa = (datetime.now() - tempo_etapa_inicio).total_seconds()
            metrics_collector.marcar_etapa("Atividades Status", tempo_etapa)
        except Exception as e:
            logger.error(f"Erro na exportação de Atividades Status: {e}")
            resumo["status"] = "erro_exportacao"
        
        # Exportação Atividades
        resumo["atividades"] = data_inicial_atividades
        try:
            logger.info(f"Exportação Atividades (data inicial: {data_inicial_atividades})")
            tempo_etapa_inicio = datetime.now()
            abrir_sidebar(driver)
            exportAtividades(driver)
            time.sleep(10)
            tempo_etapa = (datetime.now() - tempo_etapa_inicio).total_seconds()
            metrics_collector.marcar_etapa("Atividades", tempo_etapa)
        except Exception as e:
            logger.error(f"Erro na exportação de Atividades: {e}")
            resumo["status"] = "erro_exportacao"
        
        # Exportação Produção
        data_90_dias_atras_producao = data_atual_dt - timedelta(days=92)
        data_inicial_ajustada = data_90_dias_atras_producao.replace(day=1)
        data_inicial_producao = data_inicial_ajustada.strftime("%d/%m/%Y")
        resumo["producao"] = data_inicial_producao
        
        try:
            logger.info(f"Exportação Produção (data inicial: {data_inicial_producao})")
            tempo_etapa_inicio = datetime.now()
            abrir_sidebar(driver)
            exportProducao(driver)
            tempo_etapa = (datetime.now() - tempo_etapa_inicio).total_seconds()
            metrics_collector.marcar_etapa("Produção", tempo_etapa)
        except Exception as e:
            logger.error(f"Erro na exportação de Produção: {e}")
            resumo["status"] = "erro_exportacao"
        
        time.sleep(10)
        
        # Movimentação de arquivos
        dirOrigem = user_download_dir
        dirDestino = destino_final_dir
        if dirDestino:
            try:
                tempo_etapa_inicio = datetime.now()
                os.makedirs(dirDestino, exist_ok=True)
                subDiretorio = "histórico"
                logger.info(f"Arquivos encontrados na pasta de download: {os.listdir(dirOrigem)}")
                arquivos_xlsx = [f for f in os.listdir(dirOrigem) if f.lower().endswith('.xlsx')]
                mover_arquivos(dirOrigem, arquivos_xlsx, dirDestino, subDiretorio)
                resumo["arquivos"] = arquivos_baixados_com_sucesso
                tempo_etapa = (datetime.now() - tempo_etapa_inicio).total_seconds()
                metrics_collector.marcar_etapa("Movimentação de Arquivos", tempo_etapa)
            except Exception as e:
                logger.error(f"Erro ao movimentar arquivos: {e}")
                resumo["status"] = "erro_movimentacao"
        
        data_atual_final = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        resumo["fim"] = data_atual_final
        logger.info(f"Finalizado em {data_atual_final}")
        
        # Finalizar coleta de métricas
        resumo["metricas"] = metrics_collector.finalizar()
        
        # Enviar notificação de sucesso
        if resumo["status"] == "sucesso":
            notification_manager.notificar_sucesso(resumo)
        
    except Exception as e:
        logger.error(f"Erro crítico na execução: {e}")
        resumo["status"] = "erro_critico"
        notification_manager.notificar_erro(f"Erro crítico na execução: {e}", resumo)
        capturar_screenshot_erro(driver, 'execucao_critica')
    finally:
        # Fechar driver de forma segura
        fechar_driver_seguro()
        
        # Gerar resumo formatado
        print("\n" + "="*80)
        print("RESUMO DA EXECUÇÃO")
        print("="*80)
        print(f"Status: {resumo['status'].upper()}")
        if resumo["inicio"]:
            print(f"✓ Execução iniciada em: {resumo['inicio']}")
        if resumo["atividades_status"]:
            print(f"✓ Exportação Atividades Status: {resumo['atividades_status']}")
        if resumo["atividades"]:
            print(f"✓ Exportação Atividades: {resumo['atividades']}")
        if resumo["producao"]:
            print(f"✓ Exportação Produção: {resumo['producao']}")
        if resumo["arquivos"]:
            print(f"\n✓ Arquivos baixados com sucesso ({len(resumo['arquivos'])} arquivos):")
            for arquivo in resumo["arquivos"]:
                print(f"  - {arquivo}")
        else:
            print(f"\n⚠ Nenhum arquivo foi baixado nesta execução")
        
        # Mostrar métricas
        if resumo.get("metricas"):
            print(f"\n MÉTRICAS DE PERFORMANCE:")
            print(f"  Tempo total: {resumo['metricas'].get('tempo_total', 0):.2f}s")
            for etapa, tempo in resumo['metricas'].get('etapas', {}).items():
                print(f"  {etapa}: {tempo:.2f}s")
        
        if resumo["fim"]:
            print(f"\n✓ Finalizado em: {resumo['fim']}")
        print("="*80 + "\n")

# Função para agendar a execução
def agendar_execucao():
    schedule.every(30).minutes.do(executar_rotina)

# === INICIALIZAÇÃO ===
if __name__ == '__main__':
    logger.info("="*80)
    logger.info("Iniciando Robô de Download Neo")
    logger.info("="*80)
    
    # Iniciar o agendamento
    agendar_execucao()
    
    # Executar a rotina uma vez antes de agendar
    logger.info("Executando rotina inicial...")
    executar_rotina()
    
    logger.info("Entrando em modo de agendamento...")
    while True:
        agora = datetime.now().hour
        if 8 <= agora < 22:
            schedule.run_pending()
            if not schedule.get_jobs():
                logger.info("Aguardando próxima execução...")
        time.sleep(30)