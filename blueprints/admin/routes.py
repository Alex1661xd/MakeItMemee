from flask import render_template, request, redirect, url_for, session
from . import admin_bp
from models import db, User

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Lógica de login de admin
        pass
    
    return render_template('admin/login.html')

@admin_bp.route('/panel')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('admin.admin_login'))
    
    # Verificar si es admin
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin/panel.html')
