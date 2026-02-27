from flask import Blueprint, request, jsonify, g
from app.services.photos_services import upload_photo, get_photo_binary 
from app.utils.auth import login_required
from app.services.errors import NotFoundError
from werkzeug.exceptions import RequestEntityTooLarge # Utile pour certaines erreurs 413
import os

# Définition du Blueprint
photo_bp = Blueprint("photos", __name__, url_prefix="/api/photos")

# -----------------------------------------------------
# 1. POST /api/photos (Upload)
# -----------------------------------------------------
@photo_bp.route("", methods=["POST"])
@login_required 
def upload_file():
    # 1. Vérification du champ file
    if 'file' not in request.files:
        return jsonify({"error": "Bad request: missing form field 'file'"}), 400
        
    file = request.files['file']
    user_email = g.user_email

    try:
        # L'objet file est un FileStorage de Werkzeug
        uploaded_photo = upload_photo(file, user_email)
        
        # 2. Construction de la réponse conforme (Tier A)
        response_body = {
            "url": uploaded_photo.url,
            "mime_type": uploaded_photo.extension # Utiliser l'extension comme hint pour le type
        }
        
        # Le Tier A exige l'URL dans le header Location
        response = jsonify(response_body)
        response.headers['Location'] = uploaded_photo.url
        
        return response, 201

    # 3. Gestion des erreurs spécifiques (Mapping des messages du service)
    except ValueError as e:
        error_msg = str(e)
        if "File too large" in error_msg:
            return jsonify({"error": "Payload too large: max 5 MiB"}), 413 #  413 Payload Too Large
        if "Unsupported file type" in error_msg:
             return jsonify({"error": error_msg}), 415 #  415 Unsupported Media Type
        if "Missing file" in error_msg:
             return jsonify({"error": "Bad request: missing form field 'file'"}), 400
        return jsonify({"error": error_msg}), 400 # 400 Bad Request pour les autres erreurs

    except Exception as e:
        # Erreur interne non gérée
        # 🚨 AJOUTEZ CES LIGNES POUR LE DEBUG
        import traceback
        print("🔴 ERREUR CRITIQUE DANS L'UPLOAD :")
        print(e)
        traceback.print_exc() 
        # -------------------------------------
        return jsonify({"error": "Internal server error"}), 500


# -----------------------------------------------------
# 2. GET /api/photos/{photo_id} (Servage Binaire Public)
# -----------------------------------------------------
@photo_bp.route("/<int:photo_id>", methods=["GET"])
def get_photo_public(photo_id: int):
    """
    Sert le fichier binaire. La photo_id est l'ID BDD.
    """
    try:
        # Le service récupère l'objet BDD, reconstruit le chemin et sert le fichier.
        # La fonction get_photo_binary utilise send_from_directory.
        return get_photo_binary(photo_id) 
        
    except NotFoundError:
        # 404 si l'ID n'existe pas en BDD ou si le fichier physique est manquant
        return jsonify({"error": "Not found"}), 404
        
    except Exception as e:
        # Erreur interne pendant le servage
        return jsonify({"error": "Internal server error"}), 500