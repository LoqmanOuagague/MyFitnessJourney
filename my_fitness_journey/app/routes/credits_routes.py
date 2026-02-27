from flask import Blueprint, request, jsonify, g
from app.services.credits_services import CreditService
from app.utils.auth import login_required
from app.services.errors import ApiError, NotFoundError

credit_bp = Blueprint("credits", __name__, url_prefix="/api/credits")

# -----------------------------------------------------
# POST /api/credits/topup
# -----------------------------------------------------
@credit_bp.route("/topup", methods=["POST"])
@login_required
def topup_credits():
    data = request.get_json()
    actor_email = g.user_email
    amount_cents = data.get("amount_cents", 0)
    
    try:
        if not isinstance(amount_cents, int):
            raise ApiError("amount_cents must be an integer.")
            
        result = CreditService.topup_credits(actor_email, amount_cents)
        return jsonify(result), 201
        
    except NotFoundError as e:
        return jsonify({"error": "Not found"}), 404
    except ApiError as e:
        return jsonify({"error": str(e)}), 400

# -----------------------------------------------------
# GET /api/credits/ledger
# -----------------------------------------------------
@credit_bp.route("/ledger", methods=["GET"])
@login_required
def get_ledger():
    actor_email = g.user_email
    try:
        ledger = CreditService.get_ledger(actor_email)
        return jsonify(ledger), 200
    except NotFoundError as e:
        return jsonify({"error": "Not found"}), 404