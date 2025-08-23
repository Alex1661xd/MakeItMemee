from flask import render_template, request, redirect, url_for, session
from . import game_bp
from models import db, User, Game

@game_bp.route('/create', methods=['GET', 'POST'])
def create_game():
    if 'user_id' not in session:
        return redirect(url_for('auth.show_nickname_form'))
    
    if request.method == 'POST':
        # Lógica para crear juego
        pass
    
    return render_template('game/create.html')

@game_bp.route('/join', methods=['GET', 'POST'])
def join_game():
    if 'user_id' not in session:
        return redirect(url_for('auth.show_nickname_form'))
    
    if request.method == 'POST':
        # Lógica para unirse a juego
        pass
    
    return render_template('game/join.html')
