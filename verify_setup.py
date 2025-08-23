#!/usr/bin/env python3
"""
Script de verificación para Make It Meme
Verifica que todos los archivos de configuración estén en su lugar
"""

import os
import sys
import platform

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NO ENCONTRADO")
        return False

def check_directory_exists(dirpath, description):
    """Verifica si un directorio existe"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} - NO ENCONTRADO")
        return False

def main():
    print("🔍 Verificando configuración de Make It Meme...")
    print("=" * 50)
    
    # Detectar sistema operativo
    system = platform.system()
    print(f"🖥️ Sistema operativo detectado: {system}")
    
    # Archivos de configuración principales (siempre necesarios)
    required_files = [
        ("app.py", "Aplicación principal Flask"),
        ("config.py", "Archivo de configuración"),
        ("extensions.py", "Extensiones Flask"),
        ("models.py", "Modelos de base de datos"),
        ("run.py", "Script de ejecución"),
        ("requirements.txt", "Dependencias de Python"),
        (".gitignore", "Archivo Git ignore"),
        ("Procfile", "Configuración Heroku"),
        ("runtime.txt", "Versión de Python"),
        ("README.md", "Documentación del proyecto")
    ]
    
    # Archivos específicos del sistema operativo
    if system == "Windows":
        required_files.append(("start.ps1", "Script de inicio Windows"))
        print("📝 Verificando archivos para Windows...")
    elif system in ["Linux", "Darwin"]:  # Linux o macOS
        required_files.append(("start.sh", "Script de inicio Linux/Mac"))
        print("📝 Verificando archivos para Linux/Mac...")
    
    # Directorios requeridos
    required_dirs = [
        ("blueprints", "Paquete de blueprints"),
        ("blueprints/auth", "Blueprint de autenticación"),
        ("blueprints/game", "Blueprint del juego"),
        ("blueprints/admin", "Blueprint de administración"),
        ("migrations", "Directorio de migraciones")
    ]
    
    # Verificar archivos
    print("\n📁 Archivos de configuración:")
    files_ok = 0
    for filepath, description in required_files:
        if check_file_exists(filepath, description):
            files_ok += 1
    
    # Verificar directorios
    print("\n📂 Estructura de directorios:")
    dirs_ok = 0
    for dirpath, description in required_dirs:
        if check_directory_exists(dirpath, description):
            dirs_ok += 1
    
    # Verificar archivos __init__.py
    print("\n🔧 Archivos de inicialización:")
    init_files = [
        ("blueprints/__init__.py", "Init del paquete blueprints"),
        ("blueprints/auth/__init__.py", "Init del blueprint auth"),
        ("blueprints/game/__init__.py", "Init del blueprint game"),
        ("blueprints/admin/__init__.py", "Init del blueprint admin"),
        ("migrations/__init__.py", "Init del paquete migrations")
    ]
    
    init_ok = 0
    for filepath, description in init_files:
        if check_file_exists(filepath, description):
            init_ok += 1
    
    # Verificar archivos de rutas
    print("\n🛣️ Archivos de rutas:")
    route_files = [
        ("blueprints/auth/routes.py", "Rutas de autenticación"),
        ("blueprints/game/routes.py", "Rutas del juego"),
        ("blueprints/admin/routes.py", "Rutas de administración")
    ]
    
    routes_ok = 0
    for filepath, description in route_files:
        if check_file_exists(filepath, description):
            routes_ok += 1
    
    # Resumen
    print("\n" + "=" * 50)
    total_checks = len(required_files) + len(required_dirs) + len(init_files) + len(route_files)
    total_ok = files_ok + dirs_ok + init_ok + routes_ok
    
    print(f"📊 Resumen: {total_ok}/{total_checks} verificaciones exitosas")
    
    if total_ok == total_checks:
        print("🎉 ¡Configuración completa! El proyecto está listo para ejecutarse.")
        print("\n📝 Próximos pasos:")
        if system == "Windows":
            print("1. Crear entorno virtual: python -m venv venv")
            print("2. Activar entorno: venv\\Scripts\\activate")
            print("3. Instalar dependencias: pip install -r requirements.txt")
            print("4. Ejecutar: python run.py")
            print("5. O usar script automático: .\\start.ps1")
        else:
            print("1. Crear entorno virtual: python -m venv venv")
            print("2. Activar entorno: source venv/bin/activate")
            print("3. Instalar dependencias: pip install -r requirements.txt")
            print("4. Ejecutar: python run.py")
            print("5. O usar script automático: ./start.sh")
    else:
        print("⚠️ Algunas verificaciones fallaron. Revisa los archivos faltantes.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
