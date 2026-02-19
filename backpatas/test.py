from backpatas.app import app
from backpatas.extensions import db
from backpatas.models.usuario import Usuario

with app.app_context():
    usuarios = Usuario.query.all()
    print("Usuarios encontrados:", len(usuarios))

    for u in usuarios:
        print(u.to_dict())
