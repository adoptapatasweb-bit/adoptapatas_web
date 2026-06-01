from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backpatas.extensions import db
from backpatas.utils.decorators import roles_required
from backpatas.services.email_service import send_email
from backpatas.models.respuesta_formulario import RespuestaFormulario
from backpatas.models.usuario import Usuario
from backpatas.models.solicitud import Solicitud
from backpatas.models.perro import Perro
from backpatas.models.respuesta_formulario import RespuestaFormulario
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.services.knn_service import build_user_vector, knn_rank_perros

from datetime import datetime
from backpatas.models.solicitud import Solicitud
from backpatas.models.perro import Perro
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.solicitud import Solicitud

solicitud_bp = Blueprint("solicitud", __name__)

# -----------------------------
# ESTADOS (ajusta si tus IDs son distintos)
# -----------------------------
ESTADO_SOL_PENDIENTE = 1
ESTADO_SOL_APROBADA = 2
ESTADO_SOL_RECHAZADA = 3


# -----------------------------
# Helper: obtener fundación del usuario fundación (por NIT/identificacion)
# -----------------------------
def _get_fundacion_from_user(user_id: int):
    u = Usuario.query.get(user_id)
    if not u or not getattr(u, "identificacion", None):
        return None
    return Fundacion.query.filter_by(identificacion=u.identificacion).first()


#TEST DE SMTP
@solicitud_bp.get("/test-email")
def test_email():
    """
    Enviar correo de prueba (SMTP)
    ---
    tags:
      - Solicitudes
    responses:
      200:
        description: Correo enviado (si no hubo error)
    """
    send_email(
        to="erika222.cftr@gmail.com",
        subject="Prueba AdoptaPatas",
        body="Si ves esto, el SMTP funciona correctamente."
    )
    return {"msg": "Correo enviado (si no hubo error)"}


# =========================================================
# POST /solicitudes/crear
# RF-014 + RF-016
# =========================================================
@solicitud_bp.post("/crear")
@jwt_required()
@roles_required("usuario")
def crear_solicitud_con_formulario():
    """
    Crear solicitud con formulario (solo usuario)
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - perro_id
            - formulario
          properties:
            perro_id:
              type: integer
              example: 10
            formulario:
              type: object
              description: Objeto con respuestas del formulario (campos de RespuestaFormulario)
    responses:
      201:
        description: Solicitud creada con formulario + resultado_knn
      400:
        description: Validación (perro_id faltante / perro no disponible / formulario inválido)
      401:
        description: Token inválido o ausente
      403:
        description: Rol no permitido
      404:
        description: Perro no encontrado
      409:
        description: Ya existe una solicitud para este perro
      500:
        description: Error creando solicitud
    """
    data = request.get_json() or {}

    perro_id = data.get("perro_id")
    formulario = data.get("formulario")  # objeto grande con campos como tu tabla

    if not perro_id:
        return jsonify({"msg": "Debe enviar perro_id"}), 400

    if not isinstance(formulario, dict):
        return jsonify({"msg": "Debe enviar formulario como objeto JSON"}), 400

    usuario_id = int(get_jwt_identity())

    perro = Perro.query.get(perro_id)
    if not perro:
        return jsonify({"msg": "Perro no encontrado"}), 404

    if perro.estado_id != 1:
        return jsonify({"msg": "El perro no está disponible"}), 400

    existente = Solicitud.query.filter_by(usuario_id=usuario_id, perro_id=perro_id).first()
    if existente:
        return jsonify({"msg": "Ya existe una solicitud para este perro"}), 409

    try:
        # 1) Crear solicitud
        solicitud = Solicitud(
            usuario_id=usuario_id,
            perro_id=perro_id,
            fecha=datetime.utcnow(),
            estado_id=ESTADO_SOL_PENDIENTE,
            resultado_knn=None
        )
        db.session.add(solicitud)
        db.session.flush()  # ya tenemos solicitud.id

        # 2) Crear respuesta_formulario (1:1)
        rf = RespuestaFormulario(solicitud_id=solicitud.id)

        columnas_validas = {
            c.name for c in RespuestaFormulario.__table__.columns
            if c.name != "solicitud_id"
        }

        for k, v in formulario.items():
            if k in columnas_validas:
                setattr(rf, k, v)

        db.session.add(rf)
        db.session.flush()

        # 3) KNN (antes del commit)
        perros_disponibles = Perro.query.filter_by(estado_id=1).all()
        u_vec = build_user_vector(rf)

        knn = knn_rank_perros(u_vec, perros_disponibles, top_k=5, w_size=0.35)
        ranking = knn["ranking"]

        rank = None
        for idx, item in enumerate(ranking, start=1):
            if item["perro_id"] == int(perro_id):
                rank = idx
                break

        solicitud.resultado_knn = rank

        # 4) Commit atómico
        db.session.commit()

        return jsonify({
            "msg": "Solicitud creada con formulario",
            "resultado_knn": solicitud.resultado_knn,
            "solicitud": solicitud.to_dict(),
            "respuesta_formulario": rf.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creando solicitud", "error": str(e)}), 500


# =========================================================
# GET /solicitudes/listar
# RF-017
# =========================================================
@solicitud_bp.get("/listar")
@jwt_required()
def listar_solicitudes():
    """
    Listar solicitudes según rol (usuario/admin/fundación)
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de solicitudes
      401:
        description: Token inválido o ausente
      403:
        description: Rol no permitido
      404:
        description: Fundación no encontrada para este usuario
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    if rol == "usuario":
        solicitudes = Solicitud.query.filter_by(usuario_id=user_id).order_by(Solicitud.id.desc()).all()
        return jsonify([s.to_dict() for s in solicitudes]), 200

    if rol == "admin":
        solicitudes = Solicitud.query.order_by(Solicitud.id.desc()).all()
        return jsonify([s.to_dict() for s in solicitudes]), 200

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 404

        solicitudes = (
            db.session.query(Solicitud)
            .join(Perro, Perro.id == Solicitud.perro_id)
            .filter(Perro.fundacion_id == fundacion.id)
            .order_by(Solicitud.id.desc())
            .all()
        )
        return jsonify([s.to_dict() for s in solicitudes]), 200

    return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

# =========================================================
# PATCH /solicitudes/<id>/aprobar
# RF-018
# =========================================================
from datetime import datetime

@solicitud_bp.get("/test-aprobacion-email/<int:solicitud_id>")
def test_aprobacion_email(solicitud_id):
    """
    Enviar correo de prueba de aprobación (debug)
    ---
    tags:
      - Solicitudes
    parameters:
      - in: path
        name: solicitud_id
        required: true
        type: integer
    responses:
      200:
        description: Correo de prueba enviado
      404:
        description: Solicitud no encontrada
    """

    solicitud = Solicitud.query.get(solicitud_id)
    if not solicitud:
        return {"msg": "Solicitud no encontrada"}, 404

    perro = Perro.query.get(solicitud.perro_id)
    nombre_perro = perro.nombre if perro else f"ID {solicitud.perro_id}"

    usuario = Usuario.query.get(solicitud.usuario_id)

    if usuario and usuario.email:
        send_email(
            to=usuario.email,
            subject="PRUEBA: Solicitud aprobada",
            body=(
                f"Hola.\n\n"
                f"Tu solicitud #{solicitud.id} para {nombre_perro} fue APROBADA.\n\n"
                f"Motivo: Prueba manual.\n\n"
                f"Equipo AdoptaPatas\n"
            )
        )

    return {"msg": "Correo de prueba enviado"}

from datetime import datetime
from sqlalchemy import and_

from backpatas.models.adopcion import Adopcion

@solicitud_bp.patch("/<int:solicitud_id>/aprobar")
@jwt_required()
@roles_required("admin", "fundacion")
def aprobar_solicitud(solicitud_id):
    """
    Aprobar solicitud (admin o fundación dueña del perro)
    - Cambia estado a APROBADA
    - Rechaza automáticamente otras solicitudes pendientes del mismo perro
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    solicitud = Solicitud.query.get(solicitud_id)
    if not solicitud:
        return jsonify({"msg": "Solicitud no encontrada"}), 404

    if solicitud.estado_id != ESTADO_SOL_PENDIENTE:
        return jsonify({"msg": "Solo solicitudes pendientes pueden aprobarse"}), 409

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403

        perro = Perro.query.get(solicitud.perro_id)
        if not perro or perro.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado: solicitud no pertenece a tu fundación"}), 403

    data = request.get_json() or {}
    motivo = data.get("motivo")
    ahora = datetime.now()

    try:
        # 1) Aprobar esta solicitud
        solicitud.estado_id = ESTADO_SOL_APROBADA
        solicitud.fecha_decision = ahora
        solicitud.decidido_por_usuario_id = user_id
        solicitud.motivo_decision = motivo

        # 2) Rechazar otras pendientes del mismo perro
        otras_pendientes = Solicitud.query.filter(
            and_(
                Solicitud.perro_id == solicitud.perro_id,
                Solicitud.id != solicitud.id,
                Solicitud.estado_id == ESTADO_SOL_PENDIENTE
            )
        ).all()

        motivo_auto = "Rechazada automáticamente: el perro fue asignado a otra solicitud aprobada."

        for s in otras_pendientes:
            s.estado_id = ESTADO_SOL_RECHAZADA
            s.fecha_decision = ahora
            s.decidido_por_usuario_id = user_id
            s.motivo_decision = motivo_auto

        # 3) Registrar adopción (solo una por perro)
        ya_existe = Adopcion.query.filter_by(perro_id=solicitud.perro_id).first()
        if ya_existe:
            db.session.rollback()
            return jsonify({
                "msg": "Este perro ya tiene una adopción registrada.",
                "adopcion_existente": ya_existe.to_dict()
            }), 409

        perro = Perro.query.get(solicitud.perro_id)

        adopcion = Adopcion(
            solicitud_id=solicitud.id,
            perro_id=solicitud.perro_id,
            usuario_id=solicitud.usuario_id,
            fundacion_id=perro.fundacion_id,
            observaciones=motivo
        )
        db.session.add(adopcion)

        db.session.commit()

        return jsonify({
            "msg": "Solicitud aprobada correctamente. Otras pendientes fueron rechazadas automáticamente.",
            "solicitud_aprobada": solicitud.to_dict(),
            "rechazadas_automaticas": [s.to_dict() for s in otras_pendientes]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error aprobando solicitud", "error": str(e)}), 500
# =========================================================
# PATCH /solicitudes/<id>/rechazar
# RF-019
# =========================================================
from datetime import datetime

@solicitud_bp.patch("/<int:solicitud_id>/rechazar")
@jwt_required()
@roles_required("admin", "fundacion")
def rechazar_solicitud(solicitud_id):
    """
    Rechazar solicitud (admin o fundación dueña del perro)
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    solicitud = Solicitud.query.get(solicitud_id)
    if not solicitud:
        return jsonify({"msg": "Solicitud no encontrada"}), 404

    if solicitud.estado_id != ESTADO_SOL_PENDIENTE:
        return jsonify({"msg": "Solo solicitudes pendientes pueden rechazarse"}), 409

    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403

        perro = Perro.query.get(solicitud.perro_id)
        if not perro or perro.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado: solicitud no pertenece a tu fundación"}), 403

    data = request.get_json() or {}
    motivo = data.get("motivo")

    try:
        solicitud.estado_id = ESTADO_SOL_RECHAZADA
        solicitud.fecha_decision = datetime.utcnow()
        solicitud.decidido_por_usuario_id = user_id
        solicitud.motivo_decision = motivo

        db.session.commit()

        return jsonify({
            "msg": "Solicitud rechazada correctamente",
            "solicitud": solicitud.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error rechazando solicitud", "error": str(e)}), 500

# =========================================================
# GET /solicitudes/historial
# RF-020
# =========================================================
@solicitud_bp.get("/historial")
@jwt_required()
def historial_solicitudes():
    """
    Historial de solicitudes finalizadas (aprobadas/rechazadas)
    - Usuario: solo las suyas
    - Fundación: las asociadas a sus perros
    - Admin: todas
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de solicitudes finalizadas
      401:
        description: Token inválido o ausente
      403:
        description: Rol no permitido / fundación no encontrada
    """
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    estados_finales = [ESTADO_SOL_APROBADA, ESTADO_SOL_RECHAZADA]

    q = Solicitud.query.filter(Solicitud.estado_id.in_(estados_finales))

    if rol == "usuario":
        q = q.filter(Solicitud.usuario_id == user_id)

    elif rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403
        q = (
            q.join(Perro, Perro.id == Solicitud.perro_id)
             .filter(Perro.fundacion_id == fundacion.id)
        )

    elif rol == "admin":
        pass
    else:
        return jsonify({"msg": "Rol no permitido", "rol": rol}), 403

    solicitudes = q.order_by(Solicitud.id.desc()).all()
    return jsonify([s.to_dict() for s in solicitudes]), 200


from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backpatas.models.solicitud import Solicitud
from backpatas.models.respuesta_formulario import RespuestaFormulario


@solicitud_bp.get("/precarga-formulario")
@jwt_required()
def precargar_formulario():
    """
    Obtener último formulario del usuario autenticado
    ---
    tags:
      - Solicitudes
    security:
      - BearerAuth: []
    responses:
      200:
        description: Último formulario encontrado
      404:
        description: No existen formularios previos
    """

    user_id = int(get_jwt_identity())

    # Última solicitud del usuario (la más reciente por ID)
    ultima_solicitud = (
        Solicitud.query
        .filter_by(usuario_id=user_id)
        .order_by(Solicitud.id.desc())
        .first()
    )

    if not ultima_solicitud:
        return jsonify({"msg": "No existen formularios previos"}), 404

    formulario = RespuestaFormulario.query.filter_by(
        solicitud_id=ultima_solicitud.id
    ).first()

    if not formulario:
        return jsonify({"msg": "Formulario no encontrado"}), 404

    return jsonify(formulario.to_dict()), 200

from flask import jsonify
from flask_jwt_extended import jwt_required

from backpatas.models.solicitud import Solicitud
from backpatas.models.respuesta_formulario import RespuestaFormulario

from flask import jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from

from backpatas.models.solicitud import Solicitud
from backpatas.models.respuesta_formulario import RespuestaFormulario

@solicitud_bp.route("/<int:solicitud_id>/formulario", methods=["GET"])
@jwt_required()
@swag_from({
    "tags": ["Solicitudes"],
    "summary": "Obtener formulario completo de una solicitud",
    "description": "Retorna el detalle de una solicitud junto con todas las respuestas del formulario de adopción asociadas.",
    "parameters": [
        {
            "name": "solicitud_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID de la solicitud"
        }
    ],
    "responses": {
        200: {
            "description": "Formulario obtenido correctamente",
            "examples": {
                "application/json": {
                    "solicitud": {
                        "id": 13,
                        "usuario_nombre": "cristian",
                        "perro_nombre": "Luna",
                        "estado_id": 1,
                        "estado_nombre": "Creada",
                        "resultado_knn": 3,
                        "fecha_creacion": "2026-04-07T03:31:05.856917+00:00"
                    },
                    "formulario": {
                        "nombre_completo": "Cristian Pérez",
                        "edad": 28,
                        "tipo_vivienda": "Casa",
                        "permite_mascotas": True,
                        "motivo_adopcion": "Quiero darle un hogar"
                    }
                }
            }
        },
        404: {
            "description": "Solicitud o formulario no encontrado",
            "examples": {
                "application/json": {
                    "message": "Solicitud no encontrada"
                }
            }
        },
        401: {
            "description": "No autorizado"
        }
    }
})
def obtener_formulario_solicitud(solicitud_id):
    solicitud = Solicitud.query.get(solicitud_id)

    if not solicitud:
        return jsonify({"message": "Solicitud no encontrada"}), 404

    respuesta = RespuestaFormulario.query.filter_by(solicitud_id=solicitud_id).first()

    if not respuesta:
        return jsonify({"message": "No se encontraron respuestas para esta solicitud"}), 404

    return jsonify({
        "solicitud": solicitud.to_dict(),
        "formulario": respuesta.to_dict()
    }), 200


from flask import request

from flask import request, current_app
import smtplib

from flask import current_app
import smtplib

@solicitud_bp.post("/test-emailstm")
def test_email2():
    """
    Diagnóstico SMTP
    ---
    tags:
      - Debug
    responses:
      200:
        description: Correo enviado correctamente
      500:
        description: Error SMTP
    """

    try:
        email = "erika222.cftr@gmail.com"

        server_host = current_app.config.get("MAIL_SERVER")
        server_port = current_app.config.get("MAIL_PORT")
        username = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")

        pasos = []

        pasos.append("Configuración cargada")

        smtp = smtplib.SMTP(
            server_host,
            server_port,
            timeout=10
        )

        pasos.append("Conexión SMTP creada")

        smtp.starttls()
        pasos.append("TLS iniciado")

        smtp.login(username, password)
        pasos.append("Login exitoso")

        smtp.sendmail(
            username,
            email,
            f"""Subject: Prueba SMTP AdoptaPatas

Este es un correo de prueba enviado desde AdoptaPatas.

Servidor: {server_host}
Usuario SMTP: {username}
"""
        )

        pasos.append("Correo enviado")

        smtp.quit()

        return {
            "ok": True,
            "destinatario": email,
            "pasos": pasos
        }, 200

    except Exception as e:
        return {
            "ok": False,
            "tipo_error": type(e).__name__,
            "detalle": str(e),
            "mail_server": current_app.config.get("MAIL_SERVER"),
            "mail_port": current_app.config.get("MAIL_PORT"),
            "mail_username": current_app.config.get("MAIL_USERNAME"),
        }, 500