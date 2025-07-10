import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

def get_best_selector(element):
    # Tenta id
    id_attr = element.get_attribute('id')
    if id_attr:
        return f"//*[@id='{id_attr}']"
    # Tenta name
    name_attr = element.get_attribute('name')
    if name_attr:
        return f"//*[@name='{name_attr}']"
    # Tenta texto visível (para botões, spans, etc.)
    text = element.text.strip()
    tag = element.tag_name
    if text and tag in ['button', 'span', 'a', 'vaadin-button']:
        return f"//{tag}[normalize-space(text())='{text}']"
    # Tenta classe (se for única)
    class_attr = element.get_attribute('class')
    if class_attr and len(class_attr.split()) == 1:
        return f"//{tag}[@class='{class_attr}']"
    # Fallback: só a tag
    return f"//{tag}"

def process_map_json_with_selenium(map_json, driver):
    new_map = {}
    for section, fields in map_json.items():
        new_map[section] = {}
        for key, xpath in fields.items():
            try:
                if isinstance(xpath, list):
                    selectors = []
                    for x in xpath:
                        el = driver.find_element(By.XPATH, x)
                        selectors.append(get_best_selector(el))
                    new_map[section][key] = selectors
                else:
                    el = driver.find_element(By.XPATH, xpath)
                    new_map[section][key] = get_best_selector(el)
            except Exception as e:
                print(f"Erro ao processar {section}.{key}: {e}")
                new_map[section][key] = xpath  # fallback para o original
    return new_map

# --- CONFIGURAÇÃO ---
URL = "https://app.neocrm.com.br/home"  # Exemplo: "http://localhost:8080"
# --------------------

# Carrega o map.json
with open('map.json', 'r', encoding='utf-8') as f:
    map_json = json.load(f)

# Inicia o Selenium (Firefox headless)
options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.get(URL)

# Aguarde o carregamento da página se necessário (ex: time.sleep(5))

relative_map = process_map_json_with_selenium(map_json, driver)

# Salva o novo map_relative.json
with open('map_relative.json', 'w', encoding='utf-8') as f:
    json.dump(relative_map, f, indent=4, ensure_ascii=False)

driver.quit()
print("Arquivo map_relative.json gerado com seletores inteligentes via Selenium!")