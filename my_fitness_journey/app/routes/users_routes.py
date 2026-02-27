from flask import Blueprint, request, jsonify
from app.services.users_services import UserService
from app.utils.auth import admin_required

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.route("", methods=["GET"])
def get_all_users():
    users = UserService.get_all()
    return jsonify(users), 200


@user_bp.route("", methods=["POST"])
def create_user():
    data = request.get_json()
    try:
        user = UserService.create(data)
        return jsonify(user), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/<string:email>", methods=["DELETE"])
@admin_required
def delete_user(email:str):
    #data = request.get_json()
    #email = data.get("email")
    if not email:
        return jsonify({"error": "email required"})
    try: 
        UserService.delete(email)
        return "", 204
    except ValueError as e: 
        return jsonify({"error": str(e)}), 404

