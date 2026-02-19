from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backpatas.extensions import db
from backpatas.models.fundacion import Fundacion
from backpatas.models.usuario import Usuario
from backpatas.utils.decorators import roles_required

fundacion_bp = Blueprint("fundacion", __name__)


@fundacion_bp.post("/crear-con-usuario")
@jwt_required()
@roles_required("admin")
def crear_fundacion_con_usuario():
    data = request.get_json() or {}

    # ---- Datos de fundación ----
    identificacion = data.get("identificacion")
    nombre_fundacion = data.get("nombre_fundacion")
    logo_url = data.get("logo_url")
    contacto = data.get("contacto")  # normalmente email institucional

    # ---- Datos del usuario (cuenta) ----
    nombre_usuario = data.get("nombre_usuario")  # nombre del responsable o cuenta
    email_usuario = data.get("email_usuario")    # email para login (ideal: igual a contacto)
    password_usuario = data.get("password")

    # Validaciones mínimas
    if not identificacion or not nombre_fundacion or not contacto:
        return jsonify({"msg": "Faltan campos de fundación (identificacion, nombre_fundacion, contacto)"}), 400

    if not nombre_usuario or not email_usuario or not password_usuario:
        return jsonify({"msg": "Faltan campos de usuario (nombre_usuario, email_usuario, password)"}), 400

    # Evitar duplicados: email usuario
    if Usuario.query.filter_by(email=email_usuario).first():
        return jsonify({"msg": "El email de usuario ya está registrado"}), 409

    # Evitar duplicados: fundación por identificacion (si aplica en tu negocio)
    if Fundacion.query.filter_by(identificacion=identificacion).first():
        return jsonify({"msg": "Ya existe una fundación con esa identificación"}), 409

    try:
        # 1) Crear usuario con rol fundación
        u = Usuario(
            identificacion=identificacion,
            nombre=nombre_usuario,
            email=email_usuario,
            rol="fundacion",
            estado=1
        )
        u.set_password(password_usuario)
        db.session.add(u)
        db.session.flush()  # fuerza INSERT del usuario antes de crear fundación

        # 2) Crear fundación (vinculada por identificacion/contacto)
        f = Fundacion(
            identificacion=identificacion,
            logo_url=logo_url,
            nombre=nombre_fundacion,
            contacto=contacto
        )
        db.session.add(f)

        # 3) Confirmar todo
        db.session.commit()

        return jsonify({
            "msg": "Fundación y usuario fundación creados",
            "fundacion": f.to_dict(),
            "usuario_fundacion": u.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creando fundación/usuario", "error": str(e)}), 500
