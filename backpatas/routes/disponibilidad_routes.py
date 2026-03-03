from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required
from backpatas.models.perro import Perro

disponibilidad_bp = Blueprint(
    "disponibilidad",
    __name__,
    url_prefix="/disponibilidad"
)


@disponibilidad_bp.get("/resumen")
@jwt_required()
@roles_required("admin")
def resumen_disponibilidad():
    """
    Resumen global de disponibilidad de perros
    ---
    tags:
      - Disponibilidad
    security:
      - BearerAuth: []
    responses:
      200:
        description: Conteo global de perros por estado
        schema:
          type: object
          properties:
            total:
              type: integer
              example: 120
            disponibles:
              type: integer
              example: 70
            no_disponibles:
              type: integer
              example: 40
            eliminados:
              type: integer
              example: 10
      401:
        description: Token faltante o inválido
      403:
        description: Acceso denegado (solo admin)
    """

    # Agrupa por estado_id y cuenta
    rows = (
        db.session.query(Perro.estado_id, func.count(Perro.id))
        .group_by(Perro.estado_id)
        .all()
    )

    counts = {estado_id: cantidad for estado_id, cantidad in rows}

    disponibles = counts.get(1, 0)
    no_disponibles = counts.get(2, 0)
    eliminados = counts.get(3, 0)

    total = disponibles + no_disponibles + eliminados

    return jsonify({
        "total": total,
        "disponibles": disponibles,
        "adoptados": no_disponibles,
        "eliminados": eliminados
    }), 200