from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backpatas.extensions import db
from backpatas.models.fundacion import Fundacion
from backpatas.models.usuario import Usuario
from backpatas.utils.decorators import roles_required

fundacion_bp = Blueprint("fundacion", __name__)

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required
from backpatas.models.fundacion import Fundacion
from backpatas.models.usuario import Usuario

fundacion_bp = Blueprint("fundaciones", __name__, url_prefix="/fundaciones")


@fundacion_bp.get("/admin/listar")
@jwt_required()
@roles_required("admin")
def listar_fundaciones_admin():
    """
    Listar fundaciones (Admin)
    ---
    tags:
      - Administración - Fundaciones
    security:
      - BearerAuth: []
    parameters:
      - name: q
        in: query
        type: string
        required: false
        description: Filtro por nombre de fundación (búsqueda parcial)
    responses:
      200:
        description: Lista de fundaciones
        schema:
          type: array
          items:
            type: object
            properties:
              id: { type: integer, example: 1 }
              identificacion: { type: string, example: "900123456" }
              logo_url: { type: string, example: "https://..." }
              nombre: { type: string, example: "Fundación Huellitas" }
              contacto: { type: string, example: "3200000000" }
      401:
        description: Token inválido o faltante
      403:
        description: No autorizado (no es admin)
    """
    q = request.args.get("q", type=str)

    query = Fundacion.query
    if q:
        query = query.filter(Fundacion.nombre.ilike(f"%{q}%"))

    fundaciones = query.order_by(Fundacion.id.desc()).all()
    return jsonify([f.to_dict() for f in fundaciones]), 200


@fundacion_bp.get("/admin/<int:fundacion_id>")
@jwt_required()
@roles_required("admin")
def detalle_fundacion_admin(fundacion_id):
    """
    Obtener detalle de una fundación (Admin)
    ---
    tags:
      - Administración - Fundaciones
    security:
      - BearerAuth: []
    parameters:
      - name: fundacion_id
        in: path
        type: integer
        required: true
        description: ID de la fundación
    responses:
      200:
        description: Datos de la fundación
        schema:
          type: object
          properties:
            id: { type: integer, example: 1 }
            identificacion: { type: string, example: "900123456" }
            logo_url: { type: string, example: "https://..." }
            nombre: { type: string, example: "Fundación Huellitas" }
            contacto: { type: string, example: "3200000000" }
      404:
        description: Fundación no encontrada
      401:
        description: Token inválido o faltante
      403:
        description: No autorizado (no es admin)
    """
    fundacion = Fundacion.query.get(fundacion_id)
    if not fundacion:
        return jsonify({"msg": "Fundación no encontrada"}), 404

    return jsonify(fundacion.to_dict()), 200


@fundacion_bp.patch("/admin/<int:fundacion_id>")
@jwt_required()
@roles_required("admin")
def editar_fundacion_admin(fundacion_id):
    """
    Editar fundación (Admin)
    ---
    tags:
      - Administración - Fundaciones
    security:
      - BearerAuth: []
    parameters:
      - name: fundacion_id
        in: path
        type: integer
        required: true
        description: ID de la fundación
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Fundación Huellitas"
            logo_url:
              type: string
              example: "https://mi-cdn/logo.png"
            contacto:
              type: string
              example: "3200000000"
            identificacion:
              type: string
              example: "900123456"
    responses:
      200:
        description: Fundación actualizada
        schema:
          type: object
          properties:
            msg: { type: string, example: "Fundación actualizada correctamente" }
            fundacion:
              type: object
              properties:
                id: { type: integer, example: 1 }
                identificacion: { type: string, example: "900123456" }
                logo_url: { type: string, example: "https://..." }
                nombre: { type: string, example: "Fundación Huellitas" }
                contacto: { type: string, example: "3200000000" }
      400:
        description: Datos inválidos
      404:
        description: Fundación no encontrada
      401:
        description: Token inválido o faltante
      403:
        description: No autorizado (no es admin)
    """
    fundacion = Fundacion.query.get(fundacion_id)
    if not fundacion:
        return jsonify({"msg": "Fundación no encontrada"}), 404

    data = request.get_json() or {}

    if "nombre" in data:
        fundacion.nombre = data["nombre"]
    if "logo_url" in data:
        fundacion.logo_url = data["logo_url"]
    if "contacto" in data:
        fundacion.contacto = data["contacto"]
    if "identificacion" in data:
        fundacion.identificacion = data["identificacion"]

    db.session.commit()

    return jsonify({
        "msg": "Fundación actualizada correctamente",
        "fundacion": fundacion.to_dict()
    }), 200


@fundacion_bp.get("/me")
@jwt_required()
@roles_required("fundacion")
def mi_fundacion():
    """
    Obtener perfil de mi fundación (Rol: fundación)
    ---
    tags:
      - Fundaciones
    security:
      - BearerAuth: []
    responses:
      200:
        description: Perfil de la fundación autenticada
        schema:
          type: object
          properties:
            id: { type: integer, example: 1 }
            identificacion: { type: string, example: "900123456" }
            logo_url: { type: string, example: "https://..." }
            nombre: { type: string, example: "Fundación Huellitas" }
            contacto: { type: string, example: "3200000000" }
      404:
        description: Fundación no encontrada para el usuario autenticado
      401:
        description: Token inválido o faltante
      403:
        description: No autorizado (no es fundación)
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)

    fundacion = Fundacion.query.filter_by(identificacion=usuario.identificacion).first()
    if not fundacion:
        return jsonify({"msg": "Fundación no encontrada"}), 404

    return jsonify(fundacion.to_dict()), 200


@fundacion_bp.patch("/me")
@jwt_required()
@roles_required("fundacion")
def editar_mi_fundacion():
    """
    Actualizar perfil de mi fundación (Rol: fundación)
    ---
    tags:
      - Fundaciones
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            logo_url:
              type: string
              example: "https://mi-cdn/logo.png"
            contacto:
              type: string
              example: "3200000000"
    responses:
      200:
        description: Perfil actualizado
        schema:
          type: object
          properties:
            msg: { type: string, example: "Perfil actualizado correctamente" }
            fundacion:
              type: object
              properties:
                id: { type: integer, example: 1 }
                identificacion: { type: string, example: "900123456" }
                logo_url: { type: string, example: "https://..." }
                nombre: { type: string, example: "Fundación Huellitas" }
                contacto: { type: string, example: "3200000000" }
      404:
        description: Fundación no encontrada
      401:
        description: Token inválido o faltante
      403:
        description: No autorizado (no es fundación)
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)

    fundacion = Fundacion.query.filter_by(identificacion=usuario.identificacion).first()
    if not fundacion:
        return jsonify({"msg": "Fundación no encontrada"}), 404

    data = request.get_json() or {}

    if "logo_url" in data:
        fundacion.logo_url = data["logo_url"]
    if "contacto" in data:
        fundacion.contacto = data["contacto"]

    db.session.commit()

    return jsonify({
        "msg": "Perfil actualizado correctamente",
        "fundacion": fundacion.to_dict()
    }), 200

@fundacion_bp.post("/crear-con-usuario")
@jwt_required()
@roles_required("admin")
def crear_fundacion_con_usuario():
    """
    Crear fundación junto con su usuario (solo admin)
    ---
    tags:
      - Fundaciones
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - identificacion
            - nombre_fundacion
            - contacto
            - nombre_usuario
            - email_usuario
            - password
          properties:
            identificacion:
              type: string
              example: "900123456"
            nombre_fundacion:
              type: string
              example: "Fundación Patitas Felices"
            logo_url:
              type: string
              example: "https://miapp.com/logo.png"
            contacto:
              type: string
              example: "contacto@fundacion.com"
            nombre_usuario:
              type: string
              example: "Responsable Fundación"
            email_usuario:
              type: string
              example: "fundacion@login.com"
            password:
              type: string
              example: "Clave123"
    responses:
      201:
        description: Fundación y usuario creados correctamente
      400:
        description: Faltan campos obligatorios
      401:
        description: Token inválido o ausente
      403:
        description: Solo admin puede crear fundaciones
      409:
        description: Email o identificación ya registrados
      500:
        description: Error interno al crear fundación/usuario
    """
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

    # Evitar duplicados: fundación por identificacion
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
        db.session.flush()

        # 2) Crear fundación
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

