# Make It Meme

Una aplicación web para crear y jugar juegos de memes en tiempo real.

## Características

- Crear y unirse a juegos de memes
- Editor visual de memes con plantillas personalizables
- Sistema de votación en tiempo real
- Múltiples rondas de juego
- Interfaz de administrador para gestionar plantillas

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- Git

### Configuración Local

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd MakeItMemee
```

2. Crear entorno virtual:
```bash
python -m venv venv
```

3. Activar entorno virtual:
```bash
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

4. Instalar dependencias:
```bash
pip install -r requirements.txt
```

5. Configurar variables de entorno (opcional):
Crear un archivo `.env` con:
```
SECRET_KEY=tu_clave_secreta_aqui
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
REDIS_URL=redis://localhost:6379/0
```

**Nota**: Si no creas el archivo `.env`, la aplicación usará configuraciones por defecto para desarrollo local.

6. Ejecutar la aplicación:
```bash
python run.py
```

O usar el script de inicio:
```bash
# En Linux/Mac:
./start.sh

# En Windows (PowerShell):
python start.sh
```

## Configuración de Desarrollo

### Base de Datos
- **Desarrollo**: SQLite local (`app.db`)
- **Producción**: PostgreSQL (configurar `DATABASE_URL`)

### Redis (Opcional)
- **Desarrollo**: Modo local sin Redis
- **Producción**: Redis (configurar `REDIS_URL`)

### Variables de Entorno
- `SECRET_KEY`: Clave secreta para sesiones
- `FLASK_ENV`: Entorno (development/production)
- `DATABASE_URL`: URL de la base de datos
- `REDIS_URL`: URL de Redis (opcional)

## Estructura del Proyecto

```
MakeItMemee/
├── app.py              # Aplicación principal Flask
├── config.py           # Configuración de la aplicación
├── extensions.py       # Extensiones Flask (SocketIO, etc.)
├── models.py           # Modelos de base de datos
├── run.py              # Script de ejecución
├── requirements.txt    # Dependencias de Python
├── start.sh            # Script de inicio
├── verify_setup.py     # Verificación de configuración
├── blueprints/         # Módulos de la aplicación
│   ├── admin/         # Panel de administrador
│   ├── auth/          # Autenticación de usuarios
│   └── game/          # Lógica del juego
├── migrations/         # Migraciones de base de datos
└── templates/          # Plantillas HTML (a implementar)
```

## Tecnologías Utilizadas

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Base de Datos**: SQLite (desarrollo), PostgreSQL (producción)
- **Tiempo Real**: Flask-SocketIO
- **Frontend**: HTML, CSS, JavaScript (a implementar)

## Desarrollo

### Ejecutar en Modo Desarrollo
```bash
python run.py
```

### Verificar Configuración
```bash
python verify_setup.py
```

### Crear Migraciones
```bash
flask db init
flask db migrate -m "Descripción del cambio"
flask db upgrade
```

## Uso

1. Abrir la aplicación en el navegador: `http://127.0.0.1:5000`
2. Ingresar un nickname
3. Crear un nuevo juego o unirse a uno existente
4. Crear memes usando las plantillas disponibles
5. Votar por los mejores memes
6. ¡Disfrutar del juego!

## Solución de Problemas

### Error de Dependencias
```bash
pip install -r requirements.txt
```

### Error de Base de Datos
```bash
# Eliminar archivo de base de datos existente
rm app.db

# Reiniciar la aplicación
python run.py
```

### Puerto en Uso
Cambiar el puerto en `run.py` o usar:
```bash
PORT=5001 python run.py
```

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
