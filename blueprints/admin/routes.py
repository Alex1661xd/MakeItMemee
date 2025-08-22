from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from models import db, MemeTemplate
from werkzeug.utils import secure_filename
import os
import base64
import io
from PIL import Image
import imghdr

admin_bp = Blueprint("admin", __name__)

# Contraseña del admin (en producción debería estar en variables de entorno)
ADMIN_PASSWORD = "admin"

def require_admin_auth(f):
    """Decorador para requerir autenticación de admin"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    """Página de login para administradores"""
    if request.method == "POST":
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            return redirect(url_for('admin.admin_panel'))
        else:
            return render_template('admin/login.html', error="Contraseña incorrecta")
    
    return render_template('admin/login.html')

@admin_bp.route("/logout")
def admin_logout():
    """Cerrar sesión de admin"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.admin_login'))

@admin_bp.route("/")
@require_admin_auth
def admin_panel():
    """Panel administrativo principal"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    # Obtener memes con paginación
    pagination = MemeTemplate.query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    templates = pagination.items
    
    return render_template('admin/panel.html', 
                         templates=templates, 
                         pagination=pagination)

