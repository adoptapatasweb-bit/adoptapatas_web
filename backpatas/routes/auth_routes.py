# Importación de Blueprint para agrupar rutas relacionadas con autenticación
# request para recibir datos del cliente (JSON)
# jsonify para devolver respuestas en formato JSON
from flask import Blueprint, request, jsonify
from flask import request, jsonify
from flask_mail import Message
from werkzeug.security import generate_password_hash

from backpatas.extensions import db, mail
from backpatas.models.usuario import Usuario
from backpatas.utils.reset_token import generate_reset_token, verify_reset_token
from flask import current_app

# Funciones de JWT:
# create_access_token -> genera el token
# jwt_required -> protege rutas que requieren autenticación
# get_jwt_identity -> obtiene el ID del usuario desde el token
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# db es la instancia de SQLAlchemy para interactuar con la base de datos
from backpatas.extensions import db

# Modelo Usuario que representa la tabla "usuarios" en la BD
from backpatas.models.usuario import Usuario

# Decorador personalizado para controlar acceso por roles
from backpatas.utils.decorators import roles_required

# current_app permite acceder a la configuración actual de Flask
from flask import current_app

from flask_jwt_extended import get_jwt

from backpatas.models.token_blocklist import TokenBlocklist

from flask_jwt_extended import create_access_token, create_refresh_token



# Se crea el Blueprint llamado "auth"
# Todas las rutas aquí definidas estarán bajo el prefijo /auth
auth_bp = Blueprint("auth", __name__)


# Conjunto de roles válidos definidos en el sistema
# (Actualmente no se usa directamente, pero documenta los roles permitidos)
ROLES_VALIDOS = {"usuario", "admin", "fundacion"}

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backpatas.extensions import db
from backpatas.models.usuario import Usuario


@auth_bp.patch("/me")
@jwt_required()
def actualizar_mi_perfil():
    """
    Actualizar perfil del usuario autenticado
    ---
    tags:
      - administracion - usuario

    security:
      - BearerAuth: []

    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Erika García"
            identificacion:
              type: string
              example: "123456789"
            password:
              type: string
              example: "NuevaClave123"
          additionalProperties: false

    responses:
      200:
        description: Perfil actualizado correctamente
        schema:
          type: object
          properties:
            msg:
              type: string
              example: Perfil actualizado correctamente
            usuario:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                identificacion:
                  type: string
                  example: "123456789"
                nombre:
                  type: string
                  example: "Erika García"
                email:
                  type: string
                  example: "erika@email.com"
                rol:
                  type: string
                  example: usuario
                estado:
                  type: integer
                  example: 1

      400:
        description: Intento de modificar campos no permitidos o validación incorrecta

      404:
        description: Usuario no encontrado
    """

    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)

    if not usuario or usuario.estado == 0:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    data = request.get_json()

    if not data:
        return jsonify({"msg": "No se enviaron datos"}), 400

    # ❌ Bloqueo de campos restringidos
    if "rol" in data or "email" in data:
        return jsonify({"msg": "No se permite modificar rol ni email"}), 400

    # ✅ Campos permitidos
    if "nombre" in data:
        usuario.nombre = data["nombre"]

    if "identificacion" in data:
        usuario.identificacion = data["identificacion"]

    if "password" in data:
        if len(data["password"]) < 6:
            return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400
        usuario.set_password(data["password"])

    db.session.commit()

    return jsonify({
        "msg": "Perfil actualizado correctamente",
        "usuario": usuario.to_dict()
    }), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    """
    Solicitar recuperación de contraseña
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            email:
              type: string
              example: "correo@ejemplo.com"
    responses:
      200:
        description: Respuesta genérica (si existe el correo, se envían instrucciones)
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    generic = {"msg": "Si el correo existe, enviaremos instrucciones."}
    if not email:
        return jsonify(generic), 200

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify(generic), 200

    token = generate_reset_token(user.id, user.password)

    frontend_base = current_app.config.get("FRONTEND_BASE_URL", "http://localhost:5173")
    link = f"{frontend_base}/ResetPassword?token={token}"

    try:
        msg = Message(
            subject="Recuperación de contraseña - Adoptapatas",
            recipients=[user.email],
            body=(
                f"Hola {user.nombre},\n\n"
                f"Para restablecer tu contraseña abre este enlace (expira en 30 minutos):\n{link}\n\n"
                f"Si no solicitaste esto, ignora el correo."
            ),
        )
        mail.send(msg)
    except Exception:
        pass

    return jsonify(generic), 200


@auth_bp.get("/reset-password")
def reset_password_form():
    """
    Validar token de restablecimiento
    ---
    tags:
      - Auth
    parameters:
      - in: query
        name: token
        required: true
        type: string
        description: Token de reseteo enviado por correo
    responses:
      200:
        description: Token válido
      400:
        description: Token faltante, inválido o expirado
    """
    token = request.args.get("token", "").strip()
    if not token:
        return jsonify({"msg": "Token faltante"}), 400

    ttl = current_app.config.get("RESET_TOKEN_TTL_SECONDS", 1800)
    status = verify_reset_token(token, ttl)

    if status == "expired":
        return jsonify({"msg": "Token expirado"}), 400

    if status is None:
        return jsonify({"msg": "Token inválido"}), 400

    return jsonify({
        "msg": "Token válido",
        "valid": True
    }), 200


@auth_bp.post("/reset-password")
def reset_password_submit():
    """
    Restablecer contraseña
    ---
    tags:
      - Auth
    """
    data = request.get_json(silent=True) or {}

    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""
    confirm = data.get("confirm_password") or ""

    if not token:
        return jsonify({"msg": "Token faltante"}), 400

    if len(new_password) < 6:
        return jsonify({"msg": "La contraseña debe tener al menos 6 caracteres"}), 400

    if new_password != confirm:
        return jsonify({"msg": "Las contraseñas no coinciden"}), 400

    ttl = current_app.config.get("RESET_TOKEN_TTL_SECONDS", 1800)
    data = verify_reset_token(token, ttl)

    if data == "expired":
        return jsonify({"msg": "Token expirado"}), 400

    if not data:
        return jsonify({"msg": "Token inválido"}), 400

    user = Usuario.query.get(data["uid"])
    if not user:
        return jsonify({"msg": "Usuario no existe"}), 400

    if user.password != data["pwh"]:
        return jsonify({"msg": "Token ya no es válido. Solicita uno nuevo"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"msg": "Contraseña actualizada correctamente"}), 200
# =========================
# RF-001: Registro público
# =========================
@auth_bp.post("/register")
def register_usuario():
    """
    Registro público de usuario
    ---
    tags:
      - administracion - usuario
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - email
            - password
          properties:
            nombre:
              type: string
              example: "Juan Pérez"
            email:
              type: string
              example: "juan@mail.com"
            password:
              type: string
              example: "Clave123"
            identificacion:
              type: string
              example: "123456789"
            estado:
              type: integer
              example: 1
              description: 1 activo, 0 inactivo
    responses:
      201:
        description: Usuario creado
      400:
        description: Faltan campos obligatorios
      409:
        description: Email ya registrado
    """
    # Obtiene los datos enviados en formato JSON
    data = request.get_json() or {}

    # Extrae campos del JSON
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")
    identificacion = data.get("identificacion")

    # Se fuerza el rol a "usuario"
    # Esto evita que alguien cree un admin desde el registro público
    rol = "usuario"

    # Estado por defecto es 1 (activo)
    estado = data.get("estado", 1)

    # Validación básica de campos obligatorios
    if not nombre or not email or not password:
        return jsonify({"msg": "Faltan campos obligatorios (nombre, email, password)"}), 400

    # Verifica si ya existe un usuario con ese email (evita duplicados)
    existente = Usuario.query.filter_by(email=email).first()
    if existente:
        return jsonify({"msg": "El email ya está registrado"}), 409

    # Se crea la instancia del usuario
    u = Usuario(
        identificacion=identificacion,
        nombre=nombre,
        email=email,
        rol=rol,
        estado=estado
    )

    # Se encripta la contraseña antes de guardarla
    u.set_password(password)

    # Se guarda en la base de datos
    db.session.add(u)
    db.session.commit()

    # Respuesta exitosa
    return jsonify({"msg": "Usuario creado", "usuario": u.to_dict()}), 201


# =========================
# RF-004: Inicio de sesión
# =========================
@auth_bp.post("/login")
def login():
    """
    Iniciar sesión (JWT)
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "juan@mail.com"
            password:
              type: string
              example: "Clave123"
    responses:
      200:
        description: Login exitoso (access_token y refresh_token)
      400:
        description: Email y password obligatorios
      401:
        description: Credenciales inválidas
    """
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    # Validación básica
    if not email or not password:
        return jsonify({"msg": "Email y password son obligatorios"}), 400

    # Busca el usuario por email
    u = Usuario.query.filter_by(email=email).first()

    # Si no existe o la contraseña no coincide → error 401
    if not u or not u.check_password(password):
        return jsonify({"msg": "Credenciales inválidas"}), 401

    # Se genera el token JWT
    # identity = id del usuario
    # additional_claims = información extra (rol)
    access_token = create_access_token(
        identity=str(u.id),
        additional_claims={"rol": u.rol}
    )
    refresh_token = create_refresh_token(identity=str(u.id))

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": u.to_dict()
    }), 200

# =========================
# RF-040: Ruta protegida
# =========================
@auth_bp.get("/me")
@jwt_required()  # Esta ruta requiere token válido
def me():
    """
    Obtener perfil del usuario autenticado
    ---
    tags:
      - administracion - usuario
    security:
      - BearerAuth: []
    responses:
      200:
        description: Datos del usuario autenticado
      401:
        description: Token faltante o inválido
      404:
        description: Usuario no encontrado
    """
    # Obtiene el ID del usuario desde el token
    user_id = get_jwt_identity()

    # Busca el usuario en la base de datos
    u = Usuario.query.get(int(user_id))

    if not u:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    # Devuelve los datos del usuario autenticado
    return jsonify(u.to_dict()), 200


# =========================
# RF-038: Control de roles
# =========================
@auth_bp.get("/admin-test")
@roles_required("admin")  # Solo usuarios con rol "admin"
def admin_test():
    """
    Endpoint de prueba para rol admin
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Acceso permitido solo para admin
      401:
        description: Token faltante o inválido
      403:
        description: Acceso denegado (no es admin)
    """
    return jsonify({"msg": "Acceso permitido solo para admin"}), 200


# =========================
# RF-002: Registro seguro de administradores
# =========================
@auth_bp.post("/register-admin")
def register_admin():
    """
    Registro de administrador (requiere admin_secret)
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre
            - email
            - password
            - admin_secret
          properties:
            nombre:
              type: string
              example: "Admin Uno"
            email:
              type: string
              example: "admin@mail.com"
            password:
              type: string
              example: "Clave123"
            identificacion:
              type: string
              example: "999999"
            estado:
              type: integer
              example: 1
            admin_secret:
              type: string
              example: "MI_SECRETO"
    responses:
      201:
        description: Admin creado
      400:
        description: Faltan campos obligatorios
      403:
        description: Clave admin inválida
      409:
        description: Email ya registrado
      500:
        description: ADMIN_REGISTRATION_SECRET no configurado
    """
    data = request.get_json() or {}

    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")
    identificacion = data.get("identificacion")
    estado = data.get("estado", 1)

    # Se recibe la clave secreta enviada desde el cliente
    secret = data.get("admin_secret")

    # Se obtiene la clave real configurada en el servidor (.env)
    expected = current_app.config.get("ADMIN_REGISTRATION_SECRET")

    # Si no está configurada en el servidor → error interno
    if not expected:
        return jsonify({"msg": "ADMIN_REGISTRATION_SECRET no configurado"}), 500

    # Si la clave no coincide → acceso denegado
    if secret != expected:
        return jsonify({"msg": "Clave admin inválida"}), 403

    # Validación básica
    if not nombre or not email or not password:
        return jsonify({"msg": "Faltan campos obligatorios"}), 400

    # Verifica duplicado por email
    existente = Usuario.query.filter_by(email=email).first()
    if existente:
        return jsonify({"msg": "El email ya está registrado"}), 409

    # Se crea el usuario con rol fijo "admin"
    u = Usuario(
        identificacion=identificacion,
        nombre=nombre,
        email=email,
        rol="admin",
        estado=estado
    )

    # Se encripta la contraseña
    u.set_password(password)

    # Se guarda en la BD
    db.session.add(u)
    db.session.commit()

    return jsonify({"msg": "Admin creado", "usuario": u.to_dict()}), 201

@auth_bp.post("/logout")
@jwt_required()
def logout():
    """
    Cerrar sesión (revocar token actual)
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Sesión cerrada. Token revocado.
      401:
        description: Token faltante o inválido
    """
    jwt_payload = get_jwt()
    jti = jwt_payload.get("jti")

    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()

    return jsonify({"msg": "Sesión cerrada. Token revocado."}), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """
    Refrescar access token (requiere refresh token)
    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Nuevo access_token generado
      401:
        description: Refresh token faltante o inválido
      404:
        description: Usuario no encontrado
    """
    # Obtiene el ID del usuario desde el refresh token
    user_id = get_jwt_identity()

    # Busca el usuario en la BD
    u = Usuario.query.get(int(user_id))
    if not u:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    # Genera un nuevo access token
    new_access_token = create_access_token(
        identity=str(u.id),
        additional_claims={"rol": u.rol}
    )

    return jsonify({"access_token": new_access_token}), 200

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from backpatas.extensions import db
from backpatas.utils.decorators import roles_required
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.perro import Perro
from backpatas.models.solicitud import Solicitud

# Si ya creaste adopciones:
from backpatas.models.adopcion import Adopcion  # si existe

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@jwt_required()
@roles_required("admin")
def admin_dashboard():
    """
    Panel administrativo (resumen)
    ---
    tags:
      - Panel administrativo
    security:
      - BearerAuth: []
    responses:
      200:
        description: Resumen de métricas para el panel admin
    """

    # Usuarios
    usuarios_total = db.session.query(func.count(Usuario.id)).scalar()
    usuarios_activos = db.session.query(func.count(Usuario.id)).filter(Usuario.estado != 0).scalar()
    usuarios_inactivos = usuarios_total - usuarios_activos

    # Fundaciones
    fundaciones_total = db.session.query(func.count(Fundacion.id)).scalar()

    # Perros por estado_id (1 disp, 2 no disp, 3 eliminados)
    perros_rows = (
        db.session.query(Perro.estado_id, func.count(Perro.id))
        .group_by(Perro.estado_id)
        .all()
    )
    perros_counts = {eid: n for eid, n in perros_rows}

    perros_disponibles = perros_counts.get(1, 0)
    perros_no_disponibles = perros_counts.get(2, 0)
    perros_eliminados = perros_counts.get(3, 0)
    perros_total = perros_disponibles + perros_no_disponibles + perros_eliminados

    # Solicitudes por estado (1 pendiente, 2 aprobada, 3 rechazada)
    sol_rows = (
        db.session.query(Solicitud.estado_id, func.count(Solicitud.id))
        .group_by(Solicitud.estado_id)
        .all()
    )
    sol_counts = {eid: n for eid, n in sol_rows}

    solicitudes_pendientes = sol_counts.get(1, 0)
    solicitudes_aprobadas = sol_counts.get(2, 0)
    solicitudes_rechazadas = sol_counts.get(3, 0)
    solicitudes_total = solicitudes_pendientes + solicitudes_aprobadas + solicitudes_rechazadas

    # Adopciones (si aplica)
    try:
        adopciones_total = db.session.query(func.count(Adopcion.id)).scalar()
    except Exception:
        adopciones_total = None  # si aún no existe el modelo/tabla

    return jsonify({
        "usuarios": {
            "total": usuarios_total,
            "activos": usuarios_activos,
            "inactivos": usuarios_inactivos
        },
        "fundaciones": {
            "total": fundaciones_total
        },
        "perros": {
            "total": perros_total,
            "disponibles": perros_disponibles,
            "no_disponibles": perros_no_disponibles,
            "eliminados": perros_eliminados
        },
        "solicitudes": {
            "total": solicitudes_total,
            "pendientes": solicitudes_pendientes,
            "aprobadas": solicitudes_aprobadas,
            "rechazadas": solicitudes_rechazadas
        },
        "adopciones": {
            "total": adopciones_total
        }
    }), 200