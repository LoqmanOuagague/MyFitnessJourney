from flask import Blueprint, request, jsonify
from app.services.categories_services import CategoryService, ConflictError
from app.utils.auth import admin_required

category_bp = Blueprint("categories", __name__,url_prefix="/api/categories")



@category_bp.route("", methods=["GET"])
def get_all_categories():
    cats = CategoryService.get_all()
    return jsonify(cats), 200



@category_bp.route("", methods=["POST"])
@admin_required
def create_category():
    data = request.get_json()
    try:
        cat = CategoryService.create(data)
        return jsonify(cat), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400



@category_bp.route("/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id: int):
    try:
        CategoryService.delete(category_id)
        return "", 204 # 204 No Content pour la suppression
    
    except ConflictError as e: 
        # Gère l'erreur 409 Conflict
        return jsonify({"error": str(e)}), 409
    
    except ValueError as e: 
        # Gère l'erreur 404 Not Found
        return jsonify({"error": "Not found"}), 404
