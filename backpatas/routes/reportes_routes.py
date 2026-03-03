from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backpatas.utils.decorators import roles_required
from backpatas.models.adopcion import Adopcion

from backpatas.utils.decorators import roles_required
from backpatas.models.adopcion import Adopcion
from backpatas.models.perro import Perro
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.routes.solicitud_routes import _get_fundacion_from_user

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")

@reportes_bp.get("/adopciones")
@jwt_required()
@roles_required("admin", "fundacion")
def reporte_adopciones():
    """
    Reporte de adopciones (Admin / Fundación)
    ---
    tags:
      - Reportes
    security:
      - BearerAuth: []

    description: >
      Devuelve el reporte de adopciones registradas.
      - Admin: puede consultar todas las adopciones y filtrar opcionalmente por fundación y por fecha (un día).
      - Fundación: solo puede consultar sus propias adopciones (el filtro fundacion_id se ignora) y filtrar por fecha.

    parameters:
      - in: query
        name: fundacion_id
        required: false
        type: integer
        example: 1
        description: >
          Solo Admin. Filtra adopciones por fundación. Si el rol es fundación, este valor se ignora.
      - in: query
        name: fecha
        required: false
        type: string
        example: "2026-03-03"
        description: Filtrar por una fecha exacta (YYYY-MM-DD)

    responses:
      200:
        description: Reporte de adopciones
      400:
        description: Parámetros inválidos (fecha)
      401:
        description: Token inválido o ausente
      403:
        description: No autorizado
    """

    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    fecha = request.args.get("fecha")  # YYYY-MM-DD
    fundacion_id_param = request.args.get("fundacion_id", type=int)

    q = Adopcion.query

    # Fundación: forzar su fundacion_id
    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403
        q = q.filter(Adopcion.fundacion_id == fundacion.id)
    else:
        # Admin: opcional por fundacion_id
        if fundacion_id_param:
            q = q.filter(Adopcion.fundacion_id == fundacion_id_param)

    # Filtro por fecha exacta (un solo día)
    if fecha:
        try:
            inicio = datetime.strptime(fecha, "%Y-%m-%d")
            fin = inicio.replace(hour=23, minute=59, second=59)
            q = q.filter(Adopcion.fecha_adopcion >= inicio, Adopcion.fecha_adopcion <= fin)
        except Exception:
            return jsonify({"msg": "Formato de fecha inválido. Use YYYY-MM-DD (ej: 2026-03-03)"}), 400

    adopciones = q.order_by(Adopcion.fecha_adopcion.desc()).all()

    resultado = []
    for a in adopciones:
        perro = Perro.query.get(a.perro_id)
        usuario = Usuario.query.get(a.usuario_id)
        fundacion = Fundacion.query.get(a.fundacion_id)

        resultado.append({
            "id": a.id,
            "fecha_adopcion": a.fecha_adopcion.isoformat() if a.fecha_adopcion else None,
            "observaciones": a.observaciones,
            "perro_id": a.perro_id,
            "perro_nombre": perro.nombre if perro else None,
            "usuario_id": a.usuario_id,
            "usuario_nombre": usuario.nombre if usuario else None,
            "fundacion_id": a.fundacion_id,
            "fundacion_nombre": fundacion.nombre if fundacion else None
        })

    return jsonify({
        "total": len(resultado),
        "adopciones": resultado
    }), 200


@reportes_bp.get("/adopciones-simple")
@jwt_required()
@roles_required("admin", "fundacion")
def adopciones_simple():
    """
    Listado simple de adopciones (Admin / Fundación)
    ---
    tags:
      - Reportes
    security:
      - BearerAuth: []
    description: >
      Devuelve adopciones registradas sin filtros.
      - Admin: obtiene todas las adopciones del sistema.
      - Fundación: obtiene únicamente las adopciones asociadas a su fundación.
    responses:
      200:
        description: Lista de adopciones
      401:
        description: Token inválido o ausente
      403:
        description: No autorizado
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    q = Adopcion.query

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403
        q = q.filter(Adopcion.fundacion_id == fundacion.id)

    adopciones = q.order_by(Adopcion.id.desc()).all()

    resultado = []
    for a in adopciones:
        resultado.append({
            "id": a.id,
            "solicitud_id": a.solicitud_id,
            "perro_id": a.perro_id,
            "usuario_id": a.usuario_id,
            "fundacion_id": a.fundacion_id,
            "fecha_adopcion": a.fecha_adopcion.isoformat() if a.fecha_adopcion else None,
            "observaciones": a.observaciones
        })

    return jsonify({
        "total": len(resultado),
        "adopciones": resultado
    }), 200