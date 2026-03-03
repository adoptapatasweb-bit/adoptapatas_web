from datetime import datetime
from backpatas.extensions import db

class Adopcion(db.Model):
    __tablename__ = "adopciones"

    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitudes.id"), nullable=False, unique=True)

    perro_id = db.Column(db.Integer, db.ForeignKey("perros.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fundacion_id = db.Column(db.Integer, db.ForeignKey("fundaciones.id"), nullable=False)

    fecha_adopcion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observaciones = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "solicitud_id": self.solicitud_id,
            "perro_id": self.perro_id,
            "usuario_id": self.usuario_id,
            "fundacion_id": self.fundacion_id,
            "fecha_adopcion": self.fecha_adopcion.isoformat(),
            "observaciones": self.observaciones
        }