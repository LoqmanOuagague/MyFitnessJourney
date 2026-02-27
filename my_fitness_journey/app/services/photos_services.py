import os
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from app.models.photos import Photo
from app.database.database import db
from app.services.errors import ApiError, NotFoundError

# --- Constantes de Configuration (Tier A) ---
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def get_upload_folder():
    """Détermine le chemin absolu du dossier d'upload."""
    # Stockage dans app/static/uploads pour la facilité d'accès publique par Flask
    return os.path.join(current_app.root_path, "static", "uploads") 

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------------------------------
# SERVICE D'UPLOAD (POST /api/photos)
# -----------------------------------------------------
def upload_photo(file_storage: FileStorage, user_email: str) -> Photo:
    
    if file_storage.filename == "" or not file_storage.filename:
        raise ApiError("Bad request: missing form field 'file'")

    # 1. Validation de l'extension (pour 415)
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type: only jpg, jpeg, png, webp allowed") 

    # 2. Validation de la taille (pour 413)
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0) 
    
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE_MB} MB)")

    # 3. CRÉATION DU RECORD BDD POUR OBTENIR L'ID (Clé de liaison)
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    
    # On crée la Photo avec NULL pour listing_id (sera lié plus tard)
    photo = Photo(url="temp", extension=ext, is_thumbnail=False, listing_id=None) 
    
    db.session.add(photo)
    db.session.flush() # ⬅️ CLÉ : Force l'insertion pour obtenir photo.id

    # 4. Sauvegarde physique du fichier (ID.extension)
    filename_on_disk = f"{photo.id}.{ext}" 
    upload_folder = get_upload_folder()
    
    os.makedirs(upload_folder, exist_ok=True) 
    filepath = os.path.join(upload_folder, filename_on_disk)

    file_storage.save(filepath)

    # 5. Mise à jour de l'URL finale dans la BDD
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    url = f"{base_url}/api/photos/{photo.id}" 
    photo.url = url
    
    db.session.commit()
    return photo


# -----------------------------------------------------
# SERVICE DE SERVAGE (GET /api/photos/{id})
# -----------------------------------------------------
def get_photo_binary(photo_id: int):
    """
    Sert le fichier en utilisant l'ID BDD pour reconstruire le chemin du fichier.
    """
    photo = Photo.query.get(photo_id)
    if not photo:
        raise NotFoundError("Photo not found") 

    # Reconstruire le nom du fichier sur le disque
    filename_on_disk = f"{photo.id}.{photo.extension}" 
    upload_folder = get_upload_folder()
    
    # Send_from_directory est généralement appelé par la route pour l'envoi HTTP
    try:
        return send_from_directory(upload_folder, filename_on_disk)
    except FileNotFoundError:
         raise NotFoundError("Photo not found on disk")