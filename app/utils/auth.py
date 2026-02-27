from flask import request, jsonify, g
from functools import wraps

# L'e-mail de l'administrateur est une constante normative (Tier A)
ADMIN_EMAIL = "admin@imt.test"

def get_current_user_email():
    """Récupère l'e-mail de l'utilisateur depuis l'en-tête X-User-Email."""
    # Flask met les noms de headers en majuscule dans le dictionnaire headers
    return request.headers.get("X-User-Email")


def login_required(f):
    """
    Décorateur pour les endpoints nécessitant une authentification.
    Retourne 401 si le header X-User-Email est manquant.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = get_current_user_email()
        
        if not user_email:
            # Réponse 401 Unauthorized (selon OpenAPI)
            return jsonify({
                "error": "Unauthorized: missing X-User-Email"
            }), 401
        
        # Stocke l'e-mail dans l'objet global Flask (g) pour un accès facile
        g.user_email = user_email
        
        # NOTE IMPORTANTE : Pour le Tier A strict, nous n'avons pas besoin de vérifier
        # l'existence de l'e-mail dans la DB ici, mais c'est une bonne pratique.
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):

    """
    Décorateur pour les endpoints nécessitant les droits Admin.
    Nécessite login_required ET que l'e-mail soit ADMIN_EMAIL.
    Retourne 403 Forbidden si les droits sont insuffisants.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = get_current_user_email()
        if not user_email:
           return jsonify({
               "error": "Unauthorized: missing X-User-Email"
           }), 401
        g.user_email=user_email
        if user_email !=ADMIN_EMAIL:
            return jsonify({ 
               "error": "Forbidden: admin only"
            }), 403
        return f(*args,**kwargs)
    return decorated_function
