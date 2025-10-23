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

# Carrega os XPaths do arquivo map_relative.json (XPaths relativos mais robustos)
with open('map_relative.json', 'r') as f:
    XPATHS = json.load(f)

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
        # Tentar atualizar a referência do elemento se ele estiver stale
        if referencia_map and hasattr(elemento, 'find_element'):
            try:
                elemento.is_displayed()  # Testa se o elemento está stale
            except:
                # Se estiver stale, tenta encontrar o elemento novamente usando o xpath original
                xpath = XPATHS
                for key in referencia_map.split('.'):
                    xpath = xpath[key]
                elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
        
        driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
        time.sleep(0.5)  # Pequena pausa para garantir que o elemento está visível
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
    # Limpa arquivos antigos semelhantes antes de iniciar um novo download
    limpar_arquivos_antigos_downloads()
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

    # Após baixar, processar o arquivo e enviar para a API NocoDB
    try:
        # Determinar qual tabela usar baseado no nome do arquivo
        is_status = 'status' in nome_arquivo.lower()
        table_url_env = 'URL_TABELA_ATIVIDADES_STATUS' if is_status else 'URL_TABELA_ATIVIDADES'
        table_url = os.getenv(table_url_env)
        table_name = 'atividades_status' if is_status else 'atividades'
        
        if not table_url:
            logger.warning(f"Variável {table_url_env} não configurada no .env. Pulando envio para {table_name}.")
            return
        
        records = parse_export_producao(caminho_destino)
        if records:
            inicio = time.time()
            stats = post_records_to_nocodb(records, table_url=table_url, table_name=table_name)
            duracao = time.time() - inicio
            registrar_resumo_envio(table_name, caminho_destino, stats, duracao)
    except Exception as e:
        logger.error(f"Erro ao processar/enviar {nome_arquivo}: {e}")

def realizar_download_producao(driver):
    logger.info("Realizando download de produção...")
    # Limpa arquivos antigos semelhantes antes de iniciar um novo download
    limpar_arquivos_antigos_downloads()
    esperar_elemento(driver, XPATHS['producao']['download_link'], 'producao.download_link', 300)
    elemento_download = esperar_download_pronto(driver, XPATHS['producao']['download_link'], 'producao.download_link')
    url_download = elemento_download.get_attribute('href')
    nome_arquivo = elemento_download.text.strip() or 'ExportacaoProducao.xlsx'
    user_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    caminho_destino = os.path.join(user_download_dir, nome_arquivo)
    baixar_arquivo_com_cookies(driver, url_download, caminho_destino)
    clicar_elemento(driver, XPATHS['producao']['close_button'], 'producao.close_button')
    logger.info("Produção baixado com sucesso.")

    # Após baixar, processar o arquivo e enviar para a API NocoDB
    try:
        records = parse_export_producao(caminho_destino)
        if records:
            inicio = time.time()
            stats = post_records_to_nocodb(records)
            duracao = time.time() - inicio
            registrar_resumo_envio('producao', caminho_destino, stats, duracao)
    except Exception as e:
        logger.error(f"Erro ao processar/enviar ExportacaoProducao.xlsx: {e}")

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


# Utilitário: limpeza robusta da pasta de Downloads antes de iniciar cada download
def limpar_arquivos_antigos_downloads(palavras=None, padroes_regex=None, extensoes=(".xlsx",)):
    """Remove arquivos antigos na pasta Downloads que combinem com palavras-chave ou padrões.

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

    downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
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
                    logger.info(f"Arquivo antigo removido da Downloads: {nome}")
                except PermissionError as e:
                    logger.warning(f"⚠️ Não foi possível remover (em uso): {nome} - {e}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao remover arquivo antigo: {nome} - {e}")
    except FileNotFoundError:
        os.makedirs(downloads, exist_ok=True)
    except Exception as e:
        logger.warning(f"⚠️ Erro ao varrer Downloads: {e}")

    if removidos:
        logger.info(f"Limpeza de Downloads concluída: {removidos} arquivo(s) removido(s)")
    else:
        logger.info("Limpeza de Downloads: nenhum arquivo alvo encontrado")
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
    """Parse flexível usando pandas: suporta diferentes planilhas mapeadas em `nocodb_map.json`.

    Melhorias:
    - Normaliza cabeçalhos (remove acentos, pontuação, lower) e faz matching tolerante com o mapeamento
    - Tenta converter strings que parecem datas para formato `%Y-%m-%d %H:%M:%S`
    - Mantém concatenação de colunas extras em `TAGS`
    """
    import pandas as pd
    import unicodedata

    nocodb_map_file = 'nocodb_map.json'
    if not os.path.exists(nocodb_map_file):
        raise FileNotFoundError(f"Arquivo de mapeamento não encontrado: {nocodb_map_file}")

    with open(nocodb_map_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    base_name = os.path.basename(file_path)
    expected_headers = mapping.get(base_name, [])
    if not expected_headers:
        logger.warning(f"Nenhum mapeamento encontrado em {nocodb_map_file} para {base_name}")

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

    # Preparar mapeamento tolerante entre cabeçalhos esperados e colunas reais
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
            if not val_str:
                return ""
            try:
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
    for _, row in df.iterrows():
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

        records.append(rec)

    logger.info(f"Parsed {len(records)} registros de {file_path} (pandas, flex) usando mapeamento {base_name}")
    return records

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

def executar_rotina():
    etapas = []
    try:
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Iniciando execução em {data_atual}")
        etapas.append(f"Execução iniciada em {data_atual}")
        
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
        exportAtividadesStatus(driver)
        time.sleep(10)
        # Abrir sidebar
        abrir_sidebar(driver)
        # Exportação Atividades
        etapas.append(f"Exportação Atividades (data inicial: {data_inicial_atividades})")
        exportAtividades(driver)
        time.sleep(10)
        # Abrir sidebar
        abrir_sidebar(driver)
        # Exportação Produção
        data_90_dias_atras_producao = data_atual_dt - timedelta(days=92)
        data_inicial_ajustada = data_90_dias_atras_producao.replace(day=1)
        data_inicial_producao = data_inicial_ajustada.strftime("%d/%m/%Y")
        etapas.append(f"Exportação Produção (data inicial: {data_inicial_producao})")
        exportProducao(driver)
        driver.quit()
        etapas.append("Driver finalizado")
        time.sleep(10)
        # Conforme solicitado, NÃO mover arquivos baixados para outro diretório.
        # Os arquivos permanecerão na pasta de Downloads do usuário.
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        logger.info(f"Arquivos baixados permanecerão em: {downloads_dir}")
        etapas.append("Arquivos processados")
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Finalizado em {data_atual}")
        etapas.append(f"Finalizado em {data_atual}")
        logger.info("⏳ Agendando a execução a cada 30 minutos...")
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