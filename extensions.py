from flask_socketio import SocketIO
import os

# Configuración simple de SocketIO para desarrollo local
try:
    socketio = SocketIO(
        async_mode='threading', 
        logger=True,  # Habilitar logs en desarrollo
        engineio_logger=True,  # Habilitar logs de Engine.IO en desarrollo
        cors_allowed_origins="*"
    )
    print("🚀 SocketIO configurado en modo local (desarrollo)")
except Exception as e:
    print(f"⚠️ Error configurando SocketIO: {e}")
    print("🔧 Continuando sin SocketIO...")
    socketio = None
