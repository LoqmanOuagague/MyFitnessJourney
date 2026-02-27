from flask import Blueprint, request, jsonify, g
from app.services.browse_services import BrowseService
from app.services.errors import ApiError


browse_bp = Blueprint("browse_bp", __name__, url_prefix="/api/browse/listings")

@browse_bp.route("", methods=["GET"])
def browse_listings():
    # Récupération des paramètres de requête (Conversion sécurisée)
    q = request.args.get('q')
    category_id = request.args.get('category_id', type=int)
    min_price_cents = request.args.get('min_price_cents', type=int)
    max_price_cents = request.args.get('max_price_cents', type=int)
    min_total_cents = request.args.get('min_total_cents', type=int)
    max_total_cents = request.args.get('max_total_cents', type=int)
    sort = request.args.get('sort', default='price')
    order = request.args.get('order', default='asc')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=12, type=int)
    
    # Validation basique (par exemple, limites de pagination)
    if sort not in ['price', 'total'] or order not in ['asc', 'desc'] or page_size > 50 or page < 1:
         return jsonify({"error": "Bad request: invalid query parameters."}), 400
         
    try:
        results = BrowseService.get_listings_page(
            q, category_id, min_price_cents, max_price_cents, 
            min_total_cents, max_total_cents, sort, order, page, page_size
        )
        return jsonify(results), 200
        
    except ApiError as e:
        # Erreur interne ou configuration manquante
        return jsonify({"error": str(e)}), 500