from backpatas.extensions import db

class Fundacion(db.Model):
    __tablename__ = "fundaciones"

    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    contacto = db.Column(db.String(150), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "identificacion": self.identificacion,
            "logo_url": self.logo_url,
            "nombre": self.nombre,
            "contacto": self.contacto
        }
