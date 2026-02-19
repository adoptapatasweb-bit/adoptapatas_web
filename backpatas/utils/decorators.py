from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            rol = claims.get("rol")

            if rol not in roles:
                return jsonify({"msg": "Acceso denegado", "rol": rol}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
