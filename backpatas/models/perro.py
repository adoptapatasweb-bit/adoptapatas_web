from backpatas.extensions import db

class Perro(db.Model):
    __tablename__ = "perros"

    id = db.Column(db.Integer, primary_key=True)
    foto_url = db.Column(db.String(255), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    tamano = db.Column(db.String(20), nullable=True)
    nivel_actividad = db.Column(db.Integer, nullable=False)
    edad = db.Column(db.Integer, nullable=True)
    esterilizado = db.Column(db.Boolean, nullable=False)
    ruido = db.Column(db.Integer, nullable=True)
    necesita_espacio = db.Column(db.Boolean, nullable=False)
    fundacion_id = db.Column(db.Integer, nullable=False)
    estado_id = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "foto_url": self.foto_url,
            "nombre": self.nombre,
            "tamano": self.tamano,
            "nivel_actividad": self.nivel_actividad,
            "edad": self.edad,
            "esterilizado": self.esterilizado,
            "ruido": self.ruido,
            "necesita_espacio": self.necesita_espacio,
            "fundacion_id": self.fundacion_id,
            "estado_id": self.estado_id
        }
