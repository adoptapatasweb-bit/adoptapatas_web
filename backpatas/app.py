from dotenv import load_dotenv
load_dotenv()


from flask import Flask
from backpatas.config import Config
from backpatas.extensions import db, migrate, jwt, cors

from backpatas.extensions import mail



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from backpatas.models.token_blocklist import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    cors.init_app(app)

    @app.get("/")
    def home():
        return {"mensaje": "API funcionando correctamente"}

    # Importa modelos para migraciones
    from backpatas.models import usuario, perro, solicitud  # noqa: F401

    # Registrar blueprints (solo los que existan y NO estén vacíos)
    from backpatas.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from backpatas.routes.perro_routes import perro_bp
    app.register_blueprint(perro_bp, url_prefix="/perros")

    from backpatas.routes.fundacion_routes import fundacion_bp
    app.register_blueprint(fundacion_bp, url_prefix="/fundaciones")

    from backpatas.routes.solicitud_routes import solicitud_bp
    app.register_blueprint(solicitud_bp, url_prefix="/solicitudes")

    from backpatas.routes.banner_routes import banner_bp
    app.register_blueprint(banner_bp)


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
