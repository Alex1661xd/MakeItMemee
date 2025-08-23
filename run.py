from app import create_app
import sys
import os

# Crear la aplicación
app = create_app()

if __name__ == '__main__':
    # Configuración para desarrollo local
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    host = '127.0.0.1'  # Localhost para desarrollo
    
    print(f"🚀 Iniciando Make It Meme en modo desarrollo")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    
    # Intentar ejecutar con SocketIO, si falla usar Flask normal
    try:
        from extensions import socketio
        if socketio:
            print("✅ Ejecutando con SocketIO")
            socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        else:
            raise ImportError("SocketIO no disponible")
    except Exception as e:
        print(f"⚠️ SocketIO no disponible ({e}), ejecutando con Flask normal")
        app.run(host=host, port=port, debug=debug)
