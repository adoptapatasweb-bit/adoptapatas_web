from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backpatas.extensions import db
from backpatas.models.perro import Perro
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.utils.decorators import roles_required

perro_bp = Blueprint("perro", __name__)

from flask_jwt_extended import get_jwt, get_jwt_identity
from backpatas.models.fundacion import Fundacion
from backpatas.models.usuario import Usuario

from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from backpatas.models.usuario import Usuario
from backpatas.models.fundacion import Fundacion
from backpatas.models.perro import Perro
from backpatas.utils.decorators import roles_required
from flask import request, jsonify

from flask_jwt_extended import jwt_required
from flask import jsonify, request
from backpatas.models.perro import Perro

@perro_bp.patch("/<int:perro_id>/estado")
@jwt_required()
@roles_required("admin", "fundacion")
def cambiar_estado_perro(perro_id):

    data = request.get_json() or {}
    nuevo_estado = data.get("estado_id")

    if not nuevo_estado:
        return jsonify({"msg": "Debe enviar estado_id"}), 400

    perro = Perro.query.get(perro_id)
    if not perro:
        return jsonify({"msg": "Perro no encontrado"}), 404

    rol = get_jwt().get("rol")

    if rol == "fundacion":
        user_id = int(get_jwt_identity())
        u = Usuario.query.get(user_id)

        f = Fundacion.query.filter_by(
            identificacion=u.identificacion
        ).first()

        if not f or perro.fundacion_id != f.id:
            return jsonify({"msg": "No puedes modificar perros de otra fundación"}), 403

    perro.estado_id = nuevo_estado
    db.session.commit()

    return jsonify({
        "msg": "Estado actualizado",
        "perro": perro.to_dict()
    }), 200


@perro_bp.delete("/<int:perro_id>")
@jwt_required()
@roles_required("admin", "fundacion")
def eliminar_perro(perro_id):

    perro = Perro.query.get(perro_id)
    if not perro:
        return jsonify({"msg": "Perro no encontrado"}), 404

    rol = get_jwt().get("rol")

    # Validar que fundación solo elimine sus perros
    if rol == "fundacion":
        user_id = int(get_jwt_identity())
        u = Usuario.query.get(user_id)

        f = Fundacion.query.filter_by(
            identificacion=u.identificacion
        ).first()

        if not f or perro.fundacion_id != f.id:
            return jsonify({"msg": "No puedes eliminar perros de otra fundación"}), 403

    # Estado 3 = eliminado (ajusta si es otro id)
    perro.estado_id = 3

    db.session.commit()

    return jsonify({"msg": "Perro eliminado lógicamente"}), 200


@perro_bp.get("/catalogo")
@jwt_required()
def catalogo_perros():

    query = Perro.query

    # 🔹 Estado (por defecto solo disponibles)
    estado_id = request.args.get("estado_id", default=1, type=int)
    query = query.filter(Perro.estado_id == estado_id)

    # 🔹 Nombre (búsqueda parcial)
    nombre = request.args.get("nombre")
    if nombre:
        query = query.filter(Perro.nombre.ilike(f"%{nombre}%"))

    # 🔹 Sexo
    sexo = request.args.get("sexo")
    if sexo:
        query = query.filter(Perro.sexo == sexo)

    # 🔹 Tamaño
    tamano = request.args.get("tamano")
    if tamano:
        query = query.filter(Perro.tamano == tamano)

    # 🔹 Edad mínima
    edad_min = request.args.get("edad_min", type=int)
    if edad_min is not None:
        query = query.filter(Perro.edad >= edad_min)

    # 🔹 Edad máxima
    edad_max = request.args.get("edad_max", type=int)
    if edad_max is not None:
        query = query.filter(Perro.edad <= edad_max)

    # 🔹 Fundación
    fundacion_id = request.args.get("fundacion_id", type=int)
    if fundacion_id:
        query = query.filter(Perro.fundacion_id == fundacion_id)

    perros = query.all()

    return jsonify([p.to_dict() for p in perros]), 200

@perro_bp.get("/mios")
@jwt_required()
@roles_required("fundacion")
def mis_perros():
    user_id = int(get_jwt_identity())
    u = Usuario.query.get(user_id)
    if not u or not u.identificacion:
        return jsonify({"msg": "Usuario fundación sin identificacion"}), 400

    f = Fundacion.query.filter_by(identificacion=u.identificacion).first()
    if not f:
        return jsonify({"msg": "No existe fundación asociada a este usuario"}), 404

    perros = Perro.query.filter_by(fundacion_id=f.id).all()
    return jsonify([p.to_dict() for p in perros]), 200


@perro_bp.get("/<int:perro_id>")
@jwt_required()
@roles_required("admin", "fundacion")
def detalle_perro(perro_id):
    perro = Perro.query.get(perro_id)
    if not perro:
        return jsonify({"msg": "Perro no encontrado"}), 404

    rol = get_jwt().get("rol")
    if rol == "fundacion":
        user_id = int(get_jwt_identity())
        u = Usuario.query.get(user_id)
        if not u or not u.identificacion:
            return jsonify({"msg": "Usuario fundación sin identificacion"}), 400

        f = Fundacion.query.filter_by(identificacion=u.identificacion).first()
        if not f:
            return jsonify({"msg": "No existe fundación asociada a este usuario"}), 404

        if perro.fundacion_id != f.id:
            return jsonify({"msg": "No tienes acceso a este perro"}), 403

    return jsonify(perro.to_dict()), 200


@perro_bp.put("/<int:perro_id>")
@jwt_required()
@roles_required("admin", "fundacion")
def editar_perro(perro_id):
    data = request.get_json() or {}

    perro = Perro.query.get(perro_id)
    if not perro:
        return jsonify({"msg": "Perro no encontrado"}), 404

    rol = get_jwt().get("rol")

    # Si es fundación: validar que el perro pertenezca a su fundación
    if rol == "fundacion":
        user_id = int(get_jwt_identity())
        u = Usuario.query.get(user_id)

        if not u or not u.identificacion:
            return jsonify({"msg": "Usuario fundación sin identificacion"}), 400

        f = Fundacion.query.filter_by(identificacion=u.identificacion).first()
        if not f:
            return jsonify({"msg": "No existe fundación asociada a este usuario"}), 404

        if perro.fundacion_id != f.id:
            return jsonify({"msg": "No puedes editar perros de otra fundación"}), 403

    # Campos editables (solo actualiza si vienen en el JSON)
    if "foto_url" in data: perro.foto_url = data["foto_url"]
    if "nombre" in data: perro.nombre = data["nombre"]
    if "tamano" in data: perro.tamano = data["tamano"]
    if "nivel_actividad" in data: perro.nivel_actividad = data["nivel_actividad"]
    if "edad" in data: perro.edad = data["edad"]
    if "esterilizado" in data: perro.esterilizado = data["esterilizado"]
    if "ruido" in data: perro.ruido = data["ruido"]
    if "necesita_espacio" in data: perro.necesita_espacio = data["necesita_espacio"]
    if "estado_id" in data: perro.estado_id = data["estado_id"]

    # Solo admin puede cambiar fundacion_id
    if "fundacion_id" in data:
        if rol != "admin":
            return jsonify({"msg": "Solo admin puede cambiar fundacion_id"}), 403
        perro.fundacion_id = data["fundacion_id"]

    db.session.commit()

    return jsonify({"msg": "Perro actualizado", "perro": perro.to_dict()}), 200


from flask import request, jsonify
from flask_jwt_extended import jwt_required
from backpatas.models.perro import Perro
from backpatas.services.knn_service import build_user_vector, knn_rank_perros

@perro_bp.post("/recomendados")
@jwt_required()
def perros_recomendados():
    data = request.get_json() or {}
    form = data.get("formulario") or {}
    top_k = int(data.get("top_k", 5))

    if not isinstance(form, dict):
        return jsonify({"msg": "Debe enviar formulario como objeto JSON"}), 400

    # objeto dummy con atributos para reutilizar build_user_vector()
    class RF:
        pass

    rf = RF()
    rf.tamano_preferido = form.get("tamano_preferido")
    rf.nivel_actividad_usuario = form.get("nivel_actividad_usuario")
    rf.tolerancia_ruido = form.get("tolerancia_ruido")
    rf.espacio_suficiente = form.get("espacio_suficiente")
    rf.tiene_jardin = form.get("tiene_jardin")
    rf.hay_ninos = form.get("hay_ninos")
    rf.tiene_perros_actualmente = form.get("tiene_perros_actualmente")
    rf.tiene_gatos_actualmente = form.get("tiene_gatos_actualmente")
    rf.actividad_hogar = form.get("actividad_hogar")
    rf.tolerancia_muda = form.get("tolerancia_muda")
    rf.disposicion_entrenamiento = form.get("disposicion_entrenamiento")
    rf.horas_solo = form.get("horas_solo")
    rf.anios_experiencia_mascotas = form.get("anios_experiencia_mascotas")

    u_vec = build_user_vector(rf)

    perros_disponibles = Perro.query.filter_by(estado_id=1).all()
    if not perros_disponibles:
        return jsonify({"msg": "No hay perros disponibles"}), 200

    knn = knn_rank_perros(u_vec, perros_disponibles, top_k=top_k, w_size=0.35)
    topk = knn["topk"]

    # map rápido
    by_id = {p.id: p for p in perros_disponibles}

    recomendados = []
    for item in topk:
        p = by_id.get(item["perro_id"])
        if not p:
            continue
        recomendados.append({
            "perro_id": p.id,
            "nombre": p.nombre,
            "tamano": p.tamano,
            "edad": p.edad,
            "foto_url": p.foto_url,
            "score": item["distance"]  # menor = mejor
        })

    return jsonify({
        "top_k": len(recomendados),
        "recomendados": recomendados
    }), 200

@perro_bp.post("/")
@jwt_required()
@roles_required("admin", "fundacion")
def crear_perro():
    data = request.get_json() or {}

    # Campos obligatorios comunes
    nombre = data.get("nombre")
    nivel_actividad = data.get("nivel_actividad")
    esterilizado = data.get("esterilizado")
    necesita_espacio = data.get("necesita_espacio")
    estado_id = data.get("estado_id")

    if not nombre or nivel_actividad is None or esterilizado is None or necesita_espacio is None or not estado_id:
        return jsonify({"msg": "Faltan campos obligatorios"}), 400

    # Detectar rol desde el JWT
    rol = get_jwt().get("rol")

    # Determinar fundacion_id según rol
    fundacion_id = None

    if rol == "admin":
        # Admin puede asignar la fundación manualmente
        fundacion_id = data.get("fundacion_id")
        if not fundacion_id:
            return jsonify({"msg": "Como admin debes enviar fundacion_id"}), 400

    elif rol == "fundacion":
        # Fundación NO envía fundacion_id: se resuelve automático
        user_id = int(get_jwt_identity())
        u = Usuario.query.get(user_id)
        if not u or not u.identificacion:
            return jsonify({"msg": "No se pudo identificar la fundación (usuario sin identificacion)"}), 400

        f = Fundacion.query.filter_by(identificacion=u.identificacion).first()
        if not f:
            return jsonify({"msg": "No existe fundación asociada a este usuario"}), 404

        fundacion_id = f.id

    perro = Perro(
        foto_url=data.get("foto_url"),
        nombre=nombre,
        tamano=data.get("tamano"),
        nivel_actividad=nivel_actividad,
        edad=data.get("edad"),
        esterilizado=esterilizado,
        ruido=data.get("ruido"),
        necesita_espacio=necesita_espacio,
        fundacion_id=fundacion_id,
        estado_id=estado_id
    )

    db.session.add(perro)
    db.session.commit()

    return jsonify({"msg": "Perro registrado", "perro": perro.to_dict()}), 201
