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

    sexo = db.Column(db.String(10), nullable=False)
    descripcion = db.Column(db.String(1000), nullable=True)
    raza = db.Column(db.String(100), nullable=True)
    peso = db.Column(db.Numeric, nullable=True)
    vacunado = db.Column(db.Boolean, nullable=False)
    fecha_ingreso = db.Column(db.DateTime, nullable=False)
    apto_ninos = db.Column(db.Boolean, nullable=True)
    apto_perros = db.Column(db.Boolean, nullable=True)
    apto_gatos = db.Column(db.Boolean, nullable=True)
    necesidad_ejercicio = db.Column(db.Integer, nullable=True)
    nivel_muda = db.Column(db.Integer, nullable=True)
    necesidad_entrenamiento = db.Column(db.Integer, nullable=True)

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
            "estado_id": self.estado_id,
            "sexo": self.sexo,
            "descripcion": self.descripcion,
            "raza": self.raza,
            "peso": float(self.peso) if self.peso is not None else None,
            "vacunado": self.vacunado,
            "fecha_ingreso": self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            "apto_ninos": self.apto_ninos,
            "apto_perros": self.apto_perros,
            "apto_gatos": self.apto_gatos,
            "necesidad_ejercicio": self.necesidad_ejercicio,
            "nivel_muda": self.nivel_muda,
            "necesidad_entrenamiento": self.necesidad_entrenamiento
        }