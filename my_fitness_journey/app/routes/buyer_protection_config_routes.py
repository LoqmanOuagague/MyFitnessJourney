
from flask import Blueprint, request, jsonify
from app.services.buyer_protection_config_services import BuyerProtectionService
from app.utils.auth import admin_required
from app.services.errors import NotFoundError 

config_bp = Blueprint("config", __name__, url_prefix="/api/config/buyer-protection")

@config_bp.route("", methods=["GET"])
def get_buyer_protection():
    try:
        config = BuyerProtectionService.get_config()
        return jsonify(config), 200
    except NotFoundError as e:
        # Retourne 404 si la table n'est pas initialisée
        return jsonify({"error": "Configuration not initialized"}), 404

@config_bp.route("", methods=["PUT"])
@admin_required  # <-- Admin only!
def set_buyer_protection():
    data = request.get_json()
    # TODO: Validation du format des données (doit contenir ratio_percent et bias_cents)
    
    try:
        config = BuyerProtectionService.update_config(data)
        return jsonify(config), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400