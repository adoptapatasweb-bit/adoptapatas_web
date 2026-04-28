from datetime import datetime
from backpatas.extensions import db

from datetime import datetime
from backpatas.extensions import db


class Adopcion(db.Model):
    __tablename__ = "adopciones"

    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey("solicitudes.id"),
        nullable=False,
        unique=True
    )

    perro_id = db.Column(db.Integer, db.ForeignKey("perros.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fundacion_id = db.Column(db.Integer, db.ForeignKey("fundaciones.id"), nullable=False)

    fecha_adopcion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observaciones = db.Column(db.String(500), nullable=True)

    # Relaciones
    solicitud = db.relationship("Solicitud", backref="adopcion", uselist=False)
    perro = db.relationship("Perro", backref="adopciones")
    usuario = db.relationship("Usuario", backref="adopciones")
    fundacion = db.relationship("Fundacion", backref="adopciones")

    def to_dict(self):
        return {
            "id": self.id,
            "solicitud_id": self.solicitud_id,
            "perro_id": self.perro_id,
            "usuario_id": self.usuario_id,
            "fundacion_id": self.fundacion_id,
            "fecha_adopcion": self.fecha_adopcion.isoformat() if self.fecha_adopcion else None,
            "observaciones": self.observaciones,

            # Datos enriquecidos
            "perro_nombre": self.perro.nombre if self.perro else None,
            "perro_foto_url": self.perro.foto_url if self.perro else None,
            "perro_raza": self.perro.raza if self.perro else None,

            "usuario_nombre": getattr(self.usuario, "nombre", None) if self.usuario else None,
            "usuario_apellido": getattr(self.usuario, "apellido", None) if self.usuario else None,
            "usuario_email": getattr(self.usuario, "email", None) if self.usuario else None,

            "fundacion_nombre": self.fundacion.nombre if self.fundacion else None,
            "fundacion_logo_url": getattr(self.fundacion, "logo_url", None) if self.fundacion else None,
        }