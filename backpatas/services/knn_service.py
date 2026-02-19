# backpatas/services/knn_service.py
import math
from typing import Any, Dict, List, Optional

# =========================
# Normalización / mapeos
# =========================

TAMANO_MAP = {"pequeno": 1, "mediano": 2, "grande": 3}

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def norm_1_3(x: Any) -> float:
    """1..3 -> 0..1"""
    try:
        v = int(x)
    except Exception:
        v = 2
    if v < 1: v = 1
    if v > 3: v = 3
    return (v - 1) / 2.0

def norm_0_12(x: Any) -> float:
    """0..12 -> 0..1"""
    try:
        v = float(x)
    except Exception:
        v = 0.0
    if v < 0: v = 0.0
    if v > 12: v = 12.0
    return v / 12.0

def norm_0_10(x: Any) -> float:
    """0..10 -> 0..1"""
    try:
        v = float(x)
    except Exception:
        v = 0.0
    if v < 0: v = 0.0
    if v > 10: v = 10.0
    return v / 10.0

def bit(x: Any) -> float:
    """bit -> 0.0/1.0"""
    try:
        return 1.0 if int(x) == 1 else 0.0
    except Exception:
        return 0.0

def tamano_code(v: Any) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip().lower()
    return TAMANO_MAP.get(s)

# =========================
# Proxies (features calculadas del perro)
# =========================

def proxy_tolerancia_estar_solo(edad: Any, nivel_actividad_1_3: Any) -> float:
    """
    tolerancia_estar_solo (0..1)
    - baja actividad => mayor tolerancia
    - perros adultos => mayor tolerancia
    """
    try:
        edad_i = int(edad)
    except Exception:
        edad_i = 3

    try:
        act = int(nivel_actividad_1_3)
    except Exception:
        act = 2

    base = {1: 0.80, 2: 0.55, 3: 0.30}.get(act, 0.55)

    if edad_i <= 1:
        base -= 0.15
    elif edad_i >= 5:
        base += 0.10

    return clamp01(base)

def proxy_dificultad_perro(nivel_actividad_1_3: Any, ruido_1_3: Any, necesita_espacio_bit: Any) -> float:
    """
    dificultad_perro (0..1) a partir de señales "exigentes".
    """
    act = norm_1_3(nivel_actividad_1_3)
    r = norm_1_3(ruido_1_3)
    e = bit(necesita_espacio_bit)
    return clamp01(0.45 * act + 0.25 * r + 0.30 * e)

# =========================
# Vectores: Usuario (RespuestaFormulario real)
# =========================

def build_user_vector(rf: Any) -> Dict[str, Any]:
    """
    rf: instancia de RespuestaFormulario (SQLAlchemy) o un objeto con los mismos atributos.
    Usa exactamente tus columnas:
      - nivel_actividad_usuario (int 1..3)
      - tamano_preferido (nvarchar)
      - tolerancia_ruido (int 1..3)
      - horas_solo (int 0..12)
      - anios_experiencia_mascotas (int 0..10)
      - espacio_suficiente, tiene_jardin, hay_ninos, tiene_perros_actualmente, tiene_gatos_actualmente (bit)
      - actividad_hogar, tolerancia_muda, disposicion_entrenamiento (int 1..3)
    """
    u: Dict[str, Any] = {}

    # tamaño (se maneja aparte)
    u["tamano_pref_code"] = tamano_code(getattr(rf, "tamano_preferido", None))

    # ordinales 1..3
    u["nivel_actividad_usuario"] = norm_1_3(getattr(rf, "nivel_actividad_usuario", 2))
    u["tolerancia_ruido"] = norm_1_3(getattr(rf, "tolerancia_ruido", 2))
    u["actividad_hogar"] = norm_1_3(getattr(rf, "actividad_hogar", 2))
    u["tolerancia_muda"] = norm_1_3(getattr(rf, "tolerancia_muda", 2))
    u["disposicion_entrenamiento"] = norm_1_3(getattr(rf, "disposicion_entrenamiento", 2))

    # bits
    u["espacio_suficiente"] = bit(getattr(rf, "espacio_suficiente", 0))
    u["tiene_jardin"] = bit(getattr(rf, "tiene_jardin", 0))
    u["hay_ninos"] = bit(getattr(rf, "hay_ninos", 0))
    u["tiene_perros_actualmente"] = bit(getattr(rf, "tiene_perros_actualmente", 0))
    u["tiene_gatos_actualmente"] = bit(getattr(rf, "tiene_gatos_actualmente", 0))

    # continuas normalizadas
    u["horas_solo"] = norm_0_12(getattr(rf, "horas_solo", 0))
    u["anios_experiencia_mascotas"] = norm_0_10(getattr(rf, "anios_experiencia_mascotas", 0))

    return u

# =========================
# Vectores: Perro (tabla real)
# =========================

def build_dog_vector(perro: Any) -> Dict[str, Any]:
    """
    perro: instancia SQLAlchemy de Perro o un objeto con los mismos atributos.
    Usa tu tabla:
      - tamano (nvarchar)
      - nivel_actividad (int 1..3)
      - edad (int)
      - ruido (int 1..3)
      - necesita_espacio (bit)
      - apto_ninos, apto_perros, apto_gatos (bit)
      - necesidad_ejercicio, nivel_muda, necesidad_entrenamiento (int 1..3)
    """
    p: Dict[str, Any] = {}

    # tamaño aparte
    p["tamano_code"] = tamano_code(getattr(perro, "tamano", None))

    # ordinales 1..3
    p["nivel_actividad"] = norm_1_3(getattr(perro, "nivel_actividad", 2))
    p["ruido"] = norm_1_3(getattr(perro, "ruido", 2))
    p["necesidad_ejercicio"] = norm_1_3(getattr(perro, "necesidad_ejercicio", 2))
    p["nivel_muda"] = norm_1_3(getattr(perro, "nivel_muda", 2))
    p["necesidad_entrenamiento"] = norm_1_3(getattr(perro, "necesidad_entrenamiento", 2))

    # bits
    p["necesita_espacio"] = bit(getattr(perro, "necesita_espacio", 0))
    p["apto_ninos"] = bit(getattr(perro, "apto_ninos", 0))
    p["apto_perros"] = bit(getattr(perro, "apto_perros", 0))
    p["apto_gatos"] = bit(getattr(perro, "apto_gatos", 0))

    # proxies (0..1) usando edad real
    edad = getattr(perro, "edad", 3)
    p["tolerancia_estar_solo"] = proxy_tolerancia_estar_solo(
        edad=edad,
        nivel_actividad_1_3=getattr(perro, "nivel_actividad", 2),
    )
    p["dificultad_perro"] = proxy_dificultad_perro(
        nivel_actividad_1_3=getattr(perro, "nivel_actividad", 2),
        ruido_1_3=getattr(perro, "ruido", 2),
        necesita_espacio_bit=getattr(perro, "necesita_espacio", 0),
    )

    return p

# =========================
# Distancia + ranking
# =========================

def size_penalty(user_size_code: Optional[int], dog_size_code: Optional[int]) -> float:
    """
    Penalización por tamaño (0..1).
    0 = match perfecto, 0.5 = diferencia 1 nivel, 1.0 = diferencia 2 niveles.
    """
    if user_size_code is None or dog_size_code is None:
        return 0.2
    diff = abs(int(user_size_code) - int(dog_size_code))
    if diff == 0:
        return 0.0
    if diff == 1:
        return 0.5
    return 1.0

def euclidean_distance(a: List[float], b: List[float]) -> float:
    s = 0.0
    for x, y in zip(a, b):
        d = x - y
        s += d * d
    return math.sqrt(s)

def build_numeric_arrays(u: Dict[str, Any], p: Dict[str, Any]) -> tuple[List[float], List[float]]:
    """
    Orden fijo de features numéricas (12 dims).
    Nota: para el usuario, el "espacio" se resume como max(espacio_suficiente, tiene_jardin).
    """
    u_space = max(float(u["espacio_suficiente"]), float(u["tiene_jardin"]))

    # 12 dimensiones (tamaño se maneja aparte)
    u_arr = [
        float(u["nivel_actividad_usuario"]),
        float(u["tolerancia_ruido"]),
        float(u_space),
        float(u["hay_ninos"]),
        float(u["tiene_perros_actualmente"]),
        float(u["tiene_gatos_actualmente"]),
        float(u["actividad_hogar"]),
        float(u["tolerancia_muda"]),
        float(u["disposicion_entrenamiento"]),
        float(u["horas_solo"]),
        float(u["anios_experiencia_mascotas"]),
        float(u["anios_experiencia_mascotas"]),  # se compara con dificultad (proxy)
    ]

    p_arr = [
        float(p["nivel_actividad"]),
        float(p["ruido"]),
        float(p["necesita_espacio"]),
        float(p["apto_ninos"]),
        float(p["apto_perros"]),
        float(p["apto_gatos"]),
        float(p["necesidad_ejercicio"]),
        float(p["nivel_muda"]),
        float(p["necesidad_entrenamiento"]),
        float(p["tolerancia_estar_solo"]),
        float(p["dificultad_perro"]),
        float(p["dificultad_perro"]),
    ]

    return u_arr, p_arr

def knn_rank_perros(
    user_vec: Dict[str, Any],
    perros: List[Any],
    top_k: int = 5,
    w_size: float = 0.35,
) -> Dict[str, Any]:
    """
    Retorna:
      - ranking: lista ordenada (mejor -> peor) con distancias
      - topk: primeros K
    Distancia total = (1-w_size)*dist_num + w_size*penalización_tamaño
    """
    results: List[Dict[str, Any]] = []
    u_size = user_vec.get("tamano_pref_code")

    for perro in perros:
        p_vec = build_dog_vector(perro)
        u_arr, p_arr = build_numeric_arrays(user_vec, p_vec)

        d_num = euclidean_distance(u_arr, p_arr)
        d_size = size_penalty(u_size, p_vec.get("tamano_code"))

        d_total = (1.0 - float(w_size)) * float(d_num) + float(w_size) * float(d_size)

        results.append({
            "perro_id": int(getattr(perro, "id")),
            "distance": float(d_total),           # menor = mejor
            "distance_numeric": float(d_num),
            "size_penalty": float(d_size),
        })

    results.sort(key=lambda x: x["distance"])
    return {"ranking": results, "topk": results[: max(1, int(top_k))]}
