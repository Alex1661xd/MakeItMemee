#!/usr/bin/env python3
"""
Script para recrear la base de datos después de cambios en los modelos.
¡ATENCIÓN! Esto eliminará TODOS los datos existentes.
"""

import os
import sys

# Agregar el directorio actual al path para importar la aplicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar al nivel del módulo
try:
    from app import create_app
    from models import db, User, Game, MemeTemplate, PlayerTemplate, Vote
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("💡 Asegúrate de que la aplicación esté configurada correctamente")
    sys.exit(1)

def recreate_database():
    """Recrea la base de datos eliminando todas las tablas y creándolas de nuevo."""
    
    try:
        # Crear la aplicación usando la factory function
        app = create_app()
        
        with app.app_context():
            print("🗑️  Eliminando tablas existentes...")
            db.drop_all()
            print("✅ Tablas eliminadas")
            
            print("🏗️  Creando nuevas tablas...")
            db.create_all()
            print("✅ Tablas creadas")
            
            print("\n🎉 ¡Base de datos recreada exitosamente!")
            print("📋 Tablas creadas:")
            
            # Mostrar las tablas creadas
            inspector = db.inspect(db.engine)
            for table_name in inspector.get_table_names():
                print(f"   - {table_name}")
                
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando recreación de base de datos...")
    print("⚠️  ¡ATENCIÓN! Se eliminarán TODOS los datos existentes!")
    
    # Confirmación del usuario
    response = input("\n¿Estás seguro de que quieres continuar? (sí/no): ").lower().strip()
    
    if response in ['sí', 'si', 's', 'yes', 'y']:
        success = recreate_database()
        if success:
            print("\n🎯 Base de datos lista para usar!")
        else:
            print("\n💥 Algo salió mal. Revisa los errores arriba.")
    else:
        print("❌ Operación cancelada por el usuario.")
