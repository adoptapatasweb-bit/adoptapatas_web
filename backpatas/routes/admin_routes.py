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

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@jwt_required()
@roles_required("admin")
def dashboard():
    """
    Panel Administrativo - Dashboard General del Sistema
    ---
    tags:
      - Panel administrativo

    security:
      - BearerAuth: []

    description: >
      Este endpoint devuelve un resumen estratégico del sistema para el rol administrador.
      Consolida métricas globales de usuarios, fundaciones, perros, solicitudes y adopciones.
      Además, incluye información dinámica como:
        - Lista de perros actualmente disponibles para adopción.
        - Últimas 5 solicitudes registradas.
        - Últimas 5 adopciones realizadas.
      Está diseñado para alimentar el panel de control (dashboard) del administrador.

    responses:
      200:
        description: Métricas consolidadas del sistema
        schema:
          type: object
          properties:
            usuarios:
              type: object
              properties:
                total:
                  type: integer
                  example: 15
                activos:
                  type: integer
                  example: 14
                inactivos:
                  type: integer
                  example: 1
            fundaciones:
              type: object
              properties:
                total:
                  type: integer
                  example: 4
            perros:
              type: object
              properties:
                total:
                  type: integer
                  example: 20
                disponibles:
                  type: integer
                  example: 12
                no_disponibles:
                  type: integer
                  example: 6
                eliminados:
                  type: integer
                  example: 2
                lista_disponibles:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 8
                      nombre:
                        type: string
                        example: "Luna"
            solicitudes:
              type: object
              properties:
                total:
                  type: integer
                  example: 30
                pendientes:
                  type: integer
                  example: 5
                aprobadas:
                  type: integer
                  example: 20
                rechazadas:
                  type: integer
                  example: 5
                ultimas:
                  type: array
                  items:
                    type: object
            adopciones:
              type: object
              properties:
                total:
                  type: integer
                  example: 18
                ultimas:
                  type: array
                  items:
                    type: object

      401:
        description: Token inválido o ausente

      403:
        description: Acceso restringido a administradores
    """

    # USUARIOS
    usuarios_total = db.session.query(func.count(Usuario.id)).scalar()
    usuarios_activos = db.session.query(func.count(Usuario.id)).filter(Usuario.estado != 0).scalar()
    usuarios_inactivos = usuarios_total - usuarios_activos

    # FUNDACIONES
    fundaciones_total = db.session.query(func.count(Fundacion.id)).scalar()

    # PERROS
    perros_rows = (
        db.session.query(Perro.estado_id, func.count(Perro.id))
        .group_by(Perro.estado_id)
        .all()
    )
    perros_counts = {estado_id: cantidad for estado_id, cantidad in perros_rows}

    perros_disponibles = perros_counts.get(1, 0)
    perros_no_disponibles = perros_counts.get(2, 0)
    perros_eliminados = perros_counts.get(3, 0)
    perros_total = perros_disponibles + perros_no_disponibles + perros_eliminados

    # Lista de perros disponibles (id + nombre)
    perros_disponibles_lista = (
        Perro.query
        .filter(Perro.estado_id == 1)
        .order_by(Perro.id.desc())
        .all()
    )

    perros_disponibles_detalle = [
        {"id": p.id, "nombre": p.nombre}
        for p in perros_disponibles_lista
    ]

    # SOLICITUDES
    solicitudes_rows = (
        db.session.query(Solicitud.estado_id, func.count(Solicitud.id))
        .group_by(Solicitud.estado_id)
        .all()
    )
    solicitudes_counts = {estado_id: cantidad for estado_id, cantidad in solicitudes_rows}

    solicitudes_pendientes = solicitudes_counts.get(1, 0)
    solicitudes_aprobadas = solicitudes_counts.get(2, 0)
    solicitudes_rechazadas = solicitudes_counts.get(3, 0)
    solicitudes_total = (
        solicitudes_pendientes +
        solicitudes_aprobadas +
        solicitudes_rechazadas
    )

    # Últimas 5 solicitudes
    ultimas_solicitudes_query = (
        Solicitud.query
        .order_by(Solicitud.id.desc())
        .limit(5)
        .all()
    )

    ultimas_solicitudes = [
        {
            "id": s.id,
            "usuario_id": s.usuario_id,
            "perro_id": s.perro_id,
            "estado_id": s.estado_id,
            "fecha_creacion": s.fecha_creacion.isoformat() if s.fecha_creacion else None
        }
        for s in ultimas_solicitudes_query
    ]

    # ADOPCIONES
    adopciones_total = db.session.query(func.count(Adopcion.id)).scalar()

    # Últimas 5 adopciones
    ultimas_adopciones_query = (
        Adopcion.query
        .order_by(Adopcion.fecha_adopcion.desc())
        .limit(5)
        .all()
    )

    ultimas_adopciones = []
    for a in ultimas_adopciones_query:
        perro = Perro.query.get(a.perro_id)
        ultimas_adopciones.append({
            "id": a.id,
            "perro": perro.nombre if perro else None,
            "usuario_id": a.usuario_id,
            "fecha_adopcion": a.fecha_adopcion.isoformat() if a.fecha_adopcion else None
        })

    return jsonify({
        "usuarios": {
            "total": usuarios_total,
            "activos": usuarios_activos,
            "inactivos": usuarios_inactivos
        },
        "fundaciones": {
            "total": fundaciones_total
        },
        "perros": {
            "total": perros_total,
            "disponibles": perros_disponibles,
            "no_disponibles": perros_no_disponibles,
            "eliminados": perros_eliminados,
            "lista_disponibles": perros_disponibles_detalle
        },
        "solicitudes": {
            "total": solicitudes_total,
            "pendientes": solicitudes_pendientes,
            "aprobadas": solicitudes_aprobadas,
            "rechazadas": solicitudes_rechazadas,
            "ultimas": ultimas_solicitudes
        },
        "adopciones": {
            "total": adopciones_total,
            "ultimas": ultimas_adopciones
        },
        "alertas": {
            "solicitudes_pendientes": solicitudes_pendientes,
            "hay_solicitudes_pendientes": solicitudes_pendientes > 0
        }

    }), 200