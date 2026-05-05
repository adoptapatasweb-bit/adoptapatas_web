from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flasgger import Swagger

from backpatas.config import Config
from backpatas.extensions import db, migrate, jwt, cors, mail

import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    print("DATABASE_URL RAW =", repr(os.getenv("DATABASE_URL")))
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
            "title": "AdoptaPatas - API REST",
            "version": "4.0.0",
            "description": (
                "Especificación técnica formal de la API REST del sistema AdoptaPatas. "
                "Esta documentación describe los servicios expuestos por el backend "
                "implementado en Flask, incluyendo autenticación basada en JSON Web Tokens (JWT), "
                "control de acceso por roles (usuario, fundación y administrador), "
                "gestión de entidades del dominio (usuarios, fundaciones, perros, solicitudes de adopción "
                "y contenido dinámico), así como la integración de un motor de recomendación "
                "inteligente basado en el algoritmo K-Nearest Neighbors (KNN). "
                "La presente especificación define el contrato API, estructuras de datos, "
                "parámetros, códigos de estado HTTP y mecanismos de seguridad, garantizando "
                "interoperabilidad con el frontend, trazabilidad de requisitos funcionales "
                "y soporte para mantenimiento, escalabilidad y evolución del sistema."
            ),
            "contact": {
                "name": "Proyecto de Grado - Ingeniería de Sistemas y computacion",
                "email": "Cftriana@ucundinamarca.edu.co",
                "url": "https://www.ucundinamarca.edu.co/"
            },
            "license": {
                "name": "Uso Academico para Tesis",
            }
        },



        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": (
                    "Mecanismo de autenticación basado en JSON Web Tokens (JWT). "
                    "Para acceder a los endpoints protegidos, el cliente debe incluir "
                    "en el encabezado HTTP 'Authorization' un token válido utilizando "
                    "el formato: Bearer <access_token>. "
                    "Este mecanismo permite autenticación stateless y control de "
                    "autorización basado en roles definidos en el sistema."
                )
            }
        },

        "security": [
            {
                "BearerAuth": []
            }
        ]
    }



    Swagger(app, config=swagger_config, template=swagger_template)
    # ---------------------------------------

    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    from backpatas.models.token_blocklist import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @app.get("/")
    def home():
        return {
        "aplicacion": "AdoptaPatas Web ",
        "descripcion": "Plataforma para la gestión y adopción responsable de mascotas",
        "estado": "en linea",
        "mensaje": "Servicio funcionando correctamente",
        "version": "7.0.0",
        "creador": "Cristian Triana",
        "documentacion": "/docs"
    }

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

    from backpatas.routes.disponibilidad_routes import disponibilidad_bp
    app.register_blueprint(disponibilidad_bp)

    from backpatas.routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    from backpatas.routes.user_routes import user_bp
    app.register_blueprint(user_bp)  # si tu user_bp ya tiene url_prefix="/users"

    from backpatas.routes.reportes_routes import reportes_bp
    app.register_blueprint(reportes_bp)

    from backpatas.routes.seguimientos import seguimientos_bp
    app.register_blueprint(seguimientos_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)