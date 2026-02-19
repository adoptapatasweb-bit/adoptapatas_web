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

from datetime import datetime

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

        # Copiar SOLO las keys que existan en el modelo (evita basura)
        columnas_validas = {
            c.name for c in RespuestaFormulario.__table__.columns
            if c.name != "solicitud_id"
        }

        for k, v in formulario.items():
            if k in columnas_validas:
                setattr(rf, k, v)

        db.session.add(rf)

        # 3) Commit atómico
        db.session.commit()

        return jsonify({
            "msg": "Solicitud creada con formulario",
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

        q = (
            db.session.query(Solicitud)
            .join(Perro, Perro.id == Solicitud.perro_id)
            .filter(Perro.fundacion_id == fundacion.id)
            .order_by(Solicitud.id.desc())
        )
        solicitudes = q.all()
        return jsonify([s.to_dict() for s in solicitudes]), 200

    return jsonify({"msg": "Rol no permitido", "rol": rol}), 403


# =========================================================
# PATCH /solicitudes/<id>/aprobar
# RF-018
# =========================================================
from datetime import datetime
@solicitud_bp.get("/test-aprobacion-email/<int:solicitud_id>")
def test_aprobacion_email(solicitud_id):

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



@solicitud_bp.patch("/<int:solicitud_id>/aprobar")
@jwt_required()
@roles_required("admin", "fundacion")
def aprobar_solicitud(solicitud_id):
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
    motivo = data.get("motivo")  # opcional
    ahora = datetime.utcnow()

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

        db.session.commit()

        # -------------------------
        # Envío de correos (no afecta la transacción ya confirmada)
        # -------------------------
        # Email al aprobado
        # -------------------------
        # Envío de correos (no afecta la transacción ya confirmada)
        # -------------------------
        try:
            perro = Perro.query.get(solicitud.perro_id)
            nombre_perro = perro.nombre if perro else f"ID {solicitud.perro_id}"

            # ✅ Email al aprobado (solo una vez)
            aprobado_user = Usuario.query.get(solicitud.usuario_id)
            if aprobado_user and aprobado_user.email:
                send_email(
                    to=aprobado_user.email,
                    subject=f"AdoptaPatas: Solicitud aprobada (#{solicitud.id})",
                    body=(
                        f"Hola.\n\n"
                        f"¡Buenas noticias! Tu solicitud #{solicitud.id} para {nombre_perro} fue APROBADA.\n\n"
                        f"Motivo: {solicitud.motivo_decision or 'No especificado'}\n\n"
                        f"Equipo AdoptaPatas\n"
                    )
                )

            # ✅ Email a los rechazados automáticos (con nombre del perro)
            for s in otras_pendientes:
                u = Usuario.query.get(s.usuario_id)
                if u and u.email:
                    send_email(
                        to=u.email,
                        subject=f"AdoptaPatas: Actualización de tu solicitud (#{s.id})",
                        body=(
                            f"Hola.\n\n"
                            f"Tu solicitud #{s.id} para {nombre_perro} fue RECHAZADA automáticamente\n"
                            f"porque el perro fue asignado a otra solicitud aprobada.\n\n"
                            f"Puedes postularte a otro peludito en el catálogo.\n\n"
                            f"Equipo AdoptaPatas\n"
                        )
                    )

        except Exception:
            pass

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
    user_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    solicitud = Solicitud.query.get(solicitud_id)
    if not solicitud:
        return jsonify({"msg": "Solicitud no encontrada"}), 404

    # ✅ Validar pendiente antes de decidir
    if solicitud.estado_id != ESTADO_SOL_PENDIENTE:
        return jsonify({"msg": "Solo solicitudes pendientes pueden rechazarse"}), 409

    # ✅ Si es fundación: validar que el perro pertenece a su fundación
    if rol == "fundacion":
        fundacion = _get_fundacion_from_user(user_id)
        if not fundacion:
            return jsonify({"msg": "Fundación no encontrada para este usuario"}), 403

        perro = Perro.query.get(solicitud.perro_id)
        if not perro or perro.fundacion_id != fundacion.id:
            return jsonify({"msg": "No autorizado: solicitud no pertenece a tu fundación"}), 403

    # ✅ Leer motivo (opcional)
    data = request.get_json() or {}
    motivo = data.get("motivo")

    try:
        # ✅ Set campos de decisión
        solicitud.estado_id = ESTADO_SOL_RECHAZADA
        solicitud.fecha_decision = datetime.utcnow()
        solicitud.decidido_por_usuario_id = user_id
        solicitud.motivo_decision = motivo

        db.session.commit()

        # ✅ Enviar correo al usuario que creó la solicitud
        u = Usuario.query.get(solicitud.usuario_id)
        perro = Perro.query.get(solicitud.perro_id)
        nombre_perro = perro.nombre if perro else f"ID {solicitud.perro_id}"

        if u and u.email:
            send_email(
                to=u.email,
                subject=f"AdoptaPatas: Solicitud rechazada (#{solicitud.id})",
                body=(
                    f"Hola.\n\n"
                    f"Tu solicitud #{solicitud.id} para {nombre_perro} fue RECHAZADA.\n\n"
                    f"Motivo: {motivo or 'No especificado'}\n\n"
                    f"Puedes postularte a otro peludito desde el catálogo.\n\n"
                    f"Equipo AdoptaPatas\n"
                )
            )

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
# Historial = solicitudes finalizadas (aprobadas/rechazadas)
# =========================================================
@solicitud_bp.get("/historial")
@jwt_required()
def historial_solicitudes():
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
