from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required

from backpatas.models.adopcion import Adopcion
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.seguimiento_post_adopcion import SeguimientoPostAdopcion


seguimientos_bp = Blueprint("seguimientos", __name__, url_prefix="/seguimientos")


def _get_rol():
    claims = get_jwt()
    return claims.get("rol")  # así lo vienes usando


def _get_fundacion_id_from_user(user_id: int):
    """
    En tu sistema: Usuario.identificacion se asocia con Fundacion.identificacion
    Retorna fundacion.id o None.
    """
    usuario = Usuario.query.get(user_id)
    if not usuario or not usuario.identificacion:
        return None

    fundacion = Fundacion.query.filter_by(identificacion=usuario.identificacion).first()
    return fundacion.id if fundacion else None


@seguimientos_bp.post("/")
@jwt_required()
@roles_required("fundacion")
def crear_seguimiento():
    """
    Crear seguimiento post adopción (Fundación)
    ---
    tags:
      - Seguimientos
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - adopcion_id
            - estado_mascota
            - medio_seguimiento
          properties:
            adopcion_id:
              type: integer
              example: 12
            estado_mascota:
              type: string
              example: "Bueno"
            medio_seguimiento:
              type: string
              example: "WhatsApp"
            url_evidencia:
              type: string
              example: "https://drive.google.com/..."
            observaciones:
              type: string
              example: "Se adaptó bien, come normal."
    responses:
      201:
        description: Seguimiento creado
      400:
        description: Validación
      403:
        description: No autorizado
      404:
        description: Adopción no existe
    """
    data = request.get_json(silent=True) or {}

    adopcion_id = data.get("adopcion_id")
    estado_mascota = (data.get("estado_mascota") or "").strip()
    medio_seguimiento = (data.get("medio_seguimiento") or "").strip()
    url_evidencia = (data.get("url_evidencia") or "").strip() or None
    observaciones = (data.get("observaciones") or "").strip() or None

    if not adopcion_id:
        return jsonify({"msg": "adopcion_id es requerido"}), 400
    if not estado_mascota:
        return jsonify({"msg": "estado_mascota es requerido"}), 400
    if not medio_seguimiento:
        return jsonify({"msg": "medio_seguimiento es requerido"}), 400

    adopcion = Adopcion.query.get(adopcion_id)
    if not adopcion:
        return jsonify({"msg": "Adopción no encontrada"}), 404

    user_id = int(get_jwt_identity())
    fundacion_id_usuario = _get_fundacion_id_from_user(user_id)
    if not fundacion_id_usuario:
        return jsonify({"msg": "No se pudo asociar la fundación del usuario autenticado"}), 403

    # Regla: solo la fundación dueña de la adopción puede registrar seguimiento
    if adopcion.fundacion_id != fundacion_id_usuario:
        return jsonify({"msg": "No autorizado: la adopción no pertenece a tu fundación"}), 403

    seguimiento = SeguimientoPostAdopcion(
        adopcion_id=adopcion_id,
        fecha_seguimiento=datetime.utcnow(),  # puedes omitirlo y usar el default SQL, pero así queda consistente
        estado_mascota=estado_mascota,
        medio_seguimiento=medio_seguimiento,
        url_evidencia=url_evidencia,
        observaciones=observaciones,
        registrado_por_usuario_id=user_id
    )

    db.session.add(seguimiento)
    db.session.commit()

    return jsonify({
        "msg": "Seguimiento creado",
        "data": seguimiento.to_dict()
    }), 201

@seguimientos_bp.get("/para-seguimiento")
@jwt_required()
@roles_required("fundacion")
def obtener_adopciones_para_seguimiento():
    """
    Obtener adopciones disponibles para seguimiento
    ---
    tags:
      - Seguimientos
    summary: Lista de adopciones para realizar seguimiento
    description: |
      Retorna las adopciones asociadas a la fundación autenticada.
      Incluye datos del perro, adoptante y fundación.
      Solo accesible para usuarios con rol fundación.
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de adopciones obtenida correctamente
      401:
        description: Usuario no autenticado
      403:
        description: Usuario no autorizado
      404:
        description: Usuario o fundación no encontrada
    """
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)

    if not usuario:
        return jsonify({"message": "Usuario no encontrado"}), 404

    fundacion_id = _get_fundacion_id_from_user(user_id)
    if not fundacion_id:
        return jsonify({"message": "No se pudo asociar la fundación del usuario autenticado"}), 403

    adopciones = (
        Adopcion.query
        .filter_by(fundacion_id=fundacion_id)
        .order_by(Adopcion.fecha_adopcion.desc())
        .all()
    )

    return jsonify({
        "total": len(adopciones),
        "adopciones": [adopcion.to_dict() for adopcion in adopciones]
    }), 200

@seguimientos_bp.get("/<int:adopcion_id>")
@jwt_required()
@roles_required("admin", "fundacion")
def listar_seguimientos_por_adopcion(adopcion_id):
    """
    Listar seguimientos de una adopción (Admin o Fundación dueña)
    ---
    tags:
      - Seguimientos
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: adopcion_id
        required: true
        type: integer
    responses:
      200:
        description: Lista de seguimientos
      403:
        description: No autorizado
      404:
        description: Adopción no existe
    """
    adopcion = Adopcion.query.get(adopcion_id)
    if not adopcion:
        return jsonify({"msg": "Adopción no encontrada"}), 404

    rol = _get_rol()
    user_id = int(get_jwt_identity())

    # Admin ve todo; fundación solo si es dueña
    if rol != "admin":
        fundacion_id_usuario = _get_fundacion_id_from_user(user_id)
        if not fundacion_id_usuario or adopcion.fundacion_id != fundacion_id_usuario:
            return jsonify({"msg": "No autorizado: la adopción no pertenece a tu fundación"}), 403

    seguimientos = (
        SeguimientoPostAdopcion.query
        .filter_by(adopcion_id=adopcion_id)
        .order_by(SeguimientoPostAdopcion.fecha_seguimiento.desc())
        .all()
    )

    return jsonify({
        "adopcion_id": adopcion_id,
        "total": len(seguimientos),
        "data": [s.to_dict() for s in seguimientos]
    }), 200


@seguimientos_bp.get("/admin")
@jwt_required()
@roles_required("admin")
def listar_seguimientos_admin():
    """
    Listado global de seguimientos (Admin)
    ---
    tags:
      - Seguimientos
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: adopcion_id
        required: false
        type: integer
      - in: query
        name: fundacion_id
        required: false
        type: integer
      - in: query
        name: fecha
        required: false
        type: string
        description: Fecha exacta en formato YYYY-MM-DD
        example: "2026-03-03"
    responses:
      200:
        description: Lista global
    """
    adopcion_id = request.args.get("adopcion_id", type=int)
    fundacion_id = request.args.get("fundacion_id", type=int)
    fecha = request.args.get("fecha")  # YYYY-MM-DD

    q = SeguimientoPostAdopcion.query.join(Adopcion, SeguimientoPostAdopcion.adopcion_id == Adopcion.id)

    if adopcion_id:
        q = q.filter(SeguimientoPostAdopcion.adopcion_id == adopcion_id)
    if fundacion_id:
        q = q.filter(Adopcion.fundacion_id == fundacion_id)
    if fecha:
        # Filtrar por fecha exacta (ignorando hora)
        # SQL Server: CAST(datetime as date)
        q = q.filter(db.func.cast(SeguimientoPostAdopcion.fecha_seguimiento, db.Date) == fecha)

    seguimientos = q.order_by(SeguimientoPostAdopcion.fecha_seguimiento.desc()).all()

    return jsonify({
        "total": len(seguimientos),
        "data": [s.to_dict() for s in seguimientos]
    }), 200

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func, distinct

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required

from backpatas.models.adopcion import Adopcion
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.seguimiento_post_adopcion import SeguimientoPostAdopcion

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _rol():
    return (get_jwt() or {}).get("rol")


def _fundacion_id_from_user(user_id: int):
    usuario = Usuario.query.get(user_id)
    if not usuario or not usuario.identificacion:
        return None
    f = Fundacion.query.filter_by(identificacion=usuario.identificacion).first()
    return f.id if f else None


@seguimientos_bp.get("/dashboard-seguimientos")
@jwt_required()
@roles_required("admin", "fundacion")
def dashboard_seguimientos():
    """
    Mini dashboard de seguimientos post adopción (Admin / Fundación)
    ---
    tags:
      - Seguimientos
    security:
      - BearerAuth: []
    description: >
      Devuelve métricas de seguimientos post adopción.
      - Admin: ve todo.
      - Fundación: ve solo adopciones de su fundación.
    responses:
      200:
        description: Dashboard generado
    """
    user_id = int(get_jwt_identity())
    rol = _rol()

    # Base query de adopciones (con filtro si es fundación)
    adop_q = Adopcion.query
    seg_q = SeguimientoPostAdopcion.query.join(Adopcion, SeguimientoPostAdopcion.adopcion_id == Adopcion.id)

    fundacion_id = None
    if rol != "admin":
        fundacion_id = _fundacion_id_from_user(user_id)
        if not fundacion_id:
            return jsonify({"msg": "No se pudo asociar la fundación del usuario autenticado"}), 403
        adop_q = adop_q.filter(Adopcion.fundacion_id == fundacion_id)
        seg_q = seg_q.filter(Adopcion.fundacion_id == fundacion_id)

    total_adopciones = adop_q.count()

    # adopciones con seguimiento (DISTINCT adopcion_id)
    adopciones_con_seguimiento = (
        db.session.query(func.count(distinct(SeguimientoPostAdopcion.adopcion_id)))
        .select_from(SeguimientoPostAdopcion)
        .join(Adopcion, SeguimientoPostAdopcion.adopcion_id == Adopcion.id)
        .filter(True if rol == "admin" else Adopcion.fundacion_id == fundacion_id)
        .scalar()
    ) or 0

    adopciones_sin_seguimiento = max(total_adopciones - adopciones_con_seguimiento, 0)

    cobertura = 0
    if total_adopciones > 0:
        cobertura = round((adopciones_con_seguimiento / total_adopciones) * 100, 2)

    total_seguimientos = seg_q.count()

    # últimos seguimientos
    ultimos = (
        seg_q.order_by(SeguimientoPostAdopcion.fecha_seguimiento.desc())
        .limit(10)
        .all()
    )

    ultimos_data = []
    for s in ultimos:
        ultimos_data.append({
            "id": s.id,
            "adopcion_id": s.adopcion_id,
            "fecha_seguimiento": s.fecha_seguimiento.isoformat() if s.fecha_seguimiento else None,
            "estado_mascota": s.estado_mascota,
            "medio_seguimiento": s.medio_seguimiento,
            "url_evidencia": s.url_evidencia,
            "observaciones": s.observaciones,
            "registrado_por_usuario_id": s.registrado_por_usuario_id,
        })

    # distribución por estado_mascota
    dist_estado = (
        db.session.query(SeguimientoPostAdopcion.estado_mascota, func.count(SeguimientoPostAdopcion.id))
        .select_from(SeguimientoPostAdopcion)
        .join(Adopcion, SeguimientoPostAdopcion.adopcion_id == Adopcion.id)
        .filter(True if rol == "admin" else Adopcion.fundacion_id == fundacion_id)
        .group_by(SeguimientoPostAdopcion.estado_mascota)
        .order_by(func.count(SeguimientoPostAdopcion.id).desc())
        .all()
    )

    dist_estado_data = [{"estado_mascota": e, "total": c} for e, c in dist_estado]

    # distribución por medio_seguimiento
    dist_medio = (
        db.session.query(SeguimientoPostAdopcion.medio_seguimiento, func.count(SeguimientoPostAdopcion.id))
        .select_from(SeguimientoPostAdopcion)
        .join(Adopcion, SeguimientoPostAdopcion.adopcion_id == Adopcion.id)
        .filter(True if rol == "admin" else Adopcion.fundacion_id == fundacion_id)
        .group_by(SeguimientoPostAdopcion.medio_seguimiento)
        .order_by(func.count(SeguimientoPostAdopcion.id).desc())
        .all()
    )

    dist_medio_data = [{"medio_seguimiento": m, "total": c} for m, c in dist_medio]

    return jsonify({
        "scope": "global" if rol == "admin" else "fundacion",
        "fundacion_id": None if rol == "admin" else fundacion_id,

        "kpis": {
            "total_adopciones": total_adopciones,
            "total_seguimientos": total_seguimientos,
            "adopciones_con_seguimiento": adopciones_con_seguimiento,
            "adopciones_sin_seguimiento": adopciones_sin_seguimiento,
            "cobertura_seguimiento_pct": cobertura
        },
        "distribucion": {
            "por_estado_mascota": dist_estado_data,
            "por_medio_seguimiento": dist_medio_data
        },
        "ultimos_seguimientos": ultimos_data
    }), 200