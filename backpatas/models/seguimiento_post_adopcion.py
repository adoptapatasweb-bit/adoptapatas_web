from datetime import datetime
from backpatas.extensions import db


class SeguimientoPostAdopcion(db.Model):
    __tablename__ = "seguimiento_post_adopcion"

    id = db.Column(db.Integer, primary_key=True)

    adopcion_id = db.Column(
        db.Integer,
        db.ForeignKey("adopciones.id"),
        nullable=False,
        index=True
    )

    # En SQL Server tienes DEFAULT SYSDATETIME().
    # Esto deja que SQL Server lo ponga, pero también cubre inserts desde Python.
    fecha_seguimiento = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.func.sysdatetime()
    )

    estado_mascota = db.Column(db.String(100), nullable=False)
    medio_seguimiento = db.Column(db.String(100), nullable=False)

    url_evidencia = db.Column(db.String(500), nullable=True)
    observaciones = db.Column(db.String(1000), nullable=True)

    registrado_por_usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    # Relaciones (opcionales pero útiles)
    adopcion = db.relationship(
        "Adopcion",
        backref=db.backref("seguimientos", lazy=True)
    )

    registrado_por = db.relationship("Usuario")

    def to_dict(self):
        return {
            "id": self.id,
            "adopcion_id": self.adopcion_id,
            "fecha_seguimiento": self.fecha_seguimiento.isoformat() if self.fecha_seguimiento else None,
            "estado_mascota": self.estado_mascota,
            "medio_seguimiento": self.medio_seguimiento,
            "url_evidencia": self.url_evidencia,
            "observaciones": self.observaciones,
            "registrado_por_usuario_id": self.registrado_por_usuario_id,
        }

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


