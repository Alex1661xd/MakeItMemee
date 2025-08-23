from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models import db, User
import traceback

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("auth/nickname.html")

@auth_bp.route("/nickname", methods=["GET"])
def show_nickname_form():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("auth/nickname.html")

@auth_bp.route("/nickname", methods=["POST"])
def set_nickname():
    try:
        nickname = request.json.get("nickname")
        if not nickname:
            return jsonify({"error": "Nickname requerido"}), 400

        if len(nickname) < 3 or len(nickname) > 20:
            return jsonify({"error": "El nickname debe tener entre 3 y 20 caracteres"}), 400

        existing_user = User.query.filter_by(nickname=nickname).first()
        if existing_user:
            return jsonify({"error": "Este nickname ya está en uso"}), 400

        user = User(nickname=nickname)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return jsonify({"message": "Usuario creado exitosamente", "user_id": user.id})

    except Exception as e:
        db.session.rollback()
        print(f"Error al crear usuario: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Error al crear el usuario. Por favor, intenta de nuevo."}), 500

@auth_bp.route("/logout")
def logout():
    # Si el usuario está en una partida, liberarlo antes de logout
    if "user_id" in session:
        try:
            from models import User, Game
            user = User.query.get(session["user_id"])
            if user and user.game_id:
                # Liberar al usuario de la partida
                game = Game.query.get(user.game_id)
                if game and game.status == 'waiting':  # Solo si la partida no ha empezado
                    user.game_id = None
                    db.session.commit()
        except Exception as e:
            print(f"Error al liberar usuario de partida durante logout: {str(e)}")
            db.session.rollback()
    
    session.clear()
    return redirect(url_for("auth.show_nickname_form"))
