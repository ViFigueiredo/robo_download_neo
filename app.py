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

# ✅ NOVO (Fase 5): Importar SQLAlchemy ORM do package models
from models import insert_records_sqlalchemy

# Criar pasta de logs se não existir
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configuração de logging
logging.basicConfig(
    filename=os.path.join(logs_dir, 'robo_download.log'),
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
    'BROWSER', 'RETRIES_DOWNLOAD', 'TIMEOUT_DOWNLOAD', 'HEADLESS', 'OTP_URL',
    'DB_SERVER', 'DB_DATABASE', 'DB_USERNAME', 'DB_PASSWORD', 'DB_DRIVER'
])

# Timeouts configuráveis
TIMEOUT_DOWNLOAD = int(os.getenv('TIMEOUT_DOWNLOAD', '60'))
RETRIES_DOWNLOAD = int(os.getenv('RETRIES_DOWNLOAD', '3'))
DOWNLOAD_RETRY_DELAY = int(os.getenv('DOWNLOAD_RETRY_DELAY', '120'))  # ✅ NOVO: Delay entre tentativas (padrão: 120s)

# Diretório de downloads - usar pasta do projeto por padrão
DOWNLOADS_DIR = os.getenv('DOWNLOADS_DIR', os.path.join(os.path.dirname(__file__), 'downloads'))
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Carrega os XPaths do arquivo map_relative.json (XPaths relativos mais robustos)
# Sempre carrega de \bases\
map_relative_file = os.path.join(os.path.dirname(__file__), 'bases', 'map_relative.json')
if not os.path.exists(map_relative_file):
    print(f"Arquivo map_relative.json não encontrado em: {map_relative_file}")
    sys.exit(1)

with open(map_relative_file, 'r', encoding='utf-8') as f:
    XPATHS = json.load(f)

logger.info(f"Mapeamento de XPaths carregado de: {map_relative_file}")

# Acessando as variáveis
url = os.getenv("SYS_URL")
username = os.getenv("SYS_USERNAME")
password = os.getenv("SYS_PASSWORD")
secret_otp = os.getenv("SYS_SECRET_OTP")
destino_final_dir = os.getenv("DESTINO_FINAL_DIR")
browser = os.getenv("BROWSER")
print(f"Valor lido de BROWSER no .env: {browser!r}")
browser = (browser or "").strip().replace('"','').replace("'","").lower()
headless = os.getenv("HEADLESS", "false").lower() == "true"
otp_url = os.getenv("OTP_URL", "http://localhost:8000/generate_otp")

# Novas configurações para envio
DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '25'))
POST_RETRIES = int(os.getenv('POST_RETRIES', '3'))
BACKOFF_BASE = float(os.getenv('BACKOFF_BASE', '1.5'))

logger.info(f"DRY_RUN={DRY_RUN} BATCH_SIZE={BATCH_SIZE} POST_RETRIES={POST_RETRIES} BACKOFF_BASE={BACKOFF_BASE}")

logger.info(f"Valor de url: {url!r}")

def iniciar_driver():
    logger.info(f"Iniciando driver do navegador... ({browser})")
    logger.info(f"Downloads serão salvos em: {DOWNLOADS_DIR}")
    
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
            "download.default_directory": DOWNLOADS_DIR,
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
            "download.default_directory": DOWNLOADS_DIR,
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
            msg += f" (referência map_relative.json: {referencia_map})"
        logger.error(msg)
        send_notification(msg)
        return None

def esperar_elemento(driver, xpath, referencia_map=None, tempo=300):
    elemento = encontrar_elemento(driver, xpath, referencia_map, tempo)
    if not elemento:
        raise Exception(f"Elemento não encontrado: {xpath} (referência map_relative.json: {referencia_map})")
    return elemento

def clicar_elemento(driver, xpath, referencia_map=None):
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map)
        if elemento:
            elemento.click()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath} (referência map_relative.json: {referencia_map}). Tentando pressionar ESC para fechar overlay.")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        try:
            elemento = encontrar_elemento(driver, xpath, referencia_map)
            if elemento:
                elemento.click()
        except Exception as e2:
            logger.error(f"Falha ao clicar após ESC: {e2}")
            raise


def clicar_elemento_real(driver, xpath, referencia_map=None):
    try:
        elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
        if elemento:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                ActionChains(driver).move_to_element(elemento).click().perform()
            except Exception:
                # Se falhar com o elemento, tentar encontrar novamente
                elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=5)
                if elemento:
                    driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                    ActionChains(driver).move_to_element(elemento).click().perform()
    except ElementClickInterceptedException as e:
        logger.warning(f"Click interceptado em {xpath} (referência map_relative.json: {referencia_map}). Tentando pressionar ESC para fechar overlay.")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        try:
            elemento = encontrar_elemento(driver, xpath, referencia_map, tempo=30)
            if elemento:
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

# --- Início: funções para conexão e envio ao SQL Server (Fase 5: SQLAlchemy) ---

def post_records_to_mssql(records, table_name='producao', file_name=None):
    """Envia registros para SQL Server usando SQLAlchemy ORM.
    
    ✅ NOVO (Fase 5): Usa insert_records_sqlalchemy() do package models
    ✨ MELHORADO (Fase 14): Logs visuais com progresso, contadores e erros em tempo real
    
    Args:
        records: lista de dicionários com registros a enviar
        table_name: nome da tabela para logs (default: 'producao')
        file_name: nome do arquivo para rastreamento
    
    Features automáticas:
    - Barra de progresso visual (%) durante envio
    - Contadores em tempo real (x/total registros)
    - Emojis informativos para diferentes estados
    - Detalhamento de erros e duplicatas
    - Tratamento de NUL character (0x00)
    - Detecção de duplicatas (PRIMARY KEY)
    - Per-record error handling (continua batch mesmo com erros)
    - Type coercion automático via ORM
    - Logging estruturado em JSONL
    - Taxa de sucesso em porcentagem
    
    Respeita DRY_RUN (se true apenas loga payloads sem enviar).
    
    Returns:
        dict com estatísticas: {success, failed, total, batches_total, batches_failed}
    """
    if not records:
        logger.warning(f"[{table_name}] ⏭️  Nenhum registro para enviar")
        return {
            'success': 0,
            'failed': 0,
            'total': 0,
            'batches_total': 0,
            'batches_failed': 0
        }
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"🚀 INICIANDO ENVIO PARA SQL SERVER")
    logger.info(f"=" * 80)
    logger.info(f"📊 Tabela: {table_name.upper()}")
    logger.info(f"📄 Arquivo: {file_name or 'N/A'}")
    logger.info(f"📦 Total de registros: {len(records)}")
    logger.info(f"✅ SQLAlchemy ORM ativado (com NUL handling + duplicata detection)")
    logger.info(f"=" * 80)
    
    # Iniciar cronômetro
    inicio_envio = time.time()
    
    # Delegar completamente para a função do ORM
    # Ela trata automaticamente:
    # - NUL characters
    # - Duplicatas
    # - Batching
    # - Retry
    # - Logging JSONL
    stats = insert_records_sqlalchemy(
        records=records,
        table_name=table_name,
        file_name=file_name
    )
    
    # Calcular tempo decorrido
    tempo_decorrido = time.time() - inicio_envio
    
    # Extrair estatísticas
    sucesso = int(stats.get('success', 0))
    erros = int(stats.get('failed', 0))
    duplicatas = int(stats.get('duplicates', 0))
    total = int(stats.get('total', len(records)))
    
    # Calcular percentuais
    taxa_sucesso = (sucesso / total * 100) if total > 0 else 0
    taxa_erro = (erros / total * 100) if total > 0 else 0
    taxa_duplicata = (duplicatas / total * 100) if total > 0 else 0
    
    # Barra de progresso visual
    barra_tamanho = 40
    barra_preenchida = int(barra_tamanho * taxa_sucesso / 100)
    barra = "█" * barra_preenchida + "░" * (barra_tamanho - barra_preenchida)
    
    # Determinar emoji de status geral
    if taxa_sucesso >= 95:
        status_emoji = "✅"
        status_texto = "SUCESSO COMPLETO"
    elif taxa_sucesso >= 70:
        status_emoji = "⚠️ "
        status_texto = "SUCESSO PARCIAL"
    else:
        status_emoji = "❌"
        status_texto = "FALHA"
    
    # Log visual resumido
    logger.info(f"\n" + "=" * 80)
    logger.info(f"{status_emoji} RESULTADO DO ENVIO - {status_texto}")
    logger.info(f"=" * 80)
    logger.info(f"📈 Barra de progresso: [{barra}] {taxa_sucesso:.1f}%")
    logger.info(f"✅ Registros inseridos: {sucesso}/{total} ({taxa_sucesso:.1f}%)")
    
    if duplicatas > 0:
        logger.info(f"⚠️  Duplicatas detectadas: {duplicatas}/{total} ({taxa_duplicata:.1f}%)")
    
    if erros > 0:
        logger.warning(f"❌ Registros com erro: {erros}/{total} ({taxa_erro:.1f}%)")
    
    logger.info(f"⏱️  Tempo decorrido: {tempo_decorrido:.2f}s")
    
    # Calcular velocidade
    if tempo_decorrido > 0:
        velocidade = sucesso / tempo_decorrido
        logger.info(f"🚄 Velocidade: {velocidade:.0f} registros/segundo")
    
    logger.info(f"=" * 80 + "\n")
    
    # Log detalhado para arquivo (mantém registro completo)
    logger.debug(f"[{table_name}] Estatísticas detalhadas: success={sucesso}, failed={erros}, duplicates={duplicatas}, total={total}")
    
    return stats

# --- Fim: funções para conexão e envio ao SQL Server (SQLAlchemy) ---

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
    msg = f"Link de download não ficou pronto a tempo: {xpath} (referência map_relative.json: {referencia_map})"
    logger.error(msg)
    send_notification(msg)
    raise Exception(msg)

def aguardar_arquivo_disponivel(driver, timeout=300):
    """
    Aguarda o elemento h5 com texto 'Arquivo disponível' aparecer no modal.
    Isso indica que o arquivo foi processado e está pronto para download.
    
    XPath: /html/body/vaadin-dialog-overlay/vaadin-vertical-layout/h5
    Conteúdo esperado: "Arquivo disponível"
    
    Args:
        driver: Selenium driver
        timeout: Timeout em segundos (default: 300 = 5 minutos)
    
    Returns:
        True se encontrou, lança exception se timeout
    """
    logger.info(f"⏳ Aguardando elemento 'Arquivo disponível' (timeout: {timeout}s)...")
    
    xpath_arquivo_disponivel = "/html/body/vaadin-dialog-overlay/vaadin-vertical-layout/h5"
    
    try:
        # Aguardar que o elemento apareça
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath_arquivo_disponivel))
        )
        
        # Verificar se o texto contém "Arquivo disponível"
        elemento = driver.find_element(By.XPATH, xpath_arquivo_disponivel)
        texto = elemento.text.strip()
        
        logger.info(f"✅ Elemento encontrado: '{texto}'")
        
        if "Arquivo disponível" in texto or "disponível" in texto.lower():
            logger.info("✅ Arquivo está pronto para download!")
            return True
        else:
            logger.warning(f"⚠️ Elemento encontrado mas texto inesperado: '{texto}'")
            return True  # Mesmo assim retorna True, pois o elemento existe
            
    except Exception as e:
        logger.error(f"❌ Timeout esperando 'Arquivo disponível': {e}")
        raise Exception(f"Arquivo não foi processado no tempo esperado ({timeout}s): {e}")

def baixar_arquivo_com_cookies(driver, url, caminho_destino):
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    cookies = driver.get_cookies()
    s = requests.Session()
    
    # ✅ NOVO: Configurar retry automático para SSLError e timeouts
    # Essa configuração faz o requests automaticamente tentar novamente em caso de erro SSL
    retry_strategy = Retry(
        total=2,  # Total de retries automáticos (além dos retries manuais)
        status_forcelist=[429, 500, 502, 503, 504],  # Status codes que devem fazer retry
        allowed_methods=["GET"],
        backoff_factor=1  # Esperar 1s, depois 2s, depois 4s entre retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    
    for tentativa in range(1, RETRIES_DOWNLOAD+1):
        try:
            logger.info(f'Tentando baixar arquivo: {url} (tentativa {tentativa}/{RETRIES_DOWNLOAD})')
            
            # ✅ NOVO: Usar timeout mais curto para detectar SSL rapidamente
            # Se der timeout, retry mais rápido que 120s
            resposta = s.get(url, stream=True, timeout=30)
            
            if resposta.status_code == 200:
                with open(caminho_destino, 'wb') as f:
                    for chunk in resposta.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"✅ Arquivo salvo em: {caminho_destino}")
                return True
            else:
                logger.error(f'❌ Erro ao baixar arquivo: Status {resposta.status_code}')
                
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout) as e:
            # SSL, Connection ou Timeout - pode ser problema transitório
            logger.error(f'❌ Erro de conexão ao baixar arquivo: {type(e).__name__}')
            logger.debug(f'   Detalhes: {str(e)[:100]}...')
            
            if tentativa < RETRIES_DOWNLOAD:
                # Para SSL/timeout, usar delay curto (30s) para server recuperar
                delay_adaptativo = 30
                logger.warning(
                    f'⏳ Erro transitório detectado. Aguardando {delay_adaptativo}s '
                    f'antes de tentar novamente... (tentativa {tentativa}/{RETRIES_DOWNLOAD})'
                )
                time.sleep(delay_adaptativo)
            else:
                logger.error(f'❌ FALHA FINAL: SSL/Connection error após {RETRIES_DOWNLOAD} tentativas')
                
        except Exception as e:
            # Outro erro genérico
            logger.error(f'❌ Erro inesperado ao baixar arquivo: {type(e).__name__}: {e}')
            
            if tentativa < RETRIES_DOWNLOAD:
                logger.warning(f'⏳ Aguardando {DOWNLOAD_RETRY_DELAY}s antes de tentar novamente...')
                time.sleep(DOWNLOAD_RETRY_DELAY)
            else:
                logger.error(f'❌ FALHA FINAL: Erro inesperado após {RETRIES_DOWNLOAD} tentativas')
    
    send_notification(f'Falha ao baixar arquivo após {RETRIES_DOWNLOAD} tentativas: {url}')
    return False

def inserir_texto(driver, xpath, texto, referencia_map=None):
    elemento = esperar_elemento(driver, xpath, referencia_map)
    if elemento:
        elemento.click()
        elemento.clear()
        elemento.send_keys(texto)

def realizar_download_atividades(driver, button_xpath, tipo_export='atividades'):
    logger.info(f"Realizando download de {tipo_export}...")
    # NÃO limpar aqui - limpeza agora acontece UMA VEZ no início de executar_rotina()
    
    # Usar tipo_export para logging apropriado
    ref_name = f'atividades.export_{tipo_export}_button'
    clicar_elemento(driver, button_xpath, ref_name)
    
    # Esperar e processar o modal de confirmação
    esperar_elemento(driver, XPATHS['atividades']['input_code_field'], 'atividades.input_code_field')
    codigo_elemento = esperar_elemento(driver, XPATHS['atividades']['code_field'], 'atividades.code_field')
    codigo_texto = codigo_elemento.text
    match = re.search(r"(\d+)", codigo_texto)
    if match:
        numero_items = int(match.group(1))
    else:
        raise ValueError(f"Não foi possível extrair o número de {tipo_export} do texto: {codigo_texto}")
    inserir_texto(driver, XPATHS['atividades']['input_code_field'], numero_items, 'atividades.input_code_field')
    clicar_elemento(driver, XPATHS['atividades']['confirm_button'], 'atividades.confirm_button')
    
    # ✅ NOVO: Aguardar que o arquivo seja processado (h5 "Arquivo disponível")
    # Timeout: 300 segundos (5 minutos) para processar arquivo
    aguardar_arquivo_disponivel(driver, timeout=300)
    
    # Agora sim, buscar o link de download
    elemento_download = esperar_download_pronto(driver, XPATHS['atividades']['download_link'], 'atividades.download_link', timeout=60)
    url_download = elemento_download.get_attribute('href')
    
    # Nome do arquivo baseado no tipo
    nomes_padrao = {
        'status': 'Exportacao Status.xlsx',
        'atividades': 'Exportacao Atividades.xlsx'
    }
    nome_arquivo = elemento_download.text.strip() or nomes_padrao.get(tipo_export, 'Exportacao.xlsx')
    caminho_destino = os.path.join(DOWNLOADS_DIR, nome_arquivo)
    
    # ✅ Realizar o download com retries
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['atividades']['close_button'], 'atividades.close_button')
    fechar_modal(driver)
    logger.info(f"✅ {tipo_export.capitalize()} baixado com sucesso.")

    # NOTA: Parse e envio para SQL Server foi removido desta função
    # Se precisar enviar, execute: python tests/test_parse_atividades.py <arquivo>
    # Seguido de: python tests/test_post_atividades.py --dry-run

def realizar_download_producao(driver):
    logger.info("Realizando download de produção...")
    # NÃO limpar aqui - limpeza agora acontece UMA VEZ no início de executar_rotina()
    
    # ✅ NOVO: Aguardar que o arquivo seja processado (h5 "Arquivo disponível")
    # Timeout: 300 segundos (5 minutos) para processar arquivo
    aguardar_arquivo_disponivel(driver, timeout=300)
    
    elemento_download = esperar_download_pronto(driver, XPATHS['producao']['download_link'], 'producao.download_link')
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'ExportacaoProducao.xlsx'
    caminho_destino = os.path.join(DOWNLOADS_DIR, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['producao']['close_button'], 'producao.close_button')
    logger.info("Produção baixado com sucesso.")

    # NOTA: Parse e envio para SQL Server foi removido desta função
    # Se precisar enviar, execute: python tests/test_parse_atividades.py <arquivo>
    # Seguido de: python tests/test_post_atividades.py --dry-run

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


def limpar_arquivos_antigos_downloads(palavras=None, padroes_regex=None, extensoes=(".xlsx",)):
    """Remove arquivos antigos na pasta DOWNLOADS_DIR que combinem com palavras-chave ou padrões.

    - palavras: lista de palavras-chave para buscar no nome (normalizadas: sem acento, minúsculas)
    - padroes_regex: lista de padrões regex a testar no nome do arquivo
    - extensoes: tupla de extensões alvo (default: .xlsx)

    Retorna o número de arquivos removidos.
    """
    import unicodedata

    def normalizar_nome(s):
        s = s or ""
        s = s.lower()
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
        s = re.sub(r'[^a-z0-9]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # Defaults de palavras/padrões comuns aos relatórios
    if palavras is None:
        palavras = [
            'exportacao', 'exportacao producao', 'producao',
            'exportacao atividades', 'atividades',
            'exportacao status', 'status', 'vivo'
        ]
    if padroes_regex is None:
        padroes_regex = [r'^exportacao.*']

    palavras_norm = [normalizar_nome(p) for p in palavras if p]
    regexes = []
    for p in padroes_regex:
        try:
            regexes.append(re.compile(p, flags=re.IGNORECASE))
        except Exception:
            pass

    downloads = DOWNLOADS_DIR
    removidos = 0
    try:
        for nome in os.listdir(downloads):
            caminho = os.path.join(downloads, nome)
            if not os.path.isfile(caminho):
                continue
            _, ext = os.path.splitext(nome)
            if extensoes and ext.lower() not in [e.lower() for e in extensoes]:
                # Filtra por extensão alvo
                continue

            nome_norm = normalizar_nome(nome)
            combina_palavra = any(p in nome_norm for p in palavras_norm)
            combina_regex = any(rx.search(nome) for rx in regexes)

            if combina_palavra or combina_regex:
                try:
                    os.remove(caminho)
                    removidos += 1
                    logger.info(f"Arquivo antigo removido: {nome}")
                except PermissionError as e:
                    logger.warning(f"Nao foi possivel remover (em uso): {nome} - {e}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo antigo: {nome} - {e}")
    except FileNotFoundError:
        os.makedirs(downloads, exist_ok=True)
    except Exception as e:
        logger.warning(f"Erro ao varrer diretorio de downloads: {e}")

    if removidos:
        logger.info(f"Limpeza de downloads concluida: {removidos} arquivo(s) removido(s)")
    else:
        logger.info("Limpeza de downloads: nenhum arquivo alvo encontrado")
    return removidos


# Utilitário: registrar resumo de envio por arquivo/tabela
def registrar_resumo_envio(table_name, file_path, stats, elapsed_seconds):
    """Grava um resumo do envio em logs/envios_resumo.jsonl e loga no console.

    stats esperado: dict com chaves success, failed, total, batches_total, batches_failed.
    """
    try:
        os.makedirs('logs', exist_ok=True)
        resumo_path = os.path.join('logs', 'envios_resumo.jsonl')
        payload = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'table': table_name,
            'file': os.path.basename(file_path) if file_path else None,
            'elapsed_seconds': round(float(elapsed_seconds or 0), 3),
            'success': int(stats.get('success', 0)) if isinstance(stats, dict) else None,
            'failed': int(stats.get('failed', 0)) if isinstance(stats, dict) else None,
            'total': int(stats.get('total', 0)) if isinstance(stats, dict) else None,
            'batches_total': int(stats.get('batches_total', 0)) if isinstance(stats, dict) else None,
            'batches_failed': int(stats.get('batches_failed', 0)) if isinstance(stats, dict) else None,
        }
        with open(resumo_path, 'a', encoding='utf-8') as fo:
            fo.write(json.dumps(payload, ensure_ascii=False) + '\n')
        logger.info(
            f"[Resumo envio] tabela={table_name} arquivo={payload['file']} total={payload['total']} "
            f"sucesso={payload['success']} falha={payload['failed']} tempo={payload['elapsed_seconds']}s"
        )
    except Exception as e:
        logger.warning(f"Falha ao registrar resumo de envio: {e}")


# --- Início: funções para processamento do ExportacaoProducao.xlsx e envio ---
def parse_export_producao(file_path):
    """Parse flexível usando pandas e sql_map.json para mapeamento de colunas.

    Melhorias:
    - Usa APENAS sql_map.json (não precisa de nocodb_map.json)
    - Normaliza cabeçalhos (remove acentos, pontuação, lower) e faz matching tolerante
    - Tenta converter strings que parecem datas para formato `%Y-%m-%d %H:%M:%S`
    - Mantém concatenação de colunas extras em `TAGS`
    """
    import pandas as pd
    import unicodedata

    # Procura sql_map.json sempre em \bases\
    sql_map_file = os.path.join(os.path.dirname(__file__), 'bases', 'sql_map.json')
    if not os.path.exists(sql_map_file):
        raise FileNotFoundError(f"Arquivo sql_map.json não encontrado em: {sql_map_file}")

    with open(sql_map_file, 'r', encoding='utf-8') as f:
        sql_map = json.load(f)

    base_name = os.path.basename(file_path)
    
    # Buscar entrada no sql_map para este arquivo
    map_entry = sql_map.get(base_name)
    if not map_entry:
        logger.warning(f"Nenhum mapeamento encontrado em {sql_map_file} para {base_name}")
        return []
    
    # expected_headers agora vem do sql_map (colunas do banco)
    expected_headers = map_entry.get('colunas', [])
    if not expected_headers:
        logger.warning(f"Nenhuma coluna mapeada para {base_name}")
        return []

    def normalize_header(s):
        if s is None:
            return ''
        s = str(s).strip().lower()
        # Remove acentos
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(ch for ch in s if not unicodedata.combining(ch))
        # Substitui caracteres não alfanuméricos por espaço
        s = re.sub(r'[^a-z0-9]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    # Ler a planilha com pandas
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        logger.error(f"Erro ao ler Excel {file_path}: {e}")
        return []

    # Preparar mapeamento tolerante entre cabeçalhos esperados (do banco) e colunas reais (do Excel)
    df.columns = [str(c).strip() if pd.notna(c) else '' for c in df.columns]
    real_columns = list(df.columns)

    expected_norm_map = {normalize_header(h): h for h in expected_headers}
    col_to_expected = {}

    for col in real_columns:
        norm = normalize_header(col)
        if norm in expected_norm_map:
            col_to_expected[col] = expected_norm_map[norm]
        else:
            # tentar match parcial (contain)
            found = None
            for en_norm, orig in expected_norm_map.items():
                if en_norm and (en_norm in norm or norm in en_norm):
                    found = orig
                    break
            if found:
                col_to_expected[col] = found
            else:
                col_to_expected[col] = None  # será tratado como TAG extra

    # Função utilitária para formatar valores
    def format_value(val):
        if pd.isna(val):
            return ""
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        # tentar converter strings que parecem datas
        if isinstance(val, str):
            val_str = val.strip()
            
            # 🆕 Remover caracteres NUL (0x00) que causam erro no SQL
            val_str = val_str.replace('\x00', '')
            
            if not val_str:
                return ""
            
            # 🆕 Ignora FutureWarning do pandas para timezones desconhecidos (ex: "10:30 AS 12:30")
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                
                try:
                    # Se contém " AS " (range de horários), retornar como string (não tentar parse)
                    if " AS " in val_str.upper():
                        return val_str
                    
                    parsed = pd.to_datetime(val_str, dayfirst=True, errors='coerce')
                    if pd.notna(parsed):
                        return parsed.to_pydatetime().strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
            return val_str
        if isinstance(val, (int, float)):
            return str(val).replace('.0', '')
        return str(val)

    records = []
    for line_num, (_, row) in enumerate(df.iterrows(), start=2):  # start=2 porque linha 1 é header
        rec = {}
        tags_extra = []
        for col, val in row.items():
            mapped = col_to_expected.get(col)
            if mapped:
                rec[mapped] = format_value(val)
            else:
                # coluna sem mapeamento -> adicionar às tags extras
                if not pd.isna(val):
                    tags_extra.append(str(val).strip())

        # Garantir todas as chaves esperadas existam com string vazia
        for h in expected_headers:
            if h not in rec or rec[h] is None:
                rec[h] = ""

        # Concatena tags no campo 'TAGS'
        if 'TAGS' in rec:
            existing = rec.get('TAGS', "")
            parts = []
            if existing:
                parts.append(existing)
            parts.extend([t for t in tags_extra if t])
            rec['TAGS'] = ' | '.join(parts) if parts else ""
        else:
            rec['TAGS'] = ' | '.join([t for t in tags_extra if t]) if tags_extra else ""

        # Adicionar número da linha (interno, não será enviado ao banco)
        rec['_line_number'] = line_num
        rec['_file_name'] = os.path.basename(file_path)

        records.append(rec)

    logger.info(f"Parsed {len(records)} registros de {file_path} (pandas, flex) usando mapeamento {base_name}")
    return records

def parse_export_atividades(file_path):
    """Parse de arquivo de Atividades - usa mesma lógica flexível de parse_export_producao."""
    return parse_export_producao(file_path)

def parse_export_status(file_path):
    """Parse de arquivo de Status com mapeamento correto de colunas duplicadas.
    
    ✅ Problema Resolvido (Phase 15.1):
    - Excel: USUÁRIO, USUÁRIO.1 (duas colunas com mesmo nome)
    - Banco: USUARIO, USUARIO_1 (renomeadas para diferenciar)
    - Este function mapeia automaticamente os nomes!
    """
    import pandas as pd
    
    # Usar parse flexível
    records = parse_export_producao(file_path)
    
    # Mapear colunas duplicadas de Excel para nomes do banco
    # Excel: USUÁRIO → Banco: USUARIO
    # Excel: USUÁRIO.1 → Banco: USUARIO_1
    for record in records:
        keys_to_rename = []
        
        for key in list(record.keys()):
            # Procurar por USUÁRIO (com ou sem acento)
            if 'USUÁRIO' in key or 'usuario' in key.lower():
                if key == 'USUÁRIO':
                    # Primeira coluna: renomear para USUARIO (mapeamento esperado pelo banco)
                    keys_to_rename.append((key, 'USUARIO'))
                elif key == 'USUÁRIO.1':
                    # Segunda coluna: renomear para USUARIO_1 (mapeamento esperado pelo banco)
                    keys_to_rename.append((key, 'USUARIO_1'))
        
        # Aplicar renomeações
        for old_key, new_key in keys_to_rename:
            if old_key in record:
                record[new_key] = record.pop(old_key)
    
    return records

def parse_only(file_path):
    """
    🆕 Parse PURO - sem logging, sem banco, sem side effects
    
    Use esta função em testes que precisam APENAS de parse para JSON
    Não dispara nenhuma operação de banco de dados
    
    Args:
        file_path: Caminho para arquivo Excel
    
    Returns:
        Lista de dicts com registros parseados
    """
    # Apenas retorna o resultado do parse sem nenhum logging que poderia disparar side effects
    return parse_export_producao(file_path)

def post_records_to_nocodb(records, table_url=None, table_name='producao'):
    """Envia registros em batches com retry/backoff.
    
    Args:
        records: lista de dicionários com registros a enviar
        table_url: URL da tabela (default: lê URL_TABELA_PRODUCAO do .env)
        table_name: nome da tabela para logs (default: 'producao')
    
    Respeita DRY_RUN (se true apenas loga payloads).
    """
    url = table_url or os.getenv('URL_TABELA_PRODUCAO')
    token = os.getenv('BEARER_TOKEN')
    if not url or not token:
        raise ValueError('URL da tabela e/ou BEARER_TOKEN não configurados no .env')

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    os.makedirs('logs', exist_ok=True)
    out_file = os.path.join('logs', f'sent_records_{table_name}.jsonl')

    success = 0
    failed = 0
    batches_total = 0
    batches_failed = 0

    def chunks(lst, n):
        """Divide lista em chunks de tamanho n."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    # Processar todos os registros primeiro
    processed_records = []
    for record in records:
        processed_record = {}
        for key, value in record.items():
            if value is None or str(value).lower() in ('none', 'nan', ''):
                processed_record[key] = ""
            elif isinstance(value, datetime):
                processed_record[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (int, float)):
                processed_record[key] = str(value).replace(".0", "")
            else:
                processed_record[key] = str(value).strip()
        processed_records.append(processed_record)

    # Dividir em batches
    batches = list(chunks(processed_records, BATCH_SIZE))
    total_batches = len(batches)
    logger.info(f"[{table_name}] Iniciando envio de {len(processed_records)} registros em {total_batches} batches de até {BATCH_SIZE} registros cada")

    # Processar cada batch
    for batch_num, batch in enumerate(batches, 1):
        batches_total += 1
        logger.info(f"[{table_name}] Processando batch {batch_num}/{total_batches} com {len(batch)} registros")

        if DRY_RUN:
            logger.info(f"[{table_name}] DRY_RUN ativo. Payload batch {batch_num}: {json.dumps(batch[:1], ensure_ascii=False)} (...)")
            with open(out_file, 'a', encoding='utf-8') as fo:
                for record in batch:
                    fo.write(json.dumps({
                        'status': 'DRY_RUN',
                        'payload': record
                    }, default=str, ensure_ascii=False) + '\n')
            success += len(batch)
            continue

        # Tentar enviar o batch
        attempt = 0
        batch_sent = False
        while attempt < POST_RETRIES and not batch_sent:
            try:
                logger.info(f"[{table_name}] Tentativa {attempt + 1} de envio do batch {batch_num}")
                resp = requests.post(url, headers=headers, json=batch, timeout=60)
                
                if resp.status_code in (200, 201):
                    success += len(batch)
                    batch_sent = True
                    try:
                        resjson = resp.json()
                    except Exception:
                        resjson = {'raw_text': resp.text}
                    with open(out_file, 'a', encoding='utf-8') as fo:
                        for record in batch:
                            fo.write(json.dumps({
                                'status': 'sent',
                                'record': record,
                                'response': resjson
                            }, default=str, ensure_ascii=False) + '\n')
                    break
                else:
                    attempt += 1
                    logger.warning(
                        f"[{table_name}] Falha no envio do batch {batch_num}. Status={resp.status_code} "
                        f"Response={resp.text} Tentativa={attempt}/{POST_RETRIES}"
                    )
                    if attempt >= POST_RETRIES:
                        failed += len(batch)
                        batches_failed += 1
                        with open(out_file, 'a', encoding='utf-8') as fo:
                            for record in batch:
                                fo.write(json.dumps({
                                    'status': 'failed',
                                    'record': record,
                                    'response_status': resp.status_code,
                                    'response_text': resp.text
                                }, default=str, ensure_ascii=False) + '\n')
                    else:
                        time.sleep(BACKOFF_BASE ** attempt)
            except Exception as e:
                attempt += 1
                logger.error(f"[{table_name}] Erro ao enviar batch {batch_num}: {e} tentativa={attempt}/{POST_RETRIES}")
                if attempt >= POST_RETRIES:
                    failed += len(batch)
                    batches_failed += 1
                    with open(out_file, 'a', encoding='utf-8') as fo:
                        for record in batch:
                            fo.write(json.dumps({
                                'status': 'failed',
                                'record': record,
                                'error': str(e)
                            }, default=str, ensure_ascii=False) + '\n')
                    break
                time.sleep(BACKOFF_BASE ** attempt)

        if batch_num < total_batches:
            # Pequena pausa entre batches para não sobrecarregar a API
            time.sleep(0.5)

    total = success + failed
    logger.info(
        f"[{table_name}] Envio concluído: {success} sucesso(s), {failed} falha(s) de {total} total "
        f"({batches_failed} de {batches_total} batches falharam)"
    )
    return {
        'success': success,
        'failed': failed,
        'total': total,
        'batches_total': batches_total,
        'batches_failed': batches_failed
    }

# --- Fim: funções para processamento do ExportacaoProducao.xlsx e envio ---

def exportAtividadesStatus(driver):
    """Exporta relatório de Status de Atividades com retry automático (3 tentativas, com delay configurável)."""
    logger.info("Exportando atividades<>status...")
    
    max_tentativas = 3
    delay_segundos = DOWNLOAD_RETRY_DELAY  # ✅ Usa delay configurável do .env (default: 120s)
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            esperar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
            clicar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
            
            data_atual = datetime.now()
            data_90_dias_atras = data_atual - timedelta(days=90)
            data_inicial = data_90_dias_atras.strftime("%d/%m/%Y")
            
            selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial, 'atividades.date_picker')
            clicar_elemento(driver, XPATHS['atividades']['search_button'], 'atividades.search_button')
            realizar_download_atividades(driver, XPATHS['atividades']['export_status_button'], 'status')
            fechar_modal(driver)
            
            logger.info("✅ Status de Atividades baixado com sucesso!")
            return  # Sucesso, sair da função
            
        except Exception as e:
            if tentativa < max_tentativas:
                logger.warning(
                    f"⚠️ Erro ao baixar Status (tentativa {tentativa}/{max_tentativas}): {type(e).__name__}\n"
                    f"   Aguardando {delay_segundos}s antes de tentar novamente..."
                )
                time.sleep(delay_segundos)
            else:
                logger.error(
                    f"❌ FALHA FINAL: Não consegui baixar Status após {max_tentativas} tentativas.\n"
                    f"   Erro: {e}"
                )
                raise

def exportAtividades(driver):
    """Exporta relatório de Atividades com retry automático (3 tentativas, 1 min delay)."""
    logger.info("Exportando atividades...")
    
    max_tentativas = 3
    delay_segundos = DOWNLOAD_RETRY_DELAY  # ✅ Usa delay configurável do .env (default: 120s)
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            # Garantir que o painel está aberto (reabrir se necessário)
            esperar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
            clicar_elemento(driver, XPATHS['atividades']['panel'], 'atividades.panel')
            time.sleep(1)  # Pequeno delay para painel abrir
            
            # Aguardar que o grid de dados apareça
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATHS['atividades']['search_button']))
            )
            
            data_atual = datetime.now()
            data_90_dias_atras = data_atual - timedelta(days=90)
            data_inicial = data_90_dias_atras.strftime("%d/%m/%Y")
            
            selecionar_data(driver, XPATHS['atividades']['date_picker'], data_inicial, 'atividades.date_picker')
            clicar_elemento(driver, XPATHS['atividades']['search_button'], 'atividades.search_button')
            time.sleep(2)  # Aguardar grid carregar com dados
            
            # Aguardar que o botão de export esteja visível
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATHS['atividades']['export_atividades_button']))
            )
            
            realizar_download_atividades(driver, XPATHS['atividades']['export_atividades_button'], 'atividades')
            fechar_modal(driver)
            
            logger.info("✅ Atividades baixado com sucesso!")
            return  # Sucesso, sair da função
            
        except Exception as e:
            if tentativa < max_tentativas:
                logger.warning(
                    f"⚠️ Erro ao baixar Atividades (tentativa {tentativa}/{max_tentativas}): {type(e).__name__}\n"
                    f"   Aguardando {delay_segundos}s antes de tentar novamente..."
                )
                time.sleep(delay_segundos)
            else:
                logger.error(
                    f"❌ FALHA FINAL: Não consegui baixar Atividades após {max_tentativas} tentativas.\n"
                    f"   Erro: {e}"
                )
                raise

def exportProducao(driver):
    """Exporta relatório de Produção com retry automático (3 tentativas, 1 min delay)."""
    logger.info("Exportando produção...")
    
    max_tentativas = 3
    delay_segundos = DOWNLOAD_RETRY_DELAY  # ✅ Usa delay configurável do .env (default: 120s)
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            esperar_elemento(driver, XPATHS['producao']['panel'], 'producao.panel')
            clicar_elemento(driver, XPATHS['producao']['panel'], 'producao.panel')

            data_atual = datetime.now()
            data_90_dias_atras = data_atual - timedelta(days=92)
            data_inicial_ajustada = data_90_dias_atras.replace(day=1)
            data_inicial = data_inicial_ajustada.strftime("%d/%m/%Y")
            texto = "Painel de Produção Vivo"

            selecionar_data(driver, XPATHS['producao']['date_picker'], data_inicial, 'producao.date_picker')
            selecionar_texto(driver, XPATHS['producao']['combo_box'], texto, 'producao.combo_box')
            clicar_elemento(driver, XPATHS['producao']['radio_button'], 'producao.radio_button')
            clicar_elemento(driver, XPATHS['producao']['search_button'], 'producao.search_button')
            realizar_download_producao(driver)
            fechar_modal(driver)
            
            logger.info("✅ Produção baixado com sucesso!")
            return  # Sucesso, sair da função
            
        except Exception as e:
            if tentativa < max_tentativas:
                logger.warning(
                    f"⚠️ Erro ao baixar Produção (tentativa {tentativa}/{max_tentativas}): {type(e).__name__}\n"
                    f"   Aguardando {delay_segundos}s antes de tentar novamente..."
                )
                time.sleep(delay_segundos)
            else:
                logger.error(
                    f"❌ FALHA FINAL: Não consegui baixar Produção após {max_tentativas} tentativas.\n"
                    f"   Erro: {e}"
                )
                raise

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
                    logger.warning(f"💥 Conflito detectado: {arquivo}")
                    try:
                        nome, ext = os.path.splitext(arquivo) # Gerar novo nome único
                        nome_salvo = f"{nome}_BACKUP_{timestamp}{ext}"
                        shutil.move(dest_file, os.path.join(historico_path, nome_salvo)) # Mover arquivo conflitante para histórico
                        logger.info(f"✅ Backup criado: {nome_salvo}")
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
                logger.info(f"➡️ {arquivo} movido para destino")
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

def processar_arquivos_baixados():
    """Processa arquivos baixados: parse e envio ao banco de dados.
    
    Executa APÓS todos os downloads estarem completos.
    ✨ MELHORADO (Fase 14): Logs visuais com progresso e indicadores de estado
    """
    logger.info("\n" + "=" * 80)
    logger.info("📤 FASE 2: Processando e enviando arquivos para o banco")
    logger.info("=" * 80)
    
    if not os.path.exists(DOWNLOADS_DIR):
        logger.warning(f"⏭️  Diretório de downloads não existe: {DOWNLOADS_DIR}")
        return None
    
    # Mapear arquivos Excel para suas configurações de processamento
    arquivos_para_processar = [
        {
            'nome': 'Exportacao Status.xlsx',
            'tabela': 'status',
            'descricao': 'Status de Atividades'
        },
        {
            'nome': 'Exportacao Atividade.xlsx',
            'tabela': 'atividade',
            'descricao': 'Atividades'
        },
        {
            'nome': 'ExportacaoProducao.xlsx',
            'tabela': 'producao',
            'descricao': 'Produção'
        }
    ]
    
    processados_sucesso = 0
    processados_erro = 0
    total_registros_enviados = 0
    total_registros_falhados = 0
    
    for idx, arquivo_info in enumerate(arquivos_para_processar, 1):
        nome_arquivo = arquivo_info['nome']
        tabela_nome = arquivo_info['tabela']
        descricao = arquivo_info['descricao']
        
        caminho_arquivo = os.path.join(DOWNLOADS_DIR, nome_arquivo)
        
        # Verificar se arquivo existe
        if not os.path.exists(caminho_arquivo):
            logger.warning(f"⏭️  [{idx}/3] {descricao}: Arquivo não encontrado (pulando)")
            continue
        
        try:
            logger.info(f"\n" + "-" * 80)
            logger.info(f"📋 [{idx}/3] Processando: {descricao}")
            logger.info("-" * 80)
            
            # Informações do arquivo
            tamanho_kb = os.path.getsize(caminho_arquivo) / 1024
            logger.info(f"📁 Arquivo: {nome_arquivo}")
            logger.info(f"📦 Tamanho: {tamanho_kb:.1f} KB")
            
            # Parse do arquivo
            logger.info(f"🔍 Fazendo parse do arquivo...")
            records = parse_export_producao(caminho_arquivo)
            
            if not records:
                logger.warning(f"⚠️  Nenhum registro encontrado no arquivo (pulando)")
                processados_erro += 1
                continue
            
            logger.info(f"✅ Parse concluído: {len(records)} registros extraídos")
            
            # Envio ao banco de dados com indicador visual
            logger.info(f"")
            logger.info(f"📤 Enviando para SQL Server ({len(records)} registros)...")
            logger.info(f"⏱️  Aguarde enquanto os dados são processados...")
            
            inicio = time.time()
            stats = post_records_to_mssql(records, table_name=tabela_nome, file_name=nome_arquivo)
            duracao = time.time() - inicio
            
            # Registrar resumo
            registrar_resumo_envio(tabela_nome, caminho_arquivo, stats, duracao)
            
            # Atualizar contadores globais
            total_registros_enviados += stats.get('success', 0)
            total_registros_falhados += stats.get('failed', 0)
            
            logger.info(f"✅ [{idx}/3] {descricao}: Processamento concluído com sucesso!")
            processados_sucesso += 1
            
        except Exception as e:
            logger.error(f"❌ [{idx}/3] {descricao}: Erro ao processar")
            logger.error(f"   Tipo de erro: {type(e).__name__}")
            logger.error(f"   Mensagem: {str(e)[:200]}")
            logger.debug(f"   Detalhes completos:", exc_info=True)
            processados_erro += 1
    
    # Resumo final
    logger.info(f"\n" + "=" * 80)
    logger.info(f"📊 RESUMO CONSOLIDADO DE PROCESSAMENTO")
    logger.info("=" * 80)
    logger.info(f"📁 Arquivos processados: {processados_sucesso}/3")
    logger.info(f"   ✅ Sucesso: {processados_sucesso}")
    logger.info(f"   ❌ Erros: {processados_erro}")
    logger.info(f"")
    logger.info(f"📦 Registros totais:")
    logger.info(f"   ✅ Enviados com sucesso: {total_registros_enviados}")
    logger.info(f"   ❌ Falhados: {total_registros_falhados}")
    logger.info(f"   📊 Taxa geral: {(total_registros_enviados/(total_registros_enviados + total_registros_falhados)*100 if (total_registros_enviados + total_registros_falhados) > 0 else 0):.1f}%")
    logger.info("=" * 80 + "\n")
    
    return {
        'sucesso': processados_sucesso,
        'erro': processados_erro,
        'total': processados_sucesso + processados_erro,
        'registros_sucesso': total_registros_enviados,
        'registros_erro': total_registros_falhados
    }

def limpar_logs():
    """
    🔧 NOVO (Fase 10): Limpa pasta logs antes de cada execução
    Remove TODOS os arquivos de log (robo_download.log, error_records_*.jsonl, sent_records_*.jsonl, etc)
    """
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        return 0
    
    removidos = 0
    
    # Remove TODOS os arquivos na pasta logs
    for arquivo in logs_dir.glob('*'):
        if arquivo.is_file():
            try:
                arquivo.unlink()
                logger.info(f"🗑️  Log removido: {arquivo.name}")
                removidos += 1
            except Exception as e:
                logger.warning(f"⚠️  Não foi possível remover log: {arquivo.name} - {e}")
    
    if removidos > 0:
        logger.info(f"✅ Limpeza de logs: {removidos} arquivo(s) removido(s)")
    
    return removidos

def executar_rotina():
    etapas = []
    try:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Iniciando execução em {data_atual}")
        etapas.append(f"Execução iniciada em {data_atual}")
        
        # 🔧 NOVO (Fase 10): Limpar logs da execução anterior
        logger.info("\n" + "=" * 70)
        logger.info("🧹 LIMPEZA PRÉ-EXECUÇÃO")
        logger.info("=" * 70)
        limpar_logs()
        
        # Limpa a pasta de screenshots
        screenshots_dir = Path('element_screenshots')
        if screenshots_dir.exists():
            for arquivo in screenshots_dir.glob('*'):
                try:
                    arquivo.unlink()
                    logger.info(f"Screenshot removido: {arquivo.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível remover screenshot: {arquivo.name} - {e}")
        
        # Limpeza robusta da pasta Downloads antes de qualquer novo download
        removidos = limpar_arquivos_antigos_downloads()
        logger.info(f"Limpeza inicial de Downloads: {removidos} arquivo(s) removidos")
        
        # ========== FASE 1: DOWNLOADS ==========
        logger.info("\n" + "=" * 70)
        logger.info("📥 FASE 1: Baixando todos os arquivos...")
        logger.info("=" * 70)
        
        etapas.append("Driver iniciado")
        driver = iniciar_driver()
        etapas.append("Login realizado")
        login(driver)
        
        # Abrir sidebar
        abrir_sidebar(driver)
        etapas.append("Sidebar aberto")
        
        # Exportação Atividades Status
        data_atual_dt = datetime.now()
        data_90_dias_atras = data_atual_dt - timedelta(days=90)
        data_inicial_atividades = data_90_dias_atras.strftime("%d/%m/%Y")
        etapas.append(f"Exportação Atividades Status (data inicial: {data_inicial_atividades})")
        logger.info("\n[1/3] Baixando Status de Atividades...")
        exportAtividadesStatus(driver)
        time.sleep(10)
        logger.info("✅ Status de Atividades baixado!")
        
        # Abrir sidebar
        abrir_sidebar(driver)
        
        # Exportação Atividades
        etapas.append(f"Exportação Atividades (data inicial: {data_inicial_atividades})")
        logger.info("\n[2/3] Baixando Atividades...")
        exportAtividades(driver)
        time.sleep(10)
        logger.info("✅ Atividades baixado!")
        
        # Abrir sidebar
        abrir_sidebar(driver)
        
        # Exportação Produção
        data_90_dias_atras_producao = data_atual_dt - timedelta(days=92)
        data_inicial_ajustada = data_90_dias_atras_producao.replace(day=1)
        data_inicial_producao = data_inicial_ajustada.strftime("%d/%m/%Y")
        etapas.append(f"Exportação Produção (data inicial: {data_inicial_producao})")
        logger.info("\n[3/3] Baixando Produção...")
        exportProducao(driver)
        logger.info("✅ Produção baixado!")
        
        # Fechar driver após todos os downloads
        driver.quit()
        etapas.append("Driver finalizado")
        time.sleep(5)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ FASE 1 CONCLUÍDA: Todos os arquivos foram baixados!")
        logger.info("=" * 70)
        
        logger.info(f"Arquivos em: {DOWNLOADS_DIR}")
        if os.path.exists(DOWNLOADS_DIR):
            arquivos = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.xlsx')]
            logger.info(f"Total de arquivos: {len(arquivos)}")
            for arq in sorted(arquivos):
                tamanho = os.path.getsize(os.path.join(DOWNLOADS_DIR, arq)) / 1024
                logger.info(f"   📄 {arq} ({tamanho:.1f} KB)")
        
        # ========== FASE 2: PROCESSAMENTO E ENVIO ==========
        etapas.append("Iniciando processamento de arquivos")
        resultado_processamento = processar_arquivos_baixados()
        
        # Verificar se resultado não é None antes de acessar
        if resultado_processamento and resultado_processamento.get('sucesso', 0) > 0:
            logger.info(f"\n✅ {resultado_processamento['sucesso']} arquivo(s) processado(s) com sucesso!")
            logger.info(f"   Registros enviados: {resultado_processamento.get('registros_sucesso', 0)}")
        if resultado_processamento and resultado_processamento.get('erro', 0) > 0:
            logger.warning(f"⚠️ {resultado_processamento['erro']} arquivo(s) com erro durante processamento")
            logger.warning(f"   Registros falhados: {resultado_processamento.get('registros_erro', 0)}")
        
        etapas.append("Arquivos processados e enviados ao banco")
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"\nFinalizado em {data_atual}")
        etapas.append(f"Finalizado em {data_atual}")
        logger.info("Agendando a execução a cada 30 minutos...")
        
    except Exception as e:
        etapas.append(f"Erro: {e}")
        logger.error(f"Erro: {e}")
        # Não tratar erros de arquivo em uso como críticos
        if "WinError 32" in str(e) and "já está sendo usado por outro processo" in str(e):
            logger.warning(f"Arquivo em uso detectado: {e}")
            logger.warning("Este erro não é crítico e o fluxo continuará normalmente.")
        else:
            send_notification(f"Erro crítico na execução: {e}")
    finally:
        print("\nResumo das etapas executadas:")
        for etapa in etapas:
            print(f"- {etapa}")

# Função para agendar a execução
def agendar_execucao():
    schedule.every(30).minutes.do(executar_rotina)


if __name__ == '__main__':
    # Iniciar o agendamento apenas quando executado como script
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