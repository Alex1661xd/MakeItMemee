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
@a@admin_bp.route("/meme/<int:meme_id>")
@require_admin_auth
def edit_meme_positions(meme_id):
    """Editar posiciones de texto de un meme específico"""
    template = MemeTemplate.query.get_or_404(meme_id)
    return render_template('admin/edit_meme.html', template=template)

@admin_bp.route("/meme/<int:meme_id>/delete", methods=["POST"])
@require_admin_auth
def delete_meme(meme_id):
    """Eliminar un meme template"""
    template = MemeTemplate.query.get_or_404(meme_id)
    
    try:
        # Eliminar archivo de imagen si existe
        if template.image_path and os.path.exists(template.image_path):
            os.remove(template.image_path)
        
        # Eliminar de la base de datos
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Meme eliminado correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/meme/<int:meme_id>/update", methods=["POST"])
@require_admin_auth
def update_meme_positions(meme_id):
    """Actualizar posiciones de texto de un meme"""
    template = MemeTemplate.query.get_or_404(meme_id)
    
    try:
        # Actualizar número de cajas de texto si se provee
        if request.json.get('num_text_boxes'):
            template.num_text_boxes = int(request.json.get('num_text_boxes'))
        
        # Actualizar etiquetas y posiciones para cada caja de texto
        for i in range(1, 6):  # text1 a text5
            label_key = f'text{i}_label'
            x_key = f'text{i}_x'
            y_key = f'text{i}_y'
            size_key = f'text{i}_size'
            width_key = f'text{i}_width'
            height_key = f'text{i}_height'
            
            if request.json.get(label_key):
                setattr(template, label_key, request.json.get(label_key))
            if request.json.get(x_key) is not None:
                setattr(template, x_key, float(request.json.get(x_key)))
            if request.json.get(y_key) is not None:
                setattr(template, y_key, float(request.json.get(y_key)))
            if request.json.get(size_key):
                setattr(template, size_key, int(request.json.get(size_key)))
            if request.json.get(width_key) is not None:
                setattr(template, width_key, float(request.json.get(width_key)))
            if request.json.get(height_key) is not None:
                setattr(template, height_key, float(request.json.get(height_key)))
        
        # Actualizar dimensiones de imagen si se proveen
        if request.json.get('image_width'):
            template.image_width = int(request.json.get('image_width'))
        if request.json.get('image_height'):
            template.image_height = int(request.json.get('image_height'))
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Posiciones actualizadas correctamente"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500