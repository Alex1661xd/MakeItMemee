from flask import Flask, redirect, url_for, session, render_template
from flask_migrate import Migrate
from config import Config
from models import db, User
import os

# Importar SocketIO de manera segura
try:
    from extensions import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("⚠️ SocketIO no disponible, continuando sin funcionalidad en tiempo real")
    SOCKETIO_AVAILABLE = False
    socketio = None

from blueprints.auth.routes import auth_bp
from blueprints.game.routes import game_bp
from blueprints.admin.routes import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask-Migrate
    migrate = Migrate()

    # Inicializar base de datos y migraciones
    db.init_app(app)
    migrate.init_app(app, db)

    # Configurar la clave secreta para las sesiones
    app.secret_key = Config.SECRET_KEY
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(game_bp, url_prefix="/game")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def index():
        if "user_id" not in session:
            return redirect(url_for('auth.show_nickname_form'))
        # Obtener el usuario actual
        user = User.query.get(session["user_id"])
        if not user:
            # Si el usuario no existe, limpiar la sesión y redirigir
            session.clear()
            return redirect(url_for('auth.show_nickname_form'))
        
        # Verificar si el usuario está en un juego terminado y limpiarlo
        if user.game_id:
            from models import Game
            game = Game.query.get(user.game_id)
            if game and game.status in ['finished', 'completed']:
                user.game_id = None
                db.session.commit()
        
        return render_template("index.html", nickname=user.nickname)

    # Configurar Socket.IO solo si está disponible
    if SOCKETIO_AVAILABLE and socketio:
        socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
        print("✅ SocketIO configurado en la aplicación")
    else:
        print("ℹ️ Aplicación ejecutándose sin SocketIO")

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Crear todas las tablas si no existen
        db.create_all()
        print("✅ Base de datos inicializada")
    
    # Configuración para desarrollo local
    debug = os.environ.get('FLASK_ENV') == 'development' or True
    host = '127.0.0.1'  # Localhost para desarrollo
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Iniciando Make It Meme en http://{host}:{port}")
    print(f"🔧 Modo debug: {debug}")
    
    if SOCKETIO_AVAILABLE and socketio:
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        app.run(host=host, port=port, debug=debug)
