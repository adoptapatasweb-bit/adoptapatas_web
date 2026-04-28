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
    hay_ninos = db.Column(db.Boolean, nullable=True)
    tiene_perros_actualmente = db.Column(db.Boolean, nullable=True)
    tiene_gatos_actualmente = db.Column(db.Boolean, nullable=True)
    actividad_hogar = db.Column(db.Integer, nullable=True)
    tolerancia_muda = db.Column(db.Integer, nullable=True)
    disposicion_entrenamiento = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            "solicitud_id": self.solicitud_id,

            "nombre_completo": self.nombre_completo,
            "numero_identificacion": self.numero_identificacion,
            "edad": self.edad,
            "celular": self.celular,
            "telefono_fijo": self.telefono_fijo,
            "email": self.email,
            "direccion": self.direccion,
            "barrio": self.barrio,
            "ciudad": self.ciudad,
            "estado_civil": self.estado_civil,

            "profesion": self.profesion,
            "actividad_economica": self.actividad_economica,
            "empresa": self.empresa,
            "cargo": self.cargo,
            "horario_laboral": self.horario_laboral,
            "responsable_economico_mascota": self.responsable_economico_mascota,
            "otro_responsable": self.otro_responsable,

            "convivientes": self.convivientes,
            "numero_personas_hogar": self.numero_personas_hogar,
            "edades_hogar": self.edades_hogar,
            "alergias_en_hogar": self.alergias_en_hogar,
            "acuerdo_familiar_adopcion": self.acuerdo_familiar_adopcion,

            "tipo_vivienda": self.tipo_vivienda,
            "tenencia_vivienda": self.tenencia_vivienda,
            "permite_mascotas": self.permite_mascotas,
            "espacio_suficiente": self.espacio_suficiente,
            "tiene_jardin": self.tiene_jardin,
            "vivienda_segura": self.vivienda_segura,
            "lugar_mascota": self.lugar_mascota,
            "instalara_mallas": self.instalara_mallas,
            "frecuencia_mudanza": self.frecuencia_mudanza,

            "experiencia_mascotas": self.experiencia_mascotas,
            "mascotas_actuales": self.mascotas_actuales,
            "detalle_mascotas_actuales": self.detalle_mascotas_actuales,
            "ubicacion_mascotas_actuales": self.ubicacion_mascotas_actuales,
            "mascotas_previas": self.mascotas_previas,
            "causa_fallecimiento_mascotas": self.causa_fallecimiento_mascotas,

            "frecuencia_en_casa": self.frecuencia_en_casa,
            "horas_solo": self.horas_solo,
            "responsable_cuidados": self.responsable_cuidados,
            "plan_ausencias_largas": self.plan_ausencias_largas,
            "compromiso_veterinario": self.compromiso_veterinario,
            "consciente_gastos": self.consciente_gastos,
            "accion_problemas_salud": self.accion_problemas_salud,
            "accion_danos_objetos": self.accion_danos_objetos,

            "motivo_adopcion": self.motivo_adopcion,
            "motivo_devolucion": self.motivo_devolucion,

            "planes_viaje": self.planes_viaje,
            "destino_viaje": self.destino_viaje,
            "plan_mascota_viaje": self.plan_mascota_viaje,
            "plan_vacaciones": self.plan_vacaciones,

            "conoce_esterilizacion": self.conoce_esterilizacion,
            "opinion_esterilizacion": self.opinion_esterilizacion,
            "salida_sola_calle": self.salida_sola_calle,
            "uso_identificacion": self.uso_identificacion,

            "plan_nuevo_integrante": self.plan_nuevo_integrante,
            "acepta_visita_domiciliaria": self.acepta_visita_domiciliaria,
            "fotos_mascotas": self.fotos_mascotas,
            "video_vivienda": self.video_vivienda,
            "referencias_personales": self.referencias_personales,

            "nivel_actividad_usuario": self.nivel_actividad_usuario,
            "tamano_preferido": self.tamano_preferido,
            "tolerancia_ruido": self.tolerancia_ruido,
            "anios_experiencia_mascotas": self.anios_experiencia_mascotas,
            "objetivo_adopcion": self.objetivo_adopcion,
            "dio_mascota_adopcion": self.dio_mascota_adopcion,
            "motivo_adopcion_previa": self.motivo_adopcion_previa,
            "presupuesto_mensual": float(self.presupuesto_mensual) if self.presupuesto_mensual is not None else None,
            "tipo_entorno": self.tipo_entorno,
            "dinamica_hogar": self.dinamica_hogar,
            "anios_compromiso": self.anios_compromiso,
            "hay_ninos": self.hay_ninos,
            "tiene_perros_actualmente": self.tiene_perros_actualmente,
            "tiene_gatos_actualmente": self.tiene_gatos_actualmente,
            "actividad_hogar": self.actividad_hogar,
            "tolerancia_muda": self.tolerancia_muda,
            "disposicion_entrenamiento": self.disposicion_entrenamiento,
        }