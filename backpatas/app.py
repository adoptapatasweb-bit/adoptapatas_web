from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flasgger import Swagger

from backpatas.config import Config
from backpatas.extensions import db, migrate, jwt, cors, mail


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---------- Swagger (Flasgger) ----------
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "adoptapatas_spec",
                "route": "/api-adoptapatas.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "AdoptaPatas API",
            "version": "4.0.0",
            "description": "Especificación técnica basada en OpenAPI (Swagger) de la API REST del sistema AdoptaPatas. Esta documentación describe formalmente los servicios expuestos por el backend, incluyendo mecanismos de autenticación y autorización mediante JWT, control de acceso por roles (usuario, fundación y administrador), gestión integral de entidades del dominio (usuarios, fundaciones, perros, solicitudes de adopción y contenido), así como la integración de un motor de recomendación basado en K-Nearest Neighbors (KNN). La presente especificación define el contrato API, los esquemas de datos, parámetros, estructuras de respuesta y códigos de estado HTTP, garantizando interoperabilidad con el frontend, trazabilidad funcional de los requisitos y soporte para mantenimiento, escalabilidad y evolución del sistema.",
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Escribe: Bearer {tu_token}",
            }
        },
    }

    Swagger(app, config=swagger_config, template=swagger_template)
    # ---------------------------------------

    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    from backpatas.models.token_blocklist import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @app.get("/")
    def home():
        return {"mensaje": "API funcionando correctamente"}

    # Importa modelos para migraciones
    from backpatas.models import usuario, perro, solicitud  # noqa: F401

    # Blueprints
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

    from backpatas.routes.user_routes import user_bp
    app.register_blueprint(user_bp)  # si tu user_bp ya tiene url_prefix="/users"

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)