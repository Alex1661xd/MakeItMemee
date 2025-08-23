from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True, index=True)

class Game(db.Model):
    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    is_private = db.Column(db.Boolean, default=True)
    max_players = db.Column(db.Integer, default=15)
    rounds = db.Column(db.Integer, default=3)
    current_round = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    round_start_time = db.Column(db.DateTime, nullable=True)
    round_duration = db.Column(db.Integer, default=60)  # Duration in seconds
    templates_per_round = db.Column(db.Integer, default=5)
    rounds_completed = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='waiting')  # waiting, started, finished
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Definir la relación con los jugadores
    players = db.relationship('User', 
                            backref=db.backref('current_game', lazy=True),
                            foreign_keys=[User.game_id],
                            lazy=True)
    # Definir la relación con el creador
    creator = db.relationship('User',
                            backref=db.backref('created_games', lazy=True),
                            foreign_keys=[creator_id],
                            lazy=True)

class MemeTemplate(db.Model):
    __tablename__ = 'meme_template'
    id = db.Column(db.Integer, primary_key=True)
    
    # Almacenamiento de imagen
    image_path = db.Column(db.String(255), nullable=True)  # Para compatibilidad con memes existentes
    image_data = db.Column(db.Text, nullable=True)  # Base64 de la imagen comprimida
    image_filename = db.Column(db.String(255), nullable=True)  # Nombre original del archivo
    image_mimetype = db.Column(db.String(100), nullable=True)  # Tipo MIME (image/jpeg, image/png, etc.)
    
    name = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True, index=True)  # Índice para consultas de plantillas activas
    uploaded_by_user = db.Column(db.Boolean, default=False)
    
    # Número de cajas de texto activas (1-5)
    num_text_boxes = db.Column(db.Integer, default=2)
    
    # Configuración de posiciones de texto
    text1_label = db.Column(db.String(50), default="Texto 1")
    text1_x = db.Column(db.Float, default=50.0)  # Porcentaje desde la izquierda (0-100)
    text1_y = db.Column(db.Float, default=20.0)  # Porcentaje desde arriba (0-100)
    text1_size = db.Column(db.Integer, default=24)  # Tamaño de fuente
    text1_width = db.Column(db.Float, default=30.0)  # Ancho de la caja de texto en %
    text1_height = db.Column(db.Float, default=10.0)  # Alto de la caja de texto en %
    
    text2_label = db.Column(db.String(50), default="Texto 2")
    text2_x = db.Column(db.Float, default=50.0)  # Porcentaje desde la izquierda (0-100)
    text2_y = db.Column(db.Float, default=80.0)  # Porcentaje desde arriba (0-100)
    text2_size = db.Column(db.Integer, default=24)  # Tamaño de fuente
    text2_width = db.Column(db.Float, default=30.0)  # Ancho de la caja de texto en %
    text2_height = db.Column(db.Float, default=10.0)  # Alto de la caja de texto en %
    
    text3_label = db.Column(db.String(50), default="Texto 3")
    text3_x = db.Column(db.Float, default=50.0)
    text3_y = db.Column(db.Float, default=50.0)
    text3_size = db.Column(db.Integer, default=24)
    text3_width = db.Column(db.Float, default=30.0)
    text3_height = db.Column(db.Float, default=10.0)
    
    text4_label = db.Column(db.String(50), default="Texto 4")
    text4_x = db.Column(db.Float, default=25.0)
    text4_y = db.Column(db.Float, default=35.0)
    text4_size = db.Column(db.Integer, default=24)
    text4_width = db.Column(db.Float, default=30.0)
    text4_height = db.Column(db.Float, default=10.0)
    
    text5_label = db.Column(db.String(50), default="Texto 5")
    text5_x = db.Column(db.Float, default=75.0)
    text5_y = db.Column(db.Float, default=65.0)
    text5_size = db.Column(db.Integer, default=24)
    text5_width = db.Column(db.Float, default=30.0)
    text5_height = db.Column(db.Float, default=10.0)
    
    # Dimensiones de la imagen para cálculos
    image_width = db.Column(db.Integer, default=500)
    image_height = db.Column(db.Integer, default=500)

class PlayerTemplate(db.Model):
    __tablename__ = 'player_template'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('meme_template.id'), index=True)
    round_number = db.Column(db.Integer, default=1)
    
    # Datos del meme creado por el jugador
    text1 = db.Column(db.String(200), nullable=True)
    text2 = db.Column(db.String(200), nullable=True)
    text3 = db.Column(db.String(200), nullable=True)
    text4 = db.Column(db.String(200), nullable=True)
    text5 = db.Column(db.String(200), nullable=True)
    
    # Imagen del meme creado (base64)
    meme_image_data = db.Column(db.Text, nullable=True)
    meme_filename = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    user = db.relationship('User', backref='templates_created')
    game = db.relationship('Game', backref='player_templates')
    template = db.relationship('MemeTemplate', backref='player_creations')

class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    voted_template_id = db.Column(db.Integer, db.ForeignKey('player_template.id'), index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    round_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    voter = db.relationship('User', backref='votes_given')
    voted_template = db.relationship('PlayerTemplate', backref='votes_received')
    game = db.relationship('Game', backref='votes')

class GameRound(db.Model):
    __tablename__ = 'game_round'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    round_number = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='active')  # active, voting, completed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Relación
    game = db.relationship('Game', backref='rounds')
