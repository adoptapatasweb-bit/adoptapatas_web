from backpatas.extensions import db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.Integer, nullable=True)

    def set_password(self, plain_password: str):
        self.password = pwd_context.hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    def to_dict(self):
        return {
            "id": self.id,
            "identificacion": self.identificacion,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "estado": self.estado
        }
