from flask import render_template, request, redirect, url_for, session
from . import auth_bp
from models import db, User

@auth_bp.route('/nickname', methods=['GET', 'POST'])
def show_nickname_form():
    if request.method == 'POST':
        nickname = request.form.get('nickname')
        if nickname:
            # Buscar usuario existente o crear uno nuevo
            user = User.query.filter_by(nickname=nickname).first()
            if not user:
                user = User(nickname=nickname)
                db.session.add(user)
                db.session.commit()
            
            session['user_id'] = user.id
            return redirect(url_for('index'))
    
    return render_template('auth/nickname.html')
