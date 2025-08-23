from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import emit, join_room, leave_room
from models import db, Game, User, MemeTemplate, PlayerTemplate, Vote
from extensions import socketio
from datetime import datetime
import random, string

game_bp = Blueprint("game", __name__)

# Constantes de puntuación
VOTE_POINTS = {
    'suave': 1,      # Meme malo
    'normal': 3,     # Meme normal  
    'me_rei': 10     # Meme muy gracioso
}

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Cache de IDs de plantillas activas (más seguro que objetos completos)
_active_template_ids = None
_cache_timestamp = None

def get_active_templates(force_refresh=False):
    """Obtener plantillas activas de forma segura para SQLAlchemy"""
    global _active_template_ids, _cache_timestamp
    
    current_time = datetime.utcnow()
    
    # Refrescar caché si no existe, es muy viejo (>5 min), o se fuerza
    if (force_refresh or 
        _active_template_ids is None or 
        _cache_timestamp is None or 
        (current_time - _cache_timestamp).total_seconds() > 300):
        
        # Solo cachear los IDs, no los objetos completos
        template_ids = db.session.query(MemeTemplate.id).filter_by(active=True).all()
        _active_template_ids = [t[0] for t in template_ids]  # Extraer solo los IDs
        _cache_timestamp = current_time
        print(f"🔄 Cache de plantillas actualizado: {len(_active_template_ids)} plantillas")
    
    # Siempre obtener objetos frescos de la sesión actual
    if _active_template_ids:
        return MemeTemplate.query.filter(MemeTemplate.id.in_(_active_template_ids)).all()
    else:
        return []

def get_game_players_count(game_id):
    """Obtener conteo de jugadores de forma optimizada"""
    return User.query.filter_by(game_id=game_id).count()

def get_submitted_count(game_id, round_number):
    """Obtener conteo de memes enviados de forma optimizada"""
    return PlayerTemplate.query.filter_by(
        game_id=game_id,
        round_number=round_number,
        selected=True
    ).count()

def distribute_templates_optimized(game, templates, round_number):
    """
    Distribución optimizada de plantillas con manejo seguro de sesiones SQLAlchemy
    """
    num_players = len(game.players)
    if not templates or num_players == 0:
        return False
    
    max_per_round = getattr(game, 'templates_per_round', None) or 5
    
    # Optimización: usar el mínimo entre plantillas disponibles y necesarias
    available_unique = len(templates)
    max_distributable = available_unique // num_players
    templates_per_player = min(max_per_round, max_distributable)
    
    try:
        if templates_per_player >= 1:
            # Distribución sin repetidos para mejor experiencia
            shuffled = templates[:]
            random.shuffle(shuffled)
            needed = templates_per_player * num_players
            selected = shuffled[:needed]
            
            for idx, player in enumerate(game.players):
                start_idx = idx * templates_per_player
                end_idx = start_idx + templates_per_player
                player_templates = selected[start_idx:end_idx]
                
                for template in player_templates:
                    # Usar add() individual en lugar de bulk_save para mejor compatibilidad
                    pt = PlayerTemplate(
                        user_id=player.id,
                        game_id=game.id,
                        template_id=template.id,
                        round_number=round_number
                    )
                    db.session.add(pt)
        else:
            # Fallback: distribución aleatoria cuando hay pocas plantillas
            for player in game.players:
                template = random.choice(templates)
                pt = PlayerTemplate(
                    user_id=player.id,
                    game_id=game.id,
                    template_id=template.id,
                    round_number=round_number
                )
                db.session.add(pt)
        
        # No hacer commit aquí, dejarlo para la función que llama
        return True
        
    except Exception as e:
        print(f"Error distribuyendo plantillas: {str(e)}")
        db.session.rollback()
        return False

@game_bp.route("/create", methods=["GET"])
def show_create_form():
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
    
    user = User.query.get(session["user_id"])
    
    if not user:
        session.clear()
        return redirect(url_for('auth.show_nickname_form'))
    
    if user.game_id:
        game = Game.query.get(user.game_id)
        if game and game.status in ['waiting', 'started']:
            return redirect(url_for('game.waiting_room', code=game.code))
        else:
            # Limpiar juego terminado o inexistente
            user.game_id = None
            db.session.commit()

    try:
        code = generate_code()
        
        game = Game(
            code=code,
            max_players=15,
            creator_id=user.id,
            created_at=datetime.utcnow(),
            status='waiting'
        )
        
        db.session.add(game)
        db.session.commit()
        
        user = User.query.get(session["user_id"])
        user.game_id = game.id
        db.session.commit()

        return redirect(url_for('game.waiting_room', code=game.code))
    except Exception:
        db.session.rollback()
        return redirect(url_for('index'))

@game_bp.route("/create", methods=["POST"])
def create_game():
    return redirect(url_for('game.show_create_form'))

@game_bp.route("/join", methods=["GET"])
def show_join_form():
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
    return render_template('game/join.html')

@game_bp.route("/join", methods=["POST"])
def join_game():
    if "user_id" not in session:
        return jsonify({"error": "Debes tener un nickname para unirte"}), 401

    code = request.json.get("code")
    if not code:
        return jsonify({"error": "Código de partida requerido"}), 400

    game = Game.query.filter_by(code=code).first()
    if not game:
        return jsonify({"error": "Partida no encontrada"}), 404

    if game.status != 'waiting':
        return jsonify({"error": "La partida ya ha comenzado"}), 400

    user = User.query.get(session["user_id"])

    if user.game_id:
        # Verificar si el juego actual sigue activo
        current_game = Game.query.get(user.game_id)
        if current_game and current_game.status in ['waiting', 'started']:
            if user.game_id == game.id:
                return jsonify({"redirect": f"/game/waiting/{code}"})
            else:
                return jsonify({"error": "Ya estás en otra partida"}), 400
        else:
            # Limpiar juego terminado
            user.game_id = None
            db.session.commit()

    current_players = User.query.filter_by(game_id=game.id).count()
    if current_players >= game.max_players:
        return jsonify({"error": "Partida llena"}), 400

    try:
        user.game_id = game.id
        db.session.commit()
        
        return jsonify({
            "message": "Te has unido a la partida",
            "redirect": f"/game/waiting/{code}"
        })
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error al unirse a la partida"}), 500

@game_bp.route("/waiting/<code>")
def waiting_room(code):
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for('auth.show_nickname_form'))
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        return redirect(url_for('index'))
    
    # Si el juego ya terminó, redirigir al menú principal
    if game.status in ['finished', 'completed']:
        if user.game_id == game.id:
            user.game_id = None
            db.session.commit()
        return redirect(url_for('index'))
    
    if user.game_id != game.id:
        if user.id == game.creator_id:
            user.game_id = game.id
            db.session.commit()
        else:
            current_players = len(game.players)
            if current_players < game.max_players and game.status == 'waiting':
                user.game_id = game.id
                db.session.commit()
            else:
                return redirect(url_for('index'))
    
    players = User.query.filter_by(game_id=game.id).all()
    
    is_creator = user.id == game.creator_id
    
    return render_template('game/create.html', 
                         game_code=game.code,
                         creator_nickname=game.creator.nickname,
                         players=players,
                         current_players=len(players),
                         is_creator=is_creator)

@game_bp.route("/check/<code>")
def check_game_status(code):
    try:
        game = Game.query.filter_by(code=code).first_or_404()
        players = User.query.filter_by(game_id=game.id).all()
        
        current_time = datetime.utcnow()
        time_elapsed = current_time - game.created_at
        
        # Si hay más de 2 jugadores y ha pasado el tiempo, iniciar la partida automáticamente
        if len(players) >= 2 and game.status == 'waiting' and time_elapsed.total_seconds() >= 150:
            try:
                # Iniciar primera ronda
                game.status = 'started'
                game.current_round = 1
                game.round_start_time = datetime.utcnow()
                
                # Distribuir plantillas para la primera ronda (optimizado)
                templates = get_active_templates()
                distribute_templates_optimized(game, templates, 1)
                
                db.session.commit()
                socketio.emit('game_started', room=code)
                return jsonify({"status": "started", "redirect": f"/game/play/{code}"})
                
            except Exception as e:
                db.session.rollback()
                print(f"Error iniciando partida automáticamente: {str(e)}")
                return jsonify({"error": "Error al iniciar la partida"}), 500
            
        # Si solo hay 1 jugador después de 30 segundos, cancelar
        if len(players) <= 1 and game.status == 'waiting' and time_elapsed.total_seconds() > 30:
            for player in players:
                player.game_id = None
            db.session.delete(game)
            db.session.commit()
            return jsonify({"status": "cancelled", "message": "Partida cancelada por falta de jugadores"})
        
        if not game.created_at:
            game.created_at = datetime.utcnow()
            db.session.commit()
        
        current_time = datetime.utcnow()
        time_elapsed = current_time - game.created_at
        time_remaining = max(0, 150 - int(time_elapsed.total_seconds()))
        
        # Determinar si el usuario actual es el creador
        is_creator = session.get('user_id') == game.creator_id
        
    except Exception as e:
        print(f"Error en check_game_status: {str(e)}")
        return jsonify({"error": "Error al verificar el estado de la partida"}), 500
    
    response = {
        "status": game.status,
        "timeRemaining": time_remaining,
        "players": [{"id": p.id, "nickname": p.nickname, "isCreator": p.id == game.creator_id} for p in players],
        "playerCount": len(players),
        "canStart": is_creator and len(players) >= 2,
        "isCreator": is_creator
    }
    
    socketio.emit('update', room=code)
    
    return jsonify(response)

@game_bp.route("/start/<code>", methods=["POST"])
def start_game(code):
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
        
    game = Game.query.filter_by(code=code).first_or_404()
    
    # Solo el creador puede iniciar manualmente
    if request.method == "POST" and game.creator_id != session["user_id"]:
        return jsonify({"error": "Solo el creador puede iniciar la partida"}), 403
        
    if len(game.players) < 2:
        return jsonify({"error": "Se necesitan al menos 2 jugadores"}), 400
        
    try:
        # Iniciar primera ronda
        game.status = 'started'
        game.current_round = 1
        game.round_start_time = datetime.utcnow()
        
        # Distribuir plantillas para la primera ronda (optimizado)
        templates = get_active_templates()
        distribute_templates_optimized(game, templates, 1)
        
        db.session.commit()
        socketio.emit('game_started', room=code)
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@game_bp.route("/play/<code>")
def play_game(code):
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
        
    game = Game.query.filter_by(code=code).first_or_404()
    user = User.query.get(session["user_id"])
    
    if game.status != 'started':
        return redirect(url_for('game.waiting_room', code=code))
        
    # Obtener plantillas del jugador para la ronda actual
    player_templates = PlayerTemplate.query.filter_by(
        user_id=user.id,
        game_id=game.id,
        round_number=game.current_round
    ).all()
    
    print(f"Usuario {user.nickname} en ronda {game.current_round}: {len(player_templates)} plantillas encontradas")
    
    # Calcular tiempo restante
    elapsed = datetime.utcnow() - game.round_start_time
    time_left = max(0, 120 - int(elapsed.total_seconds()))
    
    # Convertir plantillas a diccionarios serializables
    templates_data = []
    for pt in player_templates:
        # Determinar la ruta de imagen
        if pt.template.image_data:
            # Imagen almacenada en Base64 en la DB
            image_path = f"/admin/public-image/{pt.template.id}"
        elif pt.template.image_path:
            # Imagen en archivo local (compatibilidad)
            image_path = pt.template.image_path
        else:
            image_path = "/static/memes/default.jpg"  # Imagen por defecto
            
        template_dict = {
            'id': pt.id,
            'template': {
                'id': pt.template.id,
                'name': pt.template.name,
                'image_path': image_path,
                'num_text_boxes': getattr(pt.template, 'num_text_boxes', 2),
                'image_width': pt.template.image_width,
                'image_height': pt.template.image_height
            }
        }
        
        # Agregar todos los campos de texto dinámicamente
        for i in range(1, 6):
            template_dict['template'][f'text{i}_label'] = getattr(pt.template, f'text{i}_label', f'Texto {i}')
            template_dict['template'][f'text{i}_x'] = getattr(pt.template, f'text{i}_x', 50.0)
            template_dict['template'][f'text{i}_y'] = getattr(pt.template, f'text{i}_y', 20.0 if i == 1 else 80.0 if i == 2 else 50.0)
            template_dict['template'][f'text{i}_size'] = getattr(pt.template, f'text{i}_size', 24)
            template_dict['template'][f'text{i}_width'] = getattr(pt.template, f'text{i}_width', 30.0)
            template_dict['template'][f'text{i}_height'] = getattr(pt.template, f'text{i}_height', 10.0)
        
        templates_data.append(template_dict)
    
    return render_template('game/play.html',
                         game=game,
                         templates=templates_data,
                         round_time_left=time_left)

@game_bp.route("/check-round/<code>")
def check_round_status(code):
    """Verificar el estado de la ronda actual y si ha expirado el tiempo"""
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    game = Game.query.filter_by(code=code).first_or_404()
    
    if game.status != 'started':
        return jsonify({"status": "not_started"}), 400
    
    # Calcular tiempo restante
    elapsed = datetime.utcnow() - game.round_start_time
    time_left = max(0, 120 - int(elapsed.total_seconds()))
    
    # Verificar si todos han enviado sus memes (optimizado)
    submitted_count = get_submitted_count(game.id, game.current_round)
    all_submitted = submitted_count == len(game.players)
    
    # Si el tiempo se agotó o todos enviaron, finalizar ronda
    if time_left <= 0 or all_submitted:
        socketio.emit('round_ended', room=code)
        return jsonify({
            "roundEnded": True,
            "allSubmitted": all_submitted,
            "timeLeft": 0
        })
    
    return jsonify({
        "roundEnded": False,
        "allSubmitted": all_submitted,
        "timeLeft": time_left,
        "current_round": game.current_round,
        "templates_available": True
    })

@game_bp.route("/submit-meme", methods=["POST"])
def submit_meme():
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    game_code = data.get('game_code')
    template_id = data.get('template_id')
    
    # Mantener compatibilidad con campos antiguos
    text_top = data.get('text_top', '')
    text_bottom = data.get('text_bottom', '')
    
    # Obtener todos los campos de texto dinámicos
    text_fields = {}
    for i in range(1, 6):
        text_fields[f'text{i}'] = data.get(f'text{i}', '')
    
    game = Game.query.filter_by(code=game_code).first_or_404()
    user = User.query.get(session["user_id"])
    
    try:
        # Actualizar la plantilla seleccionada
        template = PlayerTemplate.query.filter_by(
            id=template_id,
            user_id=user.id,
            game_id=game.id,
            round_number=game.current_round
        ).first()
        
        if template:
            template.selected = True
            # Mantener compatibilidad con campos antiguos
            template.text_top = text_top
            template.text_bottom = text_bottom
            
            # Actualizar todos los campos de texto dinámicos
            for i in range(1, 6):
                field_name = f'text{i}'
                if hasattr(template, field_name):
                    setattr(template, field_name, text_fields[field_name])
            
            db.session.commit()
        
        # Verificar si todos han enviado sus memes (optimizado)
        submitted_count = get_submitted_count(game.id, game.current_round)
        all_submitted = submitted_count == len(game.players)
        
        if all_submitted:
            # Todos han enviado sus memes, redirigir a resultados
            socketio.emit('all_submitted', room=game_code)
        
        return jsonify({
            "success": True,
            "allSubmitted": all_submitted
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@game_bp.route("/results/<code>")
def round_results(code):
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
        
    game = Game.query.filter_by(code=code).first_or_404()
    user = User.query.get(session["user_id"])
    
    if game.status != 'started':
        return redirect(url_for('game.waiting_room', code=code))
    
    # Siempre ir a la fase de votación primero
    # El podio solo se mostrará después de completar la votación de la tercera ronda
    return redirect(url_for('game.voting_phase', code=code))

@game_bp.route("/voting/<code>")
def voting_phase(code):
    """Fase de votación - mostrar memes uno por uno"""
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
        
    game = Game.query.filter_by(code=code).first_or_404()
    user = User.query.get(session["user_id"])
    
    if game.status != 'started':
        return redirect(url_for('game.waiting_room', code=code))
    
    # Obtener todos los memes de la ronda actual que fueron seleccionados
    round_memes = PlayerTemplate.query.filter_by(
        game_id=game.id,
        round_number=game.current_round,
        selected=True
    ).all()
    
    # Preparar datos de memes para votación
    memes_data = []
    for meme in round_memes:
        # Determinar la ruta de imagen
        if meme.template.image_data:
            image_path = f"/admin/public-image/{meme.template.id}"
        elif meme.template.image_path:
            image_path = meme.template.image_path
        else:
            image_path = "/static/memes/default.jpg"
        
        # Obtener textos del meme
        texts = []
        num_boxes = meme.template.num_text_boxes or 2
        for i in range(1, num_boxes + 1):
            text_content = getattr(meme, f'text{i}', '') or ''
            if text_content:
                texts.append({
                    'content': text_content,
                    'x': getattr(meme.template, f'text{i}_x', 50),
                    'y': getattr(meme.template, f'text{i}_y', 20 if i == 1 else 80),
                    'size': getattr(meme.template, f'text{i}_size', 24),
                    'width': getattr(meme.template, f'text{i}_width', 30),
                    'height': getattr(meme.template, f'text{i}_height', 10)
                })
        
        meme_data = {
            'id': meme.id,
            'creator_name': meme.user.nickname,
            'creator_id': meme.user_id,
            'image_path': image_path,
            'template_name': meme.template.name,
            'texts': texts,
            'total_points': meme.total_points
        }
        memes_data.append(meme_data)
    
    return render_template('game/voting.html',
                         game=game,
                         memes=memes_data,
                         current_user_id=user.id)

@game_bp.route("/vote", methods=["POST"])
def vote_meme():
    """Votar por un meme"""
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    data = request.json
    player_template_id = data.get('player_template_id')
    vote_type = data.get('vote_type')  # 'suave', 'normal', 'me_rei'
    game_code = data.get('game_code')
    
    # Validaciones
    if vote_type not in VOTE_POINTS:
        return jsonify({"error": "Tipo de voto inválido"}), 400
    
    game = Game.query.filter_by(code=game_code).first_or_404()
    user = User.query.get(session["user_id"])
    player_template = PlayerTemplate.query.get_or_404(player_template_id)
    
    # No permitir votar por tu propio meme
    if player_template.user_id == user.id:
        return jsonify({"error": "No puedes votar por tu propio meme"}), 400
    
    # Verificar si ya votó por este meme
    existing_vote = Vote.query.filter_by(
        voter_id=user.id,
        player_template_id=player_template_id
    ).first()
    
    if existing_vote:
        return jsonify({"error": "Ya votaste por este meme"}), 400
    
    try:
        # Crear el voto
        points = VOTE_POINTS[vote_type]
        vote = Vote(
            voter_id=user.id,
            player_template_id=player_template_id,
            game_id=game.id,
            round_number=game.current_round,
            vote_type=vote_type,
            points=points
        )
        db.session.add(vote)
        
        # Actualizar puntos totales del meme
        player_template.total_points = (player_template.total_points or 0) + points
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "points_given": points,
            "new_total": player_template.total_points
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@game_bp.route("/podium/<code>")
def final_podium(code):
    """Mostrar podio final con los mejores memes"""
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
        
    game = Game.query.filter_by(code=code).first_or_404()
    user = User.query.get(session["user_id"])
    
    if game.status != 'finished':
        return redirect(url_for('game.waiting_room', code=code))
    
    # Obtener todos los memes del juego ordenados por puntuación
    all_memes = PlayerTemplate.query.filter_by(
        game_id=game.id,
        selected=True
    ).order_by(PlayerTemplate.total_points.desc()).all()
    
    # Preparar datos del podio
    podium_data = []
    for meme in all_memes:
        # Determinar la ruta de imagen
        if meme.template.image_data:
            image_path = f"/admin/public-image/{meme.template.id}"
        elif meme.template.image_path:
            image_path = meme.template.image_path
        else:
            image_path = "/static/memes/default.jpg"
        
        # Obtener textos del meme
        texts = []
        num_boxes = meme.template.num_text_boxes or 2
        for i in range(1, num_boxes + 1):
            text_content = getattr(meme, f'text{i}', '') or ''
            if text_content:
                texts.append({
                    'content': text_content,
                    'x': getattr(meme.template, f'text{i}_x', 50),
                    'y': getattr(meme.template, f'text{i}_y', 20 if i == 1 else 80),
                    'size': getattr(meme.template, f'text{i}_size', 24),
                    'width': getattr(meme.template, f'text{i}_width', 30),
                    'height': getattr(meme.template, f'text{i}_height', 10)
                })
        
        meme_data = {
            'id': meme.id,
            'creator_name': meme.user.nickname,
            'image_path': image_path,
            'template_name': meme.template.name,
            'texts': texts,
            'total_points': meme.total_points,
            'round_number': meme.round_number
        }
        podium_data.append(meme_data)
    
    return render_template('game/podium.html',
                         game=game,
                         memes=podium_data,
                         winner=podium_data[0] if podium_data else None)

@game_bp.route("/continue-after-voting/<code>", methods=["POST"])
def continue_after_voting(code):
    """Continuar a la siguiente ronda después de la votación"""
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
        
    game = Game.query.filter_by(code=code).first_or_404()
    user = User.query.get(session["user_id"])
    
    # Solo el creador puede continuar
    if game.creator_id != user.id:
        return jsonify({"error": "Solo el creador puede continuar"}), 403
        
    if game.current_round >= 3:
        # Juego terminado
        game.status = 'finished'
        db.session.commit()
        
        # Emitir evento para todos los jugadores de que el juego ha terminado
        socketio.emit('game_finished', {
            'redirect': f"/game/podium/{code}"
        }, room=code)
        
        return jsonify({"redirect": f"/game/podium/{code}"})
        
    try:
        # Avanzar a la siguiente ronda
        game.current_round += 1
        game.round_start_time = datetime.utcnow()
        
        # Distribuir nuevas plantillas para la nueva ronda (optimizado)
        templates = get_active_templates()
        distribute_templates_optimized(game, templates, game.current_round)
        
        db.session.commit()
        
        # Verificar que se crearon las plantillas
        created_templates = PlayerTemplate.query.filter_by(
            game_id=game.id,
            round_number=game.current_round
        ).count()
        
        print(f"Ronda {game.current_round}: Se crearon {created_templates} plantillas para {len(game.players)} jugadores")
        
        # Emitir evento para todos los jugadores
        socketio.emit('next_round_started', {
            'round': game.current_round,
            'redirect': f"/game/play/{code}"
        }, room=code)
        
        # También emitir un evento específico para forzar la actualización
        socketio.emit('force_refresh', room=code)
        
        return jsonify({"success": True, "redirect": f"/game/play/{code}"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@socketio.on('join')
def on_join(data):
    code = data.get('code')
    if code:
        join_room(code)
        emit('update', room=code)

@socketio.on('leave')
def on_leave(data):
    code = data.get('code')
    if code:
        leave_room(code)
        emit('update', room=code)

@game_bp.route("/check-round-status/<code>")
def check_round_status_from_voting(code):
    """Verificar el estado de la ronda desde la fase de votación"""
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    game = Game.query.filter_by(code=code).first_or_404()
    
    # Si el juego ha terminado, indicarlo
    if game.status == 'finished':
        return jsonify({
            "status": "finished",
            "redirect": f"/game/podium/{code}"
        })
    
    if game.status != 'started':
        return jsonify({"status": "not_started"}), 400
    
    # Verificar si hay plantillas para la ronda actual
    player_templates_count = PlayerTemplate.query.filter_by(
        game_id=game.id,
        round_number=game.current_round
    ).count()
    
    return jsonify({
        "status": "started",
        "current_round": game.current_round,
        "templates_available": player_templates_count > 0,
        "templates_count": player_templates_count
    })

@game_bp.route("/cleanup-game/<code>")
def cleanup_game(code):
    """Limpiar el estado del juego cuando se regresa al menú principal"""
    if "user_id" not in session:
        return redirect(url_for('auth.show_nickname_form'))
    
    user = User.query.get(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for('auth.show_nickname_form'))
    
    try:
        # Buscar el juego
        game = Game.query.filter_by(code=code).first()
        if game:
            # Si el usuario está en este juego, limpiarlo
            if user.game_id == game.id:
                user.game_id = None
                db.session.commit()
                
                # Si el juego ya está terminado, marcarlo como completamente finalizado
                if game.status == 'finished':
                    game.status = 'completed'
                    db.session.commit()
        
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error limpiando juego: {str(e)}")
        db.session.rollback()
        return redirect(url_for('index'))
