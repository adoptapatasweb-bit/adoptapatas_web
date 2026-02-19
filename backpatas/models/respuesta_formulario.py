from backpatas.extensions import db

class RespuestaFormulario(db.Model):
    __tablename__ = "respuestas_formulario"

    # En tu tabla NO hay "id", el PK debe ser solicitud_id (1:1)
    solicitud_id = db.Column(db.Integer, primary_key=True, autoincrement=False)


    # Datos personales
    nombre_completo = db.Column(db.String(150), nullable=True)
    numero_identificacion = db.Column(db.String(50), nullable=True)
    edad = db.Column(db.Integer, nullable=True)
    celular = db.Column(db.String(20), nullable=True)
    telefono_fijo = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    barrio = db.Column(db.String(100), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    estado_civil = db.Column(db.String(50), nullable=True)

    # Laboral/económico
    profesion = db.Column(db.String(150), nullable=True)
    actividad_economica = db.Column(db.String(150), nullable=True)
    empresa = db.Column(db.String(150), nullable=True)
    cargo = db.Column(db.String(100), nullable=True)
    horario_laboral = db.Column(db.String(100), nullable=True)
    responsable_economico_mascota = db.Column(db.String(100), nullable=True)
    otro_responsable = db.Column(db.String(100), nullable=True)

    # Hogar
    convivientes = db.Column(db.String(150), nullable=True)
    numero_personas_hogar = db.Column(db.Integer, nullable=True)
    edades_hogar = db.Column(db.String(100), nullable=True)
    alergias_en_hogar = db.Column(db.Boolean, nullable=True)
    acuerdo_familiar_adopcion = db.Column(db.Boolean, nullable=True)

    # Vivienda
    tipo_vivienda = db.Column(db.String(50), nullable=True)
    tenencia_vivienda = db.Column(db.String(50), nullable=True)
    permite_mascotas = db.Column(db.Boolean, nullable=True)
    espacio_suficiente = db.Column(db.Boolean, nullable=True)
    tiene_jardin = db.Column(db.Boolean, nullable=True)
    vivienda_segura = db.Column(db.Boolean, nullable=True)
    lugar_mascota = db.Column(db.String(100), nullable=True)
    instalara_mallas = db.Column(db.Boolean, nullable=True)
    frecuencia_mudanza = db.Column(db.String(50), nullable=True)

    # Experiencia con mascotas
    experiencia_mascotas = db.Column(db.Boolean, nullable=True)
    mascotas_actuales = db.Column(db.Boolean, nullable=True)
    detalle_mascotas_actuales = db.Column(db.Text, nullable=True)
    ubicacion_mascotas_actuales = db.Column(db.String(100), nullable=True)
    mascotas_previas = db.Column(db.Boolean, nullable=True)
    causa_fallecimiento_mascotas = db.Column(db.Text, nullable=True)

    # Rutina / cuidados
    frecuencia_en_casa = db.Column(db.String(50), nullable=True)
    horas_solo = db.Column(db.Integer, nullable=True)
    responsable_cuidados = db.Column(db.String(100), nullable=True)
    plan_ausencias_largas = db.Column(db.String(150), nullable=True)
    compromiso_veterinario = db.Column(db.Boolean, nullable=True)
    consciente_gastos = db.Column(db.Boolean, nullable=True)
    accion_problemas_salud = db.Column(db.Text, nullable=True)
    accion_danos_objetos = db.Column(db.Text, nullable=True)

    # Motivaciones
    motivo_adopcion = db.Column(db.Text, nullable=True)
    motivo_devolucion = db.Column(db.Text, nullable=True)

    # Viajes / vacaciones
    planes_viaje = db.Column(db.Boolean, nullable=True)
    destino_viaje = db.Column(db.String(150), nullable=True)
    plan_mascota_viaje = db.Column(db.String(150), nullable=True)
    plan_vacaciones = db.Column(db.String(150), nullable=True)

    # Esterilización / seguridad
    conoce_esterilizacion = db.Column(db.Boolean, nullable=True)
    opinion_esterilizacion = db.Column(db.Text, nullable=True)
    salida_sola_calle = db.Column(db.Boolean, nullable=True)
    uso_identificacion = db.Column(db.Boolean, nullable=True)

    # Integración / verificación
    plan_nuevo_integrante = db.Column(db.Text, nullable=True)
    acepta_visita_domiciliaria = db.Column(db.Boolean, nullable=True)
    fotos_mascotas = db.Column(db.Text, nullable=True)
    video_vivienda = db.Column(db.Text, nullable=True)
    referencias_personales = db.Column(db.Text, nullable=True)

    # Campos para KNN (importantes para tu IA)
    nivel_actividad_usuario = db.Column(db.Integer, nullable=True)
    tamano_preferido = db.Column(db.String(20), nullable=True)
    tolerancia_ruido = db.Column(db.Integer, nullable=True)
    anios_experiencia_mascotas = db.Column(db.Integer, nullable=True)
    objetivo_adopcion = db.Column(db.String(100), nullable=True)
    dio_mascota_adopcion = db.Column(db.Boolean, nullable=True)
    motivo_adopcion_previa = db.Column(db.Text, nullable=True)
    presupuesto_mensual = db.Column(db.Numeric(10, 2), nullable=True)
    tipo_entorno = db.Column(db.String(50), nullable=True)
    dinamica_hogar = db.Column(db.String(50), nullable=True)
    anios_compromiso = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        # Para no listar 70 campos acá, al frontend normalmente le basta "ok"
        # Si lo quieres completo, lo hacemos luego con un serializer.
        return {"solicitud_id": self.solicitud_id}
