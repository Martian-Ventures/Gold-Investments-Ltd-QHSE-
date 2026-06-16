from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User
from werkzeug.security import check_password_hash

api_bp = Blueprint("api", __name__)

@api_bp.route("/token", methods=["POST"])
def token():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"msg":"Bad credentials"}), 401
    access_token = create_access_token(identity={"id": user.id, "email": user.email, "role": user.role})
    return jsonify(access_token=access_token), 200

@api_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    identity = get_jwt_identity()
    return jsonify({"hello": f"Welcome {identity['email']}", "role": identity["role"]})
