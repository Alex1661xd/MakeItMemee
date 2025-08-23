import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
    
    # Base de datos local (SQLite para desarrollo)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis local para desarrollo (opcional)
    REDIS_URL = os.environ.get(
        "REDIS_URL", 
        "redis://localhost:6379/0"
    )
    
    # Session configuration
    SESSION_COOKIE_NAME = "make_it_meme_session"
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas
