#!/usr/bin/env python3
"""
Validador de Build - robo_neo.exe

Este script valida se o .exe foi compilado corretamente e se está
pronto para distribuição.

Uso:
  python scripts/validar_build.py
"""

import os
import sys
from pathlib import Path

def validar_build():
    """Valida se a build está completa e correta."""
    
    print("\n" + "="*70)
    print("🔍 VALIDADOR DE BUILD - robo_neo.exe")
    print("="*70 + "\n")
    
    erros = []
    avisos = []
    sucessos = []
    
    # Obter diretório raiz do projeto
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    exe_path = root_dir / "dist" / "robo_neo.exe"
    env_path = root_dir / ".env"
    
    # 1. Verificar .exe
    print("[1/6] Verificando arquivo .exe...")
    if exe_path.exists():
        tamanho = exe_path.stat().st_size
        tamanho_mb = tamanho / (1024 * 1024)
        sucessos.append(f"✅ robo_neo.exe encontrado ({tamanho_mb:.1f} MB)")
        print(f"  ✅ Arquivo encontrado: {exe_path}")
        print(f"  📊 Tamanho: {tamanho_mb:.1f} MB ({tamanho:,} bytes)")
        
        if tamanho < 10_000_000:  # Menor que 10 MB
            avisos.append("⚠️ Arquivo .exe parece muito pequeno (< 10 MB)")
            print(f"  ⚠️ AVISO: Arquivo parece pequeno demais")
        elif tamanho > 100_000_000:  # Maior que 100 MB
            avisos.append("⚠️ Arquivo .exe muito grande (> 100 MB)")
            print(f"  ⚠️ AVISO: Arquivo parece muito grande")
    else:
        erros.append(f"❌ robo_neo.exe não encontrado em {exe_path}")
        print(f"  ❌ Arquivo não encontrado: {exe_path}")
    
    # 2. Verificar config_embutida.py
    print("\n[2/6] Verificando scripts...")
    config_py = script_dir / "config_embutida.py"
    robo_spec = script_dir / "robo_neo.spec"
    
    if config_py.exists():
        sucessos.append("✅ config_embutida.py encontrado")
        print(f"  ✅ {config_py.name} OK")
    else:
        erros.append(f"❌ config_embutida.py não encontrado")
        print(f"  ❌ {config_py.name} FALTANDO")
    
    if robo_spec.exists():
        sucessos.append("✅ robo_neo.spec encontrado")
        print(f"  ✅ {robo_spec.name} OK")
    else:
        erros.append(f"❌ robo_neo.spec não encontrado")
        print(f"  ❌ {robo_spec.name} FALTANDO")
    
    # 3. Verificar app.py
    print("\n[3/6] Verificando app.py...")
    app_py = root_dir / "app.py"
    if app_py.exists():
        sucessos.append("✅ app.py encontrado")
        print(f"  ✅ app.py OK")
    else:
        erros.append("❌ app.py não encontrado")
        print(f"  ❌ app.py FALTANDO")
    
    # 4. Verificar .env
    print("\n[4/6] Verificando .env...")
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                linhas = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith('#')]
            sucessos.append(f"✅ .env encontrado ({len(linhas)} variáveis)")
            print(f"  ✅ .env OK")
            print(f"  📊 {len(linhas)} variáveis configuradas")
            
            # Verificar variáveis críticas
            env_content = env_path.read_text()
            vars_criticas = ['SYS_URL', 'SYS_USERNAME', 'SYS_PASSWORD', 'DB_SERVER', 'DB_DATABASE']
            for var in vars_criticas:
                if var in env_content:
                    print(f"     ✅ {var}")
                else:
                    avisos.append(f"⚠️ Variável crítica faltando: {var}")
                    print(f"     ⚠️ {var} FALTANDO")
        except Exception as e:
            avisos.append(f"⚠️ Erro ao ler .env: {e}")
            print(f"  ⚠️ Erro ao ler .env: {e}")
    else:
        avisos.append("⚠️ .env não encontrado - será necessário para executar o .exe")
        print(f"  ⚠️ .env não encontrado")
        print(f"     (Necessário antes de executar o .exe)")
    
    # 5. Verificar estrutura de diretórios
    print("\n[5/6] Verificando estrutura...")
    dirs_esperados = {
        'dist': root_dir / 'dist',
        'scripts': script_dir,
        'bases': root_dir / 'bases',
        'logs': root_dir / 'logs',
        'downloads': root_dir / 'downloads',
        'docs': root_dir / 'docs'
    }
    
    for nome, caminho in dirs_esperados.items():
        if caminho.exists():
            sucessos.append(f"✅ Pasta {nome}/ existe")
            print(f"  ✅ {nome}/")
        else:
            avisos.append(f"⚠️ Pasta {nome}/ não existe")
            print(f"  ⚠️ {nome}/ FALTANDO")
    
    # 6. Verificar JSONs em bases/
    print("\n[6/6] Verificando JSONs...")
    bases_dir = root_dir / 'bases'
    jsons_esperados = [
        'sql_map.json',
        'map_relative.json'
    ]
    
    if bases_dir.exists():
        for json_file in jsons_esperados:
            json_path = bases_dir / json_file
            if json_path.exists():
                sucessos.append(f"✅ {json_file}")
                print(f"  ✅ {json_file}")
            else:
                avisos.append(f"⚠️ {json_file} não encontrado em bases/")
                print(f"  ⚠️ {json_file} FALTANDO")
    else:
        erros.append("❌ Pasta bases/ não existe")
        print(f"  ❌ bases/ FALTANDO")
    
    # Resumo
    print("\n" + "="*70)
    print("📋 RESUMO DA VALIDAÇÃO")
    print("="*70)
    
    print(f"\n✅ Sucessos ({len(sucessos)}):")
    for s in sucessos:
        print(f"   {s}")
    
    if avisos:
        print(f"\n⚠️ Avisos ({len(avisos)}):")
        for a in avisos:
            print(f"   {a}")
    
    if erros:
        print(f"\n❌ Erros ({len(erros)}):")
        for e in erros:
            print(f"   {e}")
    
    # Status final
    print("\n" + "="*70)
    if not erros:
        print("🟢 STATUS: TUDO OK - PRONTO PARA USAR")
        print("="*70 + "\n")
        print("Próximas ações:")
        print("  1. Executar: robo_neo.exe")
        print("  2. OU copiar dist/robo_neo.exe para outro local")
        print("  3. Garantir que .env esteja no mesmo diretório do .exe\n")
        return 0
    else:
        print("🔴 STATUS: HÁ ERROS - RESOLVA ANTES DE USAR")
        print("="*70 + "\n")
        print("Corija os erros acima e execute: scripts\\empacotar_robo_neo.bat\n")
        return 1

if __name__ == '__main__':
    sys.exit(validar_build())
