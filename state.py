from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator

class AccionPendiente(BaseModel):
    texto: str = ""

CLAMP_0_100 = {
    "habilidad_tecnica", "habilidad_politica", "habilidad_negocios",
    "energia", "energia_max", "salud_fisica", "salud_mental",
    "reputacion", "opinion_publica", "nivel_corrupcion",
    "estabilidad_pais", "aprobacion_publica", "pareja_afinidad",
    "produccion_industrial", "escandalo_acumulado",
}

PERSONALIDADES_HIJOS = ["Leal", "Rebelde", "Inútil", "Ambicioso"]
IDEOLOGIAS = ["Izquierda", "Centro", "Derecha"]
OBJETIVOS_DINASTICOS = [
    "Llegar a Presidente antes de los 45",
    "Amasar más de $100M",
    "Fundar 5 corporaciones",
    "Sobrevivir 3 generaciones",
    "Completar 3 megaobras",
    "Mantener corrupción bajo 20",
]

DICT_FIELDS = [
    "facciones", "crisis_activa", "hijos_edad", "hijos_educacion",
    "ministros", "relaciones_internacionales", "evento_decision",
    "hijos_personalidad", "mapa_electoral", "licitacion_activa",
    "negociacion_activa", "debate_activo", "crisis_minijuego",
    "corporaciones", "corporaciones_progreso",
]

LIST_FIELDS = [
    "noticias", "memoria", "acciones_pendientes", "hijos",
    "megaobras_activas", "megaobras_completadas", "leyes_aprobadas",
    "rivales", "eventos_historicos_activados", "logros",
    "archivo_noticias", "historial_aprobacion", "historial_inflacion",
    "historial_patrimonio", "objetivos_dinasticos", "objetivos_completados",
    "resumen_ultimo_turno",
]

class Estado(BaseModel):
    generacion_actual: int = 1
    apellido_dinastia: str = ""
    hijo_heredero: Optional[str] = None
    dinero_personal: int = 0
    habilidad_tecnica: int = Field(10, ge=0, le=100)
    habilidad_politica: int = Field(10, ge=0, le=100)
    habilidad_negocios: int = Field(10, ge=0, le=100)
    trabajo_actual: str = "Desempleado"
    ingreso_mensual: int = 0
    corporaciones: Dict[str, int] = Field(default_factory=dict)
    corporaciones_progreso: Dict[str, int] = Field(default_factory=dict)
    origen: str = "Técnico"
    rasgo: str = "Ninguno"
    genero: str = "Masculino"
    edad: float = 24.0
    ideologia: str = "Centro"
    objetivos_dinasticos: List[str] = Field(default_factory=list)
    objetivos_completados: List[str] = Field(default_factory=list)
    energia: int = Field(80, ge=0, le=100)
    energia_max: int = 100
    salud_fisica: int = Field(90, ge=0, le=100)
    salud_mental: int = Field(80, ge=0, le=100)
    hospitalizado: bool = False
    reputacion: int = Field(10, ge=0, le=100)
    opinion_publica: int = Field(50, ge=0, le=100)
    cargo_politico: str = "Ciudadano"
    turnos_en_poder: int = 0
    nivel_corrupcion: int = Field(0, ge=0, le=100)
    escandalo_acumulado: int = Field(0, ge=0, le=100)
    facciones: Dict[str, int] = Field(
        default_factory=lambda: {"Militares": 50, "Sindicatos": 50, "Iglesia": 50, "Empresarios": 50}
    )
    ministros: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "Economia": {"nombre": "Ministro A", "lealtad": 50, "corrupcion": 10},
            "Seguridad": {"nombre": "Ministro B", "lealtad": 50, "corrupcion": 10},
            "Salud": {"nombre": "Ministro C", "lealtad": 50, "corrupcion": 10},
        }
    )
    leyes_aprobadas: List[str] = Field(default_factory=list)
    relaciones_internacionales: Dict[str, int] = Field(
        default_factory=lambda: {"EE.UU.": 50, "China": 50, "Brasil": 50}
    )
    prestamo_fmi: bool = False
    campaña_activa: bool = False
    cargo_objetivo: str = ""
    fondo_campaña: int = 0
    mapa_electoral: Dict[str, int] = Field(default_factory=dict)
    tesoro_nacional: int = 5000000
    inflacion: float = 25.0
    estabilidad_pais: int = Field(50, ge=0, le=100)
    aprobacion_publica: int = Field(50, ge=0, le=100)
    produccion_industrial: int = Field(50, ge=0, le=100)
    megaobras_activas: List[Dict[str, Any]] = Field(default_factory=list)
    megaobras_completadas: List[str] = Field(default_factory=list)
    pareja_nombre: str = "Nadie"
    pareja_genero: str = "Femenino"
    pareja_afinidad: int = Field(50, ge=0, le=100)
    hijos: List[str] = Field(default_factory=list)
    hijos_edad: Dict[str, float] = Field(default_factory=dict)
    hijos_educacion: Dict[str, str] = Field(default_factory=dict)
    hijos_personalidad: Dict[str, str] = Field(default_factory=dict)
    rivales: List[Dict[str, Any]] = Field(default_factory=list)
    crisis_activa: Dict[str, Any] = Field(default_factory=dict)
    eventos_historicos_activados: List[str] = Field(default_factory=list)
    logros: List[str] = Field(default_factory=list)
    titular_periodico: str = "Nace una nueva figura política en el país."
    noticias: List[str] = Field(default_factory=list)
    archivo_noticias: List[Dict[str, Any]] = Field(default_factory=list)
    evento_decision: Dict[str, Any] = Field(default_factory=dict)
    acciones_sugeridas: List[str] = Field(default_factory=list)
    acciones_pendientes: List[AccionPendiente] = Field(default_factory=list)
    turno: int = 0
    mes_actual: int = 0
    memoria: List[str] = Field(default_factory=list)
    resumen_ultimo_turno: List[str] = Field(default_factory=list)
    historial_aprobacion: List[int] = Field(default_factory=list)
    historial_inflacion: List[float] = Field(default_factory=list)
    historial_patrimonio: List[int] = Field(default_factory=list)
    licitacion_activa: Dict[str, Any] = Field(default_factory=dict)
    negociacion_activa: Dict[str, Any] = Field(default_factory=dict)
    debate_activo: Dict[str, Any] = Field(default_factory=dict)
    crisis_minijuego: Dict[str, Any] = Field(default_factory=dict)
    # NUEVOS CAMPOS
    nivel_calidad_vida: int = 1  # 1=Callejón, 2=Depto chico, 3=Depto grande, 4=Casa, 5=Casa con pileta, 6=Mansión
    nivel_cargo_laboral: int = 0  # 0=Desempleado, 1=Junior, 2=Empleado, 3=Senior, 4=Gerente, 5=Director, 6=CEO
    turnos_desde_ultimo_aumento: int = 999

    @model_validator(mode="before")
    @classmethod
    def clamp_all(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            for k in CLAMP_0_100:
                if k in data and isinstance(data[k], (int, float)):
                    data[k] = max(0, min(100, int(data[k])))
        return data

def parse_estado(raw, base=None):
    base = dict(base or {})
    raw = dict(raw or {})
    merged = {**base, **raw}
    if base:
        protected = [
            "trabajo_actual", "ingreso_mensual", "habilidad_tecnica",
            "habilidad_politica", "habilidad_negocios", "edad", "nivel_corrupcion",
            "turnos_en_poder", "facciones", "titular_periodico", "hijos",
            "megaobras_activas", "megaobras_completadas", "pareja_afinidad",
            "hijos_edad", "hijos_educacion", "energia_max", "genero",
            "pareja_genero", "campaña_activa", "cargo_objetivo", "fondo_campaña",
            "ministros", "leyes_aprobadas", "relaciones_internacionales",
            "prestamo_fmi", "evento_decision", "hijos_personalidad", "rivales",
            "crisis_activa", "eventos_historicos_activados", "logros",
            "archivo_noticias", "historial_aprobacion", "historial_inflacion",
            "historial_patrimonio", "generacion_actual", "apellido_dinastia",
            "hijo_heredero", "ideologia", "objetivos_dinasticos",
            "objetivos_completados", "escandalo_acumulado", "memoria",
            "mes_actual", "resumen_ultimo_turno", "hospitalizado", "mapa_electoral",
            "licitacion_activa", "negociacion_activa", "debate_activo", "crisis_minijuego",
            "corporaciones", "corporaciones_progreso",
            "nivel_calidad_vida", "nivel_cargo_laboral", "turnos_desde_ultimo_aumento",
        ]
        for k in protected:
            if k in base:
                merged[k] = base[k]
    for k in DICT_FIELDS:
        if k in merged and not isinstance(merged[k], dict):
            merged.pop(k)
    for k in LIST_FIELDS:
        if k in merged and not isinstance(merged[k], list):
            merged.pop(k)
    try:
        return Estado(**merged).model_dump()
    except Exception:
        try:
            return Estado(**base).model_dump()
        except Exception:
            return Estado().model_dump()