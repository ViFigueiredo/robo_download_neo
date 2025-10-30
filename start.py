#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 START.PY - Menu Interativo do Robô Neo

Interface amigável para o usuário selecionar e executar operações:
1. Mapear planilhas (gerar_sql_map_automatico.py)
2. Gerar modelos SQL (gerar_models_dinamicos.py)
3. Migrar banco de dados (migrate_tables.py)
4. Sincronizar banco de dados (sincronizar_schema.py)
5. Iniciar aplicação (app.py)

Desenvolvido em: October 2025
Versão: 1.0
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Limpa a tela do console"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Imprime o cabeçalho da aplicação"""
    clear_screen()
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "🚀 ROBÔ DE DOWNLOAD NEO - Menu Interativo".center(68) + "║")
    print("║" + " "*68 + "║")
    print("║" + f"Data: {datetime.now().strftime('%d de %B de %Y às %H:%M:%S')}".ljust(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.ENDC}\n")

def print_menu():
    """Imprime o menu principal"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}📋 Selecione uma operação:{Colors.ENDC}\n")
    
    menu_items = [
        ("1", "📊 Mapear Planilhas", "Gera sql_map.json a partir dos arquivos Excel"),
        ("2", "🔧 Gerar Modelos SQL", "Cria models_generated.py baseado em sql_map.json"),
        ("3", "🗄️  Migrar Banco de Dados", "Cria/verifica tabelas no SQL Server"),
        ("4", "🔄 Sincronizar Banco de Dados", "Sincroniza schema entre ORM e SQL Server"),
        ("5", "▶️  Iniciar Aplicação", "Executa o robô de download (app.py)"),
        ("0", "❌ Sair", "Encerra o programa"),
    ]
    
    for num, title, desc in menu_items:
        if num == "0":
            print(f"{Colors.FAIL}  [{num}] {title:<25} - {desc}{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  [{num}] {title:<25} - {desc}{Colors.ENDC}")
    
    print()

def get_choice():
    """Obtém a escolha do usuário"""
    while True:
        try:
            choice = input(f"{Colors.OKCYAN}Escolha uma opção [0-5]: {Colors.ENDC}").strip()
            if choice in ['0', '1', '2', '3', '4', '5']:
                return choice
            else:
                print(f"{Colors.FAIL}❌ Opção inválida! Digite um número de 0 a 5.{Colors.ENDC}\n")
        except KeyboardInterrupt:
            print(f"\n{Colors.FAIL}❌ Operação cancelada pelo usuário.{Colors.ENDC}\n")
            sys.exit(0)
        except Exception as e:
            print(f"{Colors.FAIL}❌ Erro ao ler entrada: {e}{Colors.ENDC}\n")

def execute_script(script_name, description):
    """Executa um script Python"""
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}▶️  Iniciando: {description}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*70}{Colors.ENDC}\n")
    
    try:
        # Verificar se o script existe
        if not Path(script_name).exists():
            print(f"{Colors.FAIL}❌ Erro: Arquivo '{script_name}' não encontrado!{Colors.ENDC}\n")
            return False
        
        # Executar script
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(__file__) or '.',
            check=False
        )
        
        # Verificar resultado
        if result.returncode == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ Operação concluída com sucesso!{Colors.ENDC}\n")
            return True
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️  Operação concluída com avisos/erros (código: {result.returncode}){Colors.ENDC}\n")
            return False
            
    except Exception as e:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Erro ao executar script: {e}{Colors.ENDC}\n")
        return False

def show_step_info(current, total, description):
    """Mostra informação do passo sendo executado"""
    print(f"\n{Colors.OKCYAN}[Passo {current}/{total}] {description}{Colors.ENDC}")

def execute_option(choice):
    """Executa a opção escolhida"""
    
    if choice == '0':
        print(f"{Colors.WARNING}\n👋 Encerrando aplicação...{Colors.ENDC}\n")
        sys.exit(0)
    
    elif choice == '1':
        print_header()
        print(f"{Colors.OKBLUE}{Colors.BOLD}📊 MAPEAR PLANILHAS{Colors.ENDC}\n")
        print("Este processo irá:")
        print("  1. Ler os arquivos Excel em 'downloads/'")
        print("  2. Detectar colunas e duplicatas")
        print("  3. Gerar ou atualizar 'bases/sql_map.json'")
        print()
        
        if execute_script('gerar_sql_map_automatico.py', 'Mapeamento de Planilhas'):
            pass
        
        input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
    
    elif choice == '2':
        print_header()
        print(f"{Colors.OKBLUE}{Colors.BOLD}🔧 GERAR MODELOS SQL{Colors.ENDC}\n")
        print("Este processo irá:")
        print("  1. Ler 'bases/sql_map.json'")
        print("  2. Gerar classes SQLAlchemy")
        print("  3. Criar 'models/models_generated.py'")
        print()
        
        if not Path('bases/sql_map.json').exists():
            print(f"{Colors.WARNING}⚠️  Aviso: 'bases/sql_map.json' não encontrado!{Colors.ENDC}")
            print(f"   Execute primeiro a opção 1 (Mapear Planilhas)\n")
            input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
            return
        
        if execute_script('gerar_models_dinamicos.py', 'Geração de Modelos'):
            pass
        
        input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
    
    elif choice == '3':
        print_header()
        print(f"{Colors.OKBLUE}{Colors.BOLD}🗄️  MIGRAR BANCO DE DADOS{Colors.ENDC}\n")
        print("Este processo irá:")
        print("  1. Conectar ao SQL Server")
        print("  2. Criar tabelas baseadas em models_generated.py")
        print("  3. Sincronizar schema automaticamente")
        print()
        
        if not Path('models/models_generated.py').exists():
            print(f"{Colors.WARNING}⚠️  Aviso: 'models/models_generated.py' não encontrado!{Colors.ENDC}")
            print(f"   Execute primeiro a opção 2 (Gerar Modelos SQL)\n")
            input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
            return
        
        if execute_script('migrate_tables.py', 'Migração de Banco de Dados'):
            pass
        
        input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
    
    elif choice == '4':
        print_header()
        print(f"{Colors.OKBLUE}{Colors.BOLD}🔄 SINCRONIZAR BANCO DE DADOS{Colors.ENDC}\n")
        print("Este processo irá:")
        print("  1. Comparar modelos ORM com tabelas SQL Server")
        print("  2. Detectar diferenças de schema")
        print("  3. Aplicar mudanças necessárias (ADD/ALTER COLUMN)")
        print()
        
        if execute_script('sincronizar_schema.py', 'Sincronização de Schema'):
            pass
        
        input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
    
    elif choice == '5':
        print_header()
        print(f"{Colors.OKBLUE}{Colors.BOLD}▶️  INICIAR APLICAÇÃO{Colors.ENDC}\n")
        print("Este processo irá:")
        print("  1. Conectar ao sistema web")
        print("  2. Realizar login com OTP")
        print("  3. Baixar relatórios")
        print("  4. Processar dados")
        print("  5. Inserir no SQL Server")
        print()
        print(f"{Colors.WARNING}⚠️  A aplicação continuará rodando até ser interrompida (Ctrl+C){Colors.ENDC}\n")
        
        response = input(f"{Colors.OKCYAN}Deseja continuar? (s/n): {Colors.ENDC}").strip().lower()
        if response != 's':
            print(f"{Colors.WARNING}Operação cancelada.{Colors.ENDC}\n")
            input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")
            return
        
        if execute_script('app.py', 'Aplicação Principal'):
            pass
        
        input(f"{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")

def show_pipeline_suggestion():
    """Mostra sugestão de pipeline para primeira execução"""
    print(f"\n{Colors.BOLD}{Colors.OKGREEN}💡 Dica: Primeira Execução?{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Execute nesta ordem:{Colors.ENDC}")
    print(f"  1️⃣  Mapear Planilhas (opção 1)")
    print(f"  2️⃣  Gerar Modelos SQL (opção 2)")
    print(f"  3️⃣  Migrar Banco de Dados (opção 3)")
    print(f"  4️⃣  Sincronizar Banco de Dados (opção 4)")
    print(f"  5️⃣  Iniciar Aplicação (opção 5)")
    print()

def show_status():
    """Mostra status dos arquivos necessários"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}📊 Status dos Arquivos:{Colors.ENDC}\n")
    
    files_to_check = [
        ('.env', 'Configurações'),
        ('bases/map_relative.json', 'Mapa de XPaths'),
        ('bases/sql_map.json', 'Mapa SQL'),
        ('models/models_generated.py', 'Modelos Gerados'),
    ]
    
    for file_path, description in files_to_check:
        status = "✅" if Path(file_path).exists() else "❌"
        print(f"  {status} {description:<25} ({file_path})")
    
    print()

def main():
    """Função principal"""
    try:
        while True:
            print_header()
            show_status()
            show_pipeline_suggestion()
            print_menu()
            
            choice = get_choice()
            
            if choice != '0':
                print_header()
            
            execute_option(choice)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.FAIL}{Colors.BOLD}❌ Aplicação interrompida pelo usuário.{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Erro inesperado: {e}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
