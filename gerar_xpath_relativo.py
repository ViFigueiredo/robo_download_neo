import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

def convert_absolute_to_relative(xpath):
    """Converte XPath absoluto para relativo."""
    if xpath.startswith('/html'):
        # Remove /html/body e começa com //
        xpath = xpath.replace('/html/body', '')
        if not xpath.startswith('//'):
            xpath = '//' + xpath.lstrip('/')
    return xpath

def get_best_selector(element):
    """Gera o melhor seletor relativo para um elemento."""
    tag = element.tag_name
    
    # Tenta id
    id_attr = element.get_attribute('id')
    if id_attr and id_attr.strip():
        return f"//{tag}[@id='{id_attr}']"
    
    # Tenta name
    name_attr = element.get_attribute('name')
    if name_attr and name_attr.strip():
        return f"//{tag}[@name='{name_attr}']"
    
    # Tenta texto visível (para botões, spans, etc.)
    text = element.text.strip()
    if text and tag in ['button', 'span', 'a', 'vaadin-button']:
        return f"//{tag}[normalize-space(text())='{text}']"
    
    # Tenta classe (se for significativa)
    class_attr = element.get_attribute('class')
    if class_attr and class_attr.strip():
        classes = class_attr.split()
        if len(classes) > 0:
            # Usa a primeira classe mais significativa
            main_class = classes[0]
            return f"//{tag}[contains(@class, '{main_class}')]"
    
    # Tenta title ou placeholder
    title = element.get_attribute('title')
    if title and title.strip():
        return f"//{tag}[@title='{title}']"
    
    placeholder = element.get_attribute('placeholder')
    if placeholder and placeholder.strip():
        return f"//{tag}[@placeholder='{placeholder}']"
    
    # Fallback: tag relativa com posição
    parent = element.find_element(By.XPATH, '..')
    parent_tag = parent.tag_name
    try:
        siblings = parent.find_elements(By.XPATH, f'./{tag}')
        position = siblings.index(element) + 1
        return f"//{parent_tag}//{tag}[{position}]"
    except:
        pass
    
    # Último recurso: tag sozinha
    return f"//{tag}"

def process_map_json_with_selenium(map_json, driver):
    new_map = {}
    for section, fields in map_json.items():
        new_map[section] = {}
        for key, xpath in fields.items():
            try:
                # Primeiro tenta converter se for absoluto
                xpath_convertido = convert_absolute_to_relative(xpath)
                
                if isinstance(xpath, list):
                    selectors = []
                    for x in xpath:
                        try:
                            x_convertido = convert_absolute_to_relative(x)
                            el = driver.find_element(By.XPATH, x_convertido)
                            selectors.append(get_best_selector(el))
                        except Exception as e:
                            print(f"Erro ao processar lista {section}.{key}: {e}")
                            selectors.append(x)
                    new_map[section][key] = selectors
                else:
                    try:
                        # Tenta com o XPath convertido
                        el = driver.find_element(By.XPATH, xpath_convertido)
                        new_map[section][key] = get_best_selector(el)
                    except:
                        # Se não encontrar, tenta com o original
                        el = driver.find_element(By.XPATH, xpath)
                        new_map[section][key] = get_best_selector(el)
            except Exception as e:
                print(f"Erro ao processar {section}.{key}: {e}")
                # Fallback: converte o XPath original
                new_map[section][key] = convert_absolute_to_relative(xpath)
    return new_map

# --- CONFIGURAÇÃO ---
URL = "https://neo.solucoes.plus/home"  # Exemplo: "http://localhost:8080"
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