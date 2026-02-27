from flask import Blueprint, request, jsonify, g
from app.services.listings_services import ListingService
from app.services.browse_services import BrowseService
from app.utils.auth import admin_required, login_required
from app.services.errors import ApiError

listing_bp = Blueprint("listing_bp", __name__, url_prefix="/api/listings")


#  GET : récupérer un listing par son id
@listing_bp.route("/<int:listing_id>", methods=["GET"])
def get_listing(listing_id):
    try:
        result = ListingService.get(listing_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


#  POST : créer un nouveau listing
@listing_bp.route("", methods=["POST"])
@login_required
def create_listing():
    try:
        data = request.get_json()
        seller_email = g.user_email
        result = ListingService.create(data, seller_email)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# PUT : mise à jour d’un listing existant
@listing_bp.route("/<int:listing_id>", methods=["PUT"])
@login_required
def update_listing(listing_id):
    try:
        email = g.user_email
        data = request.get_json()
        result = ListingService.update(email, listing_id, data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


#  DELETE : suppression d’un listing

@listing_bp.route("/<int:listing_id>", methods=["DELETE"])
@login_required
def delete_listing(listing_id):
    try:
        email = g.user_email
        result = ListingService.delete(listing_id, email)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
