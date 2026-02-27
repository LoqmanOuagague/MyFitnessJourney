from flask import Blueprint, request, jsonify, g
from app.services.purchases_services import PurchaseService
from app.utils.auth import login_required
from app.services.errors import (
    ApiError, 
    NotFoundError, 
    ForbiddenError, 
    ConflictError, 
    UnauthorizedError
)

purchase_bp = Blueprint("purchases", __name__, url_prefix="/api/purchases")

# -----------------------------------------------------
# 1. LISTER LES ACHATS (GET /api/purchases?role=...)
# -----------------------------------------------------
@purchase_bp.route("", methods=["GET"])
@login_required
def get_purchases():
    actor_email = g.user_email
    # Récupère le paramètre optionnel 'role', par défaut 'buyer'
    role = request.args.get('role', default='buyer')
    
    try:
        purchases = PurchaseService.get_purchases(actor_email, role)
        return jsonify(purchases), 200
        
    except ApiError as e:
        # Gère le cas où le rôle est invalide (ni buyer ni seller)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


# -----------------------------------------------------
# 2. CRÉER UN ACHAT (POST /api/purchases)
# -----------------------------------------------------
@purchase_bp.route("", methods=["POST"])
@login_required
def create_purchase():
    data = request.get_json()
    buyer_email = g.user_email
    
    try:
        purchase = PurchaseService.create_purchase(data, buyer_email)
        return jsonify(purchase), 201
        
    except NotFoundError as e:
        # Listing, Acheteur ou Adresse introuvable
        return jsonify({"error": "Not found"}), 404
        
    except ForbiddenError as e:
        # Tente d'acheter son propre objet
        return jsonify({"error": str(e)}), 403
        
    except ApiError as e:
        # Crédits insuffisants, Listing non actif, Erreur transaction
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        import traceback
        print("==========================================")
        print("❌ ERREUR CRITIQUE DANS CREATE_PURCHASE :")
        print(e)
        traceback.print_exc() 
        print("==========================================")
        # -----------------------------------------------
        return jsonify({"error": "Internal server error"}), 500


# -----------------------------------------------------
# 3. DÉTAIL D'UN ACHAT (GET /api/purchases/{id})
# -----------------------------------------------------
@purchase_bp.route("/<int:purchase_id>", methods=["GET"])
@login_required
def get_purchase(purchase_id: int):
    actor_email = g.user_email
    
    try:
        purchase = PurchaseService.get_purchase_by_id(actor_email, purchase_id)
        return jsonify(purchase), 200
        
    except UnauthorizedError as e:
        # RESPECT TIER A : Si l'utilisateur n'existe pas en base, on renvoie 401
        # pour ne pas révéler l'existence ou non de l'email.
        return jsonify({"error": str(e)}), 401
        
    except NotFoundError as e:
        # L'achat n'existe pas
        return jsonify({"error": str(e)}), 404
        
    except ForbiddenError as e:
        # L'utilisateur n'est ni acheteur, ni vendeur, ni admin
        return jsonify({"error": str(e)}), 403


# -----------------------------------------------------
# 4. DÉCLARER RÉCEPTION (POST /api/purchases/{id}/declare)
# -----------------------------------------------------
@purchase_bp.route("/<int:purchase_id>/declare", methods=["POST"])
@login_required
def declare_purchase_outcome(purchase_id: int):
    data = request.get_json()
    actor_email = g.user_email
    
    try:
        result = PurchaseService.declare_outcome(purchase_id, data, actor_email)
        return jsonify(result), 200
        
    except NotFoundError as e:
        return jsonify({"error": "Not found"}), 404
        
    except ForbiddenError as e:
        # Seul l'acheteur peut déclarer
        return jsonify({"error": str(e)}), 403
        
    except ConflictError as e:
        # 🚨 L'achat est déjà clos ou remboursé
        return jsonify({"error": str(e)}), 409
        
    except ApiError as e:
        # Statut invalide (autre que OK, NOT_RECEIVED...)
        return jsonify({"error": str(e)}), 400