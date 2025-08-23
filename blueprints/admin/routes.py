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

@admin_bp.route("/meme/<int:meme_id>")
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

def compress_image(image_data, max_width=800, quality=85):
    """Comprime una imagen y la convierte a Base64"""
    try:
        # Abrir imagen desde bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convertir a RGB si es necesario (para PNGs con transparencia)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Redimensionar si es muy grande
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Guardar como JPEG comprimido
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        
        # Convertir a Base64
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        
        return base64_data, img.width, img.height
        
    except Exception as e:
        raise Exception(f"Error comprimiendo imagen: {str(e)}")

@admin_bp.route("/upload", methods=["POST"])
@require_admin_auth
def upload_meme():
    """Subir nueva plantilla de meme con imagen"""
    try:
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No se subió ninguna imagen"}), 400
        
        file = request.files['image']
        name = request.form.get('name', '').strip()
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No se seleccionó ningún archivo"}), 400
        
        if not name:
            # Usar el nombre del archivo sin extensión
            name = os.path.splitext(file.filename)[0]
        
        # Validar tipo de archivo
        if not file.content_type.startswith('image/'):
            return jsonify({"success": False, "error": "El archivo debe ser una imagen"}), 400
        
        # Leer datos de la imagen
        image_data = file.read()
        
        # Comprimir imagen
        base64_data, width, height = compress_image(image_data)
        
        # Crear plantilla en la base de datos
        template = MemeTemplate(
            name=name,
            image_data=base64_data,
            image_filename=secure_filename(file.filename),
            image_mimetype=file.content_type,
            image_width=width,
            image_height=height,
            num_text_boxes=2,  # Por defecto usar 2 cajas
            text1_label="Texto 1",
            text1_x=50.0,
            text1_y=20.0,
            text1_size=24,
            text1_width=30.0,
            text1_height=10.0,
            text2_label="Texto 2",
            text2_x=50.0,
            text2_y=80.0,
            text2_size=24,
            text2_width=30.0,
            text2_height=10.0,
            text3_label="Texto 3",
            text3_x=50.0,
            text3_y=50.0,
            text3_size=24,
            text3_width=30.0,
            text3_height=10.0,
            text4_label="Texto 4",
            text4_x=25.0,
            text4_y=35.0,
            text4_size=24,
            text4_width=30.0,
            text4_height=10.0,
            text5_label="Texto 5",
            text5_x=75.0,
            text5_y=65.0,
            text5_size=24,
            text5_width=30.0,
            text5_height=10.0,
            active=True
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Meme subido correctamente",
            "id": template.id,
            "redirect": f"/admin/dynamic-editor/{template.id}"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@admin_bp.route("/editor/<int:meme_id>")
@require_admin_auth
def visual_editor(meme_id):
    """Editor visual drag & drop para posicionar texto"""
    template = MemeTemplate.query.get_or_404(meme_id)
    return render_template('admin/visual_editor.html', template=template)

@admin_bp.route("/dynamic-editor/<int:meme_id>")
@require_admin_auth
def dynamic_editor(meme_id):
    """Editor dinámico para configurar número variable de cajas de texto"""
    template = MemeTemplate.query.get_or_404(meme_id)
    return render_template('admin/dynamic_editor.html', template=template)

@admin_bp.route("/image/<int:meme_id>")
@require_admin_auth
def serve_meme_image(meme_id):
    """Servir imagen de meme desde la base de datos (solo para admin)"""
    template = MemeTemplate.query.get_or_404(meme_id)
    
    # Si tiene imagen en Base64, usarla
    if template.image_data:
        from flask import Response
        image_data = base64.b64decode(template.image_data)
        return Response(
            image_data,
            mimetype=template.image_mimetype or 'image/jpeg'
        )
    
    # Si solo tiene path, redirigir (compatibilidad)
    elif template.image_path:
        return redirect(f"/{template.image_path}")
    
    else:
        return "Imagen no encontrada", 404

@admin_bp.route("/public-image/<int:meme_id>")
def serve_public_meme_image(meme_id):
    """Servir imagen de meme públicamente (para el juego)"""
    template = MemeTemplate.query.get_or_404(meme_id)
    
    # Si tiene imagen en Base64, usarla
    if template.image_data:
        from flask import Response
        image_data = base64.b64decode(template.image_data)
        return Response(
            image_data,
            mimetype=template.image_mimetype or 'image/jpeg'
        )
    
    # Si solo tiene path, redirigir (compatibilidad)
    elif template.image_path:
        return redirect(f"/{template.image_path}")
    
    else:
        return "Imagen no encontrada", 404

@admin_bp.route("/meme/add", methods=["GET"])
def add_meme():
    """Mostrar formulario para agregar meme"""
    return render_template('admin/upload_meme.html')
