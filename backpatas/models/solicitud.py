from backpatas.extensions import db
from datetime import datetime

from datetime import datetime, timezone

class Solicitud(db.Model):
    __tablename__ = "solicitudes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    perro_id = db.Column(db.Integer, db.ForeignKey("perros.id"), nullable=False)

    fecha = db.Column(db.DateTime)
    resultado_knn = db.Column(db.Integer, nullable=True)
    estado_id = db.Column(db.Integer, nullable=False)

    fecha_creacion = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    fecha_decision = db.Column(db.DateTime, nullable=True)
    decidido_por_usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    motivo_decision = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        from backpatas.models.usuario import Usuario
        from backpatas.models.perro import Perro
        from backpatas.models.fundacion import Fundacion

        usuario = Usuario.query.get(self.usuario_id) if self.usuario_id else None
        perro = Perro.query.get(self.perro_id) if self.perro_id else None
        fundacion = Fundacion.query.get(perro.fundacion_id) if perro and perro.fundacion_id else None

        estados = {
            1: "Creada",
            2: "Aprobada",
            3: "Rechazada",
        }

        return {
            "id": self.id,

            "usuario_id": self.usuario_id,
            "usuario_nombre": getattr(usuario, "nombre", None),

            "perro_id": self.perro_id,
            "perro_nombre": getattr(perro, "nombre", None),
            "perro_foto_url": getattr(perro, "foto_url", None),
            "perro_edad": getattr(perro, "edad", None),
            "perro_tamano": getattr(perro, "tamano", None),

            "fundacion_id": getattr(perro, "fundacion_id", None) if perro else None,
            "fundacion_nombre": getattr(fundacion, "nombre", None) if fundacion else None,

            "estado_id": self.estado_id,
            "estado_nombre": estados.get(self.estado_id, "No definido"),

            "resultado_knn": self.resultado_knn,

            "fecha": (
                self.fecha.replace(tzinfo=timezone.utc).isoformat()
                if self.fecha else None
            ),
            "fecha_creacion": (
                self.fecha_creacion.replace(tzinfo=timezone.utc).isoformat()
                if self.fecha_creacion else None
            ),
            "fecha_decision": (
                self.fecha_decision.replace(tzinfo=timezone.utc).isoformat()
                if self.fecha_decision else None
            ),

            "decidido_por_usuario_id": self.decidido_por_usuario_id,
            "motivo_decision": self.motivo_decision,
        }