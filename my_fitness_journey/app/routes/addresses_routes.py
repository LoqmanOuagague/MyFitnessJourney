# app/routes/addresses_routes.py

from flask import Blueprint, request, jsonify, g
from app.services.addresses_services import AddressService
from app.utils.auth import login_required
from app.services.errors import ApiError, NotFoundError, ForbiddenError, UnauthorizedError

address_bp = Blueprint("addresses", __name__, url_prefix="/api/addresses")

# -----------------------------------------------------
# GET /api/addresses 
# -----------------------------------------------------
@address_bp.route("", methods=["GET"])
@login_required
def get_addresses():
    actor_email = g.user_email
    
    try:
        # List addresses
        addresses = AddressService.get_addresses(actor_email)
        return jsonify(addresses), 200
    except UnauthorizedError as e:
        return jsonify({"error": str(e)}), 404   
    except NotFoundError as e :
        return jsonify({"error": str(e)}), 404  


# -----------------------------------------------------
# POST /api/addresses 
# -----------------------------------------------------
@address_bp.route("", methods=["POST"])
@login_required
def create_address():
    actor_email = g.user_email
    try:
        # Add address
        data = request.get_json()
        address = AddressService.add_address(data, actor_email)
        return jsonify(address), 201
            
    except ApiError as e:
        return jsonify({"error": str(e)}), 400
    except UnauthorizedError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

# -----------------------------------------------------
# PUT /api/addresses/{id} (Update)
# -----------------------------------------------------
@address_bp.route("/<int:address_id>", methods=["PUT"])
@login_required
def update_address(address_id: int):
    actor_email = g.user_email
    try:
        # Update address
        data = request.get_json()
        address = AddressService.update_address(address_id, data, actor_email)
        return jsonify(address), 200

    except NotFoundError as e:
        return jsonify({"error": "Not found"}), 404
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403

# -----------------------------------------------------
# PUT /api/addresses/{id} (Update) & DELETE /api/addresses/{id} (Delete)
# -----------------------------------------------------
@address_bp.route("/<int:address_id>", methods=["DELETE"])
@login_required
def delete_address(address_id: int):
    actor_email = g.user_email
    
    try:
        AddressService.delete_address(address_id, actor_email)
        return "", 204 # 204 No Content
            
    except NotFoundError as e:
        return jsonify({"error": "Not found"}), 404
    except ForbiddenError as e:
        return jsonify({"error": str(e)}), 403
    except ApiError as e:
        return jsonify({"error": str(e)}), 400