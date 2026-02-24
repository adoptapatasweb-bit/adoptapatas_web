from datetime import datetime
from backpatas.extensions import db

class Banner(db.Model):
    __tablename__ = "banners"

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    imagen_url = db.Column(db.String(255), nullable=True)

    activo = db.Column(db.Boolean, nullable=True)
    orden = db.Column(db.Integer, nullable=True)

    # ✅ IMPORTANTÍSIMO: para que no inserte NULL
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    fundacion_id = db.Column(db.Integer, db.ForeignKey("fundaciones.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "imagen_url": self.imagen_url,
            "activo": self.activo,
            "orden": self.orden,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "fundacion_id": self.fundacion_id,
            "created_by": self.created_by,
        }