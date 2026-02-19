from backpatas.extensions import db
from datetime import datetime

class Solicitud(db.Model):
    __tablename__ = "solicitudes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    perro_id = db.Column(db.Integer, db.ForeignKey("perros.id"), nullable=False)

    fecha = db.Column(db.DateTime)  # puedes dejarla si ya existe
    resultado_knn = db.Column(db.Integer, nullable=True)
    estado_id = db.Column(db.Integer, nullable=False)

    # NUEVOS CAMPOS
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_decision = db.Column(db.DateTime, nullable=True)
    decidido_por_usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    motivo_decision = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "perro_id": self.perro_id,
            "estado_id": self.estado_id,
            "resultado_knn": self.resultado_knn,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_decision": self.fecha_decision.isoformat() if self.fecha_decision else None,
            "decidido_por_usuario_id": self.decidido_por_usuario_id,
            "motivo_decision": self.motivo_decision
        }
