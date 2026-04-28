from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backpatas.extensions import db
from backpatas.models.usuario import Usuario
from backpatas.utils.decorators import roles_required


from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.perro import Perro
from backpatas.models.solicitud import Solicitud
from backpatas.models.adopcion import Adopcion

user_bp = Blueprint("users", __name__, url_prefix="/users")


# =====================================================
# 🔵 ADMIN - GESTIÓN DE USUARIOS (RF-028)
# =====================================================


# 1️⃣ LISTAR USUARIOS
@user_bp.get("/usuarios")
@jwt_required()
@roles_required("admin")
def listar_usuarios():
    """
    Listar usuarios (Admin)
    ---
    tags:
      - Administracion - Usuarios
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: estado
        type: integer
        required: false
        description: Filtrar por estado (1 = activo, 0 = inactivo)
      - in: query
        name: q
        type: string
        required: false
        description: Buscar por nombre o email
    responses:
      200:
        description: Lista de usuarios
      401:
        description: No autorizado
      403:
        description: Acceso solo para admin
    """
    estado = request.args.get("estado")
    q = request.args.get("q")

    query = Usuario.query

    if estado is not None:
        query = query.filter(Usuario.estado == int(estado))

    if q:
        query = query.filter(
            (Usuario.nombre.ilike(f"%{q}%")) |
            (Usuario.email.ilike(f"%{q}%"))
        )

    usuarios = query.all()

    return jsonify([u.to_dict() for u in usuarios]), 200


# 2️⃣ VER DETALLE
@user_bp.get("/usuarios/<int:usuario_id>")
@jwt_required()
@roles_required("admin")
def obtener_usuario(usuario_id):
    """
    Obtener detalle de usuario
    ---
    tags:
      - Administracion - Usuarios
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
    responses:
      200:
        description: Datos del usuario
      404:
        description: Usuario no encontrado
    """
    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    return jsonify(usuario.to_dict()), 200


# 3️⃣ EDITAR USUARIO
@user_bp.patch("/usuarios/<int:usuario_id>")
@jwt_required()
@roles_required("admin")
def actualizar_usuario(usuario_id):
    """
    Actualizar usuario (sin cambiar rol)
    ---
    tags:
      - Administracion - Usuarios
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            identificacion:
              type: string
            estado:
              type: integer
              example: 1
    responses:
      200:
        description: Usuario actualizado correctamente
      400:
        description: No se enviaron datos
      404:
        description: Usuario no encontrado
    """
    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"msg": "No se enviaron datos"}), 400

    if "nombre" in data:
        usuario.nombre = data["nombre"]

    if "identificacion" in data:
        usuario.identificacion = data["identificacion"]

    if "estado" in data:
        usuario.estado = data["estado"]

    db.session.commit()

    return jsonify({
        "msg": "Usuario actualizado correctamente",
        "usuario": usuario.to_dict()
    }), 200


# 4️⃣ ELIMINACIÓN LÓGICA
@user_bp.delete("/usuarios/<int:usuario_id>")
@jwt_required()
@roles_required("admin")
def eliminar_usuario(usuario_id):
    """
    Desactivar usuario (eliminación lógica)
    ---
    tags:
      - Administracion - Usuarios
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
    responses:
      200:
        description: Usuario desactivado correctamente
      404:
        description: Usuario no encontrado
      400:
        description: No puedes desactivarte a ti mismo
    """
    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    current_user_id = int(get_jwt_identity())

    if usuario.id == current_user_id:
        return jsonify({"msg": "No puedes desactivarte a ti mismo"}), 400

    usuario.estado = 0
    db.session.commit()

    return jsonify({"msg": "Usuario desactivado correctamente"}), 200