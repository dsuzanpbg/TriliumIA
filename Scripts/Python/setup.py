#!/usr/bin/env python3
"""
========================================
SETUP SCRIPT - Configurar entorno virtual
Compatible con Windows y Linux
========================================

Uso:
    python setup.py          # Crear venv e instalar dependencias
    python setup.py install # Igual a arriba
    python setup.py clean  # Eliminar venv
    python setup.py deps   # Solo instalar dependencias
========================================
"""

import os
import sys
import subprocess
import shutil
import platform

# ========================================
# CONFIGURACION
# ========================================

VENV_NAME = "venv"
REQUIREMENTS = [
    "requests>=2.28.0",
]

# ========================================
# DETECTAR SISTEMA OPERATIVO
# ========================================

def get_system():
    """Detectar sistema operativo"""
    return platform.system().lower()

def is_windows():
    return get_system() == "windows"

def is_linux():
    return get_system() == "linux"

def is_macos():
    return get_system() == "darwin"

# ========================================
# COMANDOS
# ========================================

def get_python_executable():
    """Obtener el ejecutable de Python"""
    if is_windows():
        return os.path.join(VENV_NAME, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_NAME, "bin", "python")

def get_pip_executable():
    """Obtener el ejecutable de pip"""
    if is_windows():
        return os.path.join(VENV_NAME, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_NAME, "bin", "pip")

def create_venv():
    """Crear entorno virtual"""
    print("="*50)
    print("Creando entorno virtual...")
    print("="*50)
    
    # Verificar si ya existe
    if os.path.exists(VENV_NAME):
        print(f"El entorno '{VENV_NAME}' ya existe.")
        respuesta = input("Deseas eliminarlo y crear uno nuevo? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'y', 'yes']:
            shutil.rmtree(VENV_NAME)
            print("Entorno anterior eliminado.")
        else:
            print("Usando el entorno existente.")
            return False
    
    # Crear venv
    print(f"Sistema: {platform.system()}")
    print(f"Python executable: {sys.executable}")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_NAME], check=True)
        print(f"Entorno virtual '{VENV_NAME}' creado exitosamente.")
        return True
    except Exception as e:
        print(f"Error al crear el entorno virtual: {e}")
        return False

def install_dependencies():
    """Instalar dependencias en el venv"""
    print("\n" + "="*50)
    print("Instalando dependencias...")
    print("="*50)
    
    pip = get_pip_executable()
    
    # Actualizar pip
    print("Actualizando pip...")
    subprocess.run([pip, "install", "--upgrade", "pip"], check=False)
    
    # Instalar requirements
    for req in REQUIREMENTS:
        print(f"Instalando {req}...")
        subprocess.run([pip, "install", req], check=True)
    
    print("\nDependencias instaladas.")

def install_dependencies_system():
    """Instalar dependencias en el sistema (sin venv)"""
    print("\n" + "="*50)
    print("Instalando dependencias en el sistema...")
    print("="*50)
    
    for req in REQUIREMENTS:
        print(f"Instalando {req}...")
        subprocess.run([sys.executable, "-m", "pip", "install", req], check=True)
    
    print("\nDependencias instaladas en el sistema.")

def clean_venv():
    """Eliminar entorno virtual"""
    if os.path.exists(VENV_NAME):
        shutil.rmtree(VENV_NAME)
        print(f"Entorno virtual '{VENV_NAME}' eliminado.")
    else:
        print(f"El entorno '{VENV_NAME}' no existe.")

def create_requirements_file():
    """Crear archivo requirements.txt"""
    with open("requirements.txt", "w") as f:
        f.write("# Requirements for PBG Scripts\n")
        f.write("# Install with: pip install -r requirements.txt\n\n")
        for req in REQUIREMENTS:
            f.write(req + "\n")
    print("Archivo requirements.txt creado.")

def create_launcher_scripts():
    """Crear scripts de lanzamiento para Windows y Linux"""
    
    # Script para Linux/Mac
    if not is_windows():
        launcher = """#!/bin/bash
# Lanzador para ejecutar scripts de Python
# Uso: ./run.sh script.py [argumentos]

SCRIPT=$1
shift

if [ -z "$SCRIPT" ]; then
    echo "Uso: ./run.sh script.py [argumentos]"
    exit 1
fi

# Activar venv si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar script
python3 "$SCRIPT" "$@"
"""
        with open("run.sh", "w") as f:
            f.write(launcher)
        os.chmod("run.sh", 0o755)
        print("Script 'run.sh' creado.")
    
    # Script para Windows
    if is_windows() or os.name == 'nt':
        launcher = """@echo off
REM Lanzador para ejecutar scripts de Python
REM Uso: run.bat script.py [argumentos]

set SCRIPT=%1
shift

if "%SCRIPT%"=="" (
    echo Uso: run.bat script.py [argumentos]
    exit /b 1
)

REM Activar venv si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Ejecutar script
python "%SCRIPT%" %*
"""
        with open("run.bat", "w") as f:
            f.write(launcher)
        print("Script 'run.bat' creado.")

def print_help():
    """Mostrar ayuda"""
    print("""
========================================
COMANDOS DISPONIBLES
========================================

python setup.py          - Crear venv e instalar deps
python setup.py install - Igual que arriba
python setup.py clean   - Eliminar venv
python setup.py deps    - Solo instalar dependencias
python setup.py system  - Instalar en el sistema (sin venv)
python setup.py init    - Crear archivos de configuracion

========================================
ENTORNOS COMPATIBLES
========================================

- Windows (10/11)
- Linux (Ubuntu, Debian, CentOS, etc.)
- macOS

========================================
USO
========================================

1. Crear entorno virtual:
   python setup.py install

2. Ejecutar scripts:
   Linux/Mac:   ./run.sh Scripts/Python/yaml_to_asana.py --dry-run
   Windows:     run.bat Scripts\\Python\\yaml_to_asana.py --dry-run

3. Activar manualmente:
   Linux/Mac:   source venv/bin/activate
   Windows:     venv\\Scripts\\activate

========================================
""")

# ========================================
# MAIN
# ========================================

def main():
    if len(sys.argv) < 2:
        # Por defecto, crear e instalar
        create_requirements_file()
        create_launcher_scripts()
        
        if create_venv():
            install_dependencies()
        
        print("\n" + "="*50)
        print("CONFIGURACION COMPLETA")
        print("="*50)
        print(f"\nSistema: {platform.system()}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Entorno: {VENV_NAME}/")
        print("\nPara ejecutar scripts:")
        if is_windows():
            print("  run.bat Scripts\\Python\\yaml_to_asana.py --dry-run")
        else:
            print("  ./run.sh Scripts/Python/yaml_to_asana.py --dry-run")
        return
    
    command = sys.argv[1].lower()
    
    if command in ["install", "i"]:
        create_requirements_file()
        create_launcher_scripts()
        if create_venv():
            install_dependencies()
            
    elif command in ["clean", "c"]:
        clean_venv()
        
    elif command in ["deps", "d"]:
        install_dependencies()
        
    elif command in ["system", "s"]:
        install_dependencies_system()
        
    elif command in ["init"]:
        create_requirements_file()
        create_launcher_scripts()
        
    elif command in ["help", "h", "-h", "--help"]:
        print_help()
        
    else:
        print(f"Comando desconocido: {command}")
        print_help()


if __name__ == "__main__":
    main()
