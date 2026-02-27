from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required

from backpatas.models.banner import Banner
from backpatas.models.fundacion import Fundacion  # si tu modelo se llama así


banner_bp = Blueprint("banners", __name__, url_prefix="/banners")



# ✅ Público: banners activos
@banner_bp.get("/")
def listar_banners_publicos():
    """
    Listar banners públicos activos
    ---
    tags:
      - Contenido - Banners
    parameters:
      - in: query
        name: fundacion_id
        type: integer
        required: false
        description: Si se envía, retorna banners globales + los de esa fundación
    responses:
      200:
        description: Lista de banners activos
    """
    fundacion_id = request.args.get("fundacion_id", type=int)

    q = Banner.query.filter(Banner.activo == True)

    if fundacion_id is not None:
        q = q.filter((Banner.fundacion_id == None) | (Banner.fundacion_id == fundacion_id))
    else:
        q = q.filter(Banner.fundacion_id == None)

    banners = q.order_by(Banner.orden.asc().nullslast(), Banner.id.desc()).all()
    return jsonify([b.to_dict() for b in banners]), 200


from backpatas.routes.solicitud_routes import _get_fundacion_from_user


# ✅ Listar para panel
@banner_bp.get("/listar")
@jwt_required()
def listar_banners_panel():
    """
    Listar banners para panel administrativo
    ---
    tags:
      - Contenido - Banners
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de banners según rol
      403:
        description: Rol no permitido
      404:
        description: Fundación no encontrada
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    if rol == "admin":
        banners = Banner.query.order_by(Banner.id.desc()).all()
        return jsonify([b.to_dict() for b in banners]), 200

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404

        banners = (
            Banner.query
            .filter(Banner.fundacion_id == fundacion.id)
            .order_by(Banner.id.desc())
            .all()
        )
        return jsonify([b.to_dict() for b in banners]), 200

    return jsonify({"msg": "Rol no permitido", "rol": rol}), 403


# ✅ Crear banner
@banner_bp.post("/crear")
@jwt_required()
def crear_banner():
    """
    Crear nuevo banner
    ---
    tags:
      - Contenido - Banners
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - titulo
          properties:
            titulo:
              type: string
              example: "Gran jornada de adopción"
            descripcion:
              type: string
            imagen_url:
              type: string
            activo:
              type: boolean
              example: true
            orden:
              type: integer
              example: 1
            fundacion_id:
              type: integer
              example: 2
    responses:
      201:
        description: Banner creado correctamente
      400:
        description: Validación incorrecta
      403:
        description: Rol no permitido
      404:
        description: Fundación no encontrada
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")
    data = request.get_json() or {}

    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        return jsonify({"msg": "titulo es obligatorio"}), 400

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404
        fundacion_id = fundacion.id

    elif rol == "admin":
        fundacion_id = data.get("fundacion_id", None)

        if fundacion_id is not None:
            f = Fundacion.query.get(fundacion_id)
            if not f:
                return jsonify({"msg": "fundacion_id no existe"}), 400

    else:
        return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

    orden = data.get("orden")

    if orden is None:
        max_orden = (
            db.session.query(db.func.max(Banner.orden))
            .filter(Banner.fundacion_id == fundacion_id)
            .scalar()
        )
        orden = (max_orden or 0) + 1
    else:
        existe = Banner.query.filter_by(
            fundacion_id=fundacion_id,
            orden=orden
        ).first()

        if existe:
            return jsonify({"msg": f"Ya existe un banner con orden {orden} en este grupo"}), 400

    banner = Banner(
        titulo=titulo,
        descripcion=data.get("descripcion"),
        imagen_url=data.get("imagen_url"),
        activo=bool(data.get("activo", True)),
        orden=orden,
        fundacion_id=fundacion_id,
        created_by=user_id
    )

    db.session.add(banner)
    db.session.commit()
    return jsonify(banner.to_dict()), 201


# ✅ Editar banner
@banner_bp.patch("/<int:banner_id>/editar")
@jwt_required()
def editar_banner(banner_id):
    """
    Editar banner existente
    ---
    tags:
      - Contenido - Banners
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: banner_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            titulo:
              type: string
            descripcion:
              type: string
            imagen_url:
              type: string
            activo:
              type: boolean
            orden:
              type: integer
            fundacion_id:
              type: integer
    responses:
      200:
        description: Banner actualizado
      403:
        description: No autorizado
      404:
        description: Banner no encontrado
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")
    data = request.get_json() or {}

    banner = Banner.query.get(banner_id)
    if not banner:
        return jsonify({"msg": "Banner no encontrado"}), 404

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404
        if banner.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado para editar este banner"}), 403

    elif rol != "admin":
        return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

    if "titulo" in data:
        banner.titulo = (data.get("titulo") or "").strip()
    if "descripcion" in data:
        banner.descripcion = data.get("descripcion")
    if "imagen_url" in data:
        banner.imagen_url = data.get("imagen_url")
    if "activo" in data:
        banner.activo = bool(data.get("activo"))
    if "orden" in data:
        banner.orden = int(data.get("orden")) if data.get("orden") is not None else None

    if rol == "admin" and "fundacion_id" in data:
        new_fid = data.get("fundacion_id", None)
        if new_fid is not None:
            f = Fundacion.query.get(new_fid)
            if not f:
                return jsonify({"msg": "fundacion_id no existe"}), 400
        banner.fundacion_id = new_fid

    if not banner.titulo:
        return jsonify({"msg": "titulo no puede quedar vacío"}), 400

    db.session.commit()
    return jsonify(banner.to_dict()), 200


# ✅ Toggle activo
@banner_bp.patch("/<int:banner_id>/toggle")
@jwt_required()
def toggle_banner(banner_id):
    """
    Cambiar estado activo del banner
    ---
    tags:
      - Contenido - Banners
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: banner_id
        required: true
        type: integer
    responses:
      200:
        description: Estado actualizado
      403:
        description: No autorizado
      404:
        description: Banner no encontrado
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    banner = Banner.query.get(banner_id)
    if not banner:
        return jsonify({"msg": "Banner no encontrado"}), 404

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404
        if banner.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado para cambiar estado de este banner"}), 403

    elif rol != "admin":
        return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

    banner.activo = not bool(banner.activo)
    db.session.commit()
    return jsonify({"msg": "Estado actualizado", "activo": banner.activo, "banner": banner.to_dict()}), 200


# ✅ Eliminar lógico
@banner_bp.delete("/<int:banner_id>/eliminar")
@jwt_required()
def eliminar_banner(banner_id):
    """
    Eliminar lógico (desactivar) banner
    ---
    tags:
      - Contenido - Banners
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: banner_id
        required: true
        type: integer
    responses:
      200:
        description: Banner desactivado
      403:
        description: No autorizado
      404:
        description: Banner no encontrado
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    banner = Banner.query.get(banner_id)
    if not banner:
        return jsonify({"msg": "Banner no encontrado"}), 404

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404
        if banner.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado para eliminar este banner"}), 403

    elif rol != "admin":
        return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

    banner.activo = False
    db.session.commit()
    return jsonify({"msg": "Banner desactivado"}), 200