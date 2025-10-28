import sys
import os
from pathlib import Path
import json

# Garantir diretório raiz no sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importamos a função do módulo app
from app import post_records_to_nocodb

# Registro de exemplo que funcionou no Postman
test_record = {
    "GRUPO": "Vendas Corporativas",
    "FILA": "Atendimento Empresarial",
    "NUMERO ATIVIDADE": "ATV-20251022-001",
    "PEDIDO VINCULO": "PED-874562",
    "COTAÇÃO": "COT-55698",
    "ATIVIDADE ORIGEM": "Prospecção Comercial",
    "CODIGO PORTABILIDADE": "PORT1234567",
    "LOGIN OPERADORA": "vinifigueiredo",
    "NOME CLIENTE": "Empresa Alfa Tecnologia Ltda",
    "CPF/CNPJ": "12.345.678/0001-90",
    "PF OU PJ": "PJ",
    "CIDADE CLIENTE": "São Paulo",
    "ESTADO": "SP",
    "DDD": "11",
    "PROPRIETÁRIO DO PEDIDO": "João Mendes",
    "TAGS USUARIO PEDIDO": "cliente_pj, alta_prioridade, portabilidade",
    "ADM DO PEDIDO": "Maria Souza",
    "CONSULTOR NA OPERADORA": "Carlos Ribeiro",
    "EQUIPE": "Equipe B2B Leste",
    "ETAPA PEDIDO": "Em análise técnica",
    "CATEGORIA": "Internet Dedicada",
    "SUB-CATEGORIA": "Fibra Corporativa 100MB",
    "CADASTRO": "2025-10-20 10:30:00",
    "ATUALIZACAO": "2025-10-22 13:45:00",
    "SOLICITACAO": "2025-10-21 08:00:00",
    "TIPO NEGOCIACAO": "Portabilidade com upgrade",
    "NOTAS FISCAIS": "NF-125879, NF-125880",
    "REVISAO": "1.2",
    "ATIVIDADES": "Instalação de Fibra",
    "ITEM": "Link Dedicado",
    "NUMERO": "AT-001",
    "NUMERO PROVISORIO": "999991234",
    "ETAPA ITEM": "Agendado",
    "PORTABILIDADE": "Sim",
    "OPERADORA CEDENTE": "Vivo",
    "NOME CEDENTE": "José Lima",
    "CPF CNPJ CEDENTE": "123.456.789-00",
    "TELEFONE CEDENTE": "(11) 98877-6655",
    "EMAIL CEDENTE": "jose.lima@vivo.com.br",
    "PRODUTO": "Link Dedicado 100MB",
    "VALOR UNIT": "1499.90",
    "QUANTIDADE": "1",
    "DATA REF": "2025-10-21",
    "ORIGEM": "CRM Corporativo",
    "DATA INSTALAÇÃO": "2025-10-25",
    "PERIODO": "Manhã",
    "CIDADE INSTALAÇÃO": "São Paulo",
    "UF": "SP",
    "RPON": "RPN-5412",
    "INSTANCIA": "SP01",
    "TAGS": "fibra, corporativo, instalacao"
}

print("Iniciando teste com registro único...")
print(f"Registro de teste:\n{json.dumps(test_record, indent=2, ensure_ascii=False)}")

# Enviar apenas um registro
try:
    result = post_records_to_nocodb([test_record])
    print('\nEnvio finalizado. Verifique logs/sent_records.jsonl e robo_download.log')
    if isinstance(result, dict):
        print('Resumo:')
        print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f'Erro ao executar post_records_to_nocodb: {e}')
    raise