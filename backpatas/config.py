import os

class Config:
    RESET_TOKEN_TTL_SECONDS = 30 * 60  # 30 minutos
    BACKEND_BASE_URL = "http://localhost:5000"  # cámbialo en producción

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME"))

    SECRET_KEY = os.getenv("SECRET_KEY", "clave_super_segura")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mssql+pyodbc://sa:tu_password@localhost/adoptapatas_web?driver=ODBC+Driver+17+for+SQL+Server"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_super_seguro")

    ADMIN_REGISTRATION_SECRET = os.getenv("ADMIN_REGISTRATION_SECRET")

