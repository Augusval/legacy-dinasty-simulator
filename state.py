import random
import json
import os
import logging
from typing import Dict, Any, List, Optional
from entidades import Empresa, Hijo, Ministro, Medio, Rival

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTES Y DATOS BASE
# ==============================================================================

NOMBRES_PILA = [
    "Agustín", "Benjamín", "Camilo", "Diego", "Emilio", "Federico",
    "Gabriel", "Hernán", "Ignacio", "Joaquín", "Lucas", "Martín",
    "Nicolás", "Oliver", "Pedro", "Rafael", "Santiago", "Tomás",
    "Valentina", "Camila", "Sofía", "Isabella", "Catalina", "Lucía",
    "Valeria", "Mariana", "Florencia", "Julieta", "Antonella", "Delfina"
]

APELLIDOS_ARGENTINOS = [
    "González", "Rodríguez", "Gómez", "Fernández", "López", "Martínez",
    "Sánchez", "Pérez", "García", "Torres", "Ramírez", "Flores",
    "Acosta", "Medina", "Aguirre", "Ortiz", "Rojas", "Vargas", "Castro", "Romero"
]

TIPOS_EMPRESA = {
    "Consultora": {"costo": 100000, "req_negocios": 30, "dividendo_base": 15000},
    "Tech Startup": {"costo": 250000, "req_negocios": 50, "dividendo_base": 40000},
    "Inmobiliaria": {"costo": 500000, "req_negocios": 70, "dividendo_base": 80000},
    "Banco": {"costo": 1000000, "req_negocios": 85, "dividendo_base": 200000},
}

CARGOS_POLITICOS = ["Ciudadano", "Diputado", "Gobernador", "Presidente"]

TRABAJOS_DISPONIBLES = {
    "Desempleado": {"req_reputacion": 0, "sueldo_base": 0},
    "Junior Developer": {"req_reputacion": 0, "sueldo_base": 150000},
    "Asesor Político": {"req_reputacion": 40, "sueldo_base": 120000},
    "Emprendedor": {"req_reputacion": 30, "sueldo_base": 100000},
    "Gerente": {"req_reputacion": 60, "sueldo_base": 450000},
    "Director": {"req_reputacion": 80, "sueldo_base": 800000},
    "CEO": {"req_reputacion": 95, "sueldo_base": 1500000},
}

FACCIONES_INICIALES = {
    "Militares": 30,
    "Sindicatos": 30,
    "Empresarios": 40,
    "Iglesia": 35,
}

# ==============================================================================
# INICIALIZACIÓN DE ESTADO (LIMPIO - Sin stats inútiles)
# ==============================================================================

def inicializar_estado(
    nombre: str, 
    apellido: str, 
    edad: float, 
    genero: str, 
    origen: str, 
    ideologia: str, 
    rasgo: str
) -> Dict[str, Any]:
    """Crea un estado inicial limpio, sin stats decorativas."""
    
    # Stats base del personaje
    estado = {
        # Identidad
        "nombre": nombre,
        "apellido_dinastia": apellido,
        "edad": edad,
        "genero": genero,
        "origen": origen,
        "ideologia": ideologia,
        "rasgo": rasgo,
        
        # Stats principales (las que SÍ afectan el juego)
        "reputacion": 50,
        "aprobacion_publica": 50,
        "nivel_escandalo": 0,
        
        # Habilidades
        "habilidad_tecnica": 20,
        "habilidad_politica": 20,
        "habilidad_negocios": 20,
        
        # Economía
        "dinero_personal": 50000,
        "ingreso_mensual": 0,
        "inflacion": 25.0,
        "nivel_calidad_vida": 1,
        
        # Política
        "cargo_politico": "Ciudadano",
        "trabajo_actual": "Junior Developer",
        "turnos_en_poder": 0,
        "facciones": dict(FACCIONES_INICIALES),
        
        # Empresas y Gabinete
        "corporaciones": {},
        "ministros": {},
        "medios": [
            Medio(nombre="Clarín", postura="Conservador", apoyo=20),
            Medio(nombre="Página 12", postura="Progresista", apoyo=-10),
            Medio(nombre="TN", postura="Neutro", apoyo=10),
        ],
        
        # Rivales
        "rivales": [
            Rival(nombre="Opositor Luciana", poder=40, secretos=["Recibe fondos de empresas extranjeras"], cargo="Opositora"),
            Rival(nombre="Senador Roberto", poder=30, secretos=["Tiene vínculos con el narcotráfico"], cargo="Senador"),
        ],
        
        # Sistema de logros y objetivos
        "logros": [],
        "objetivos_dinasticos": [],
        "objetivos_completados": [],
        "bonificaciones_objetivos": [],
        
        # Historial para gráficos
        "historial_patrimonio": [50000],
        "historial_aprobacion": [50],
        
        # Estado del juego
        "turno": 0,
        "generacion_actual": 1,
        "titular_periodico": f"Comienza la era de la Dinastía {apellido}.",
        "hospitalizado": False,
        "juicio_politico_activo": False,
        "juicio_politico_sobrevivido": False,
        "crisis_sobrevividas": 0,
    }
    
    # Aplicar modificadores por Origen
    if origen == "Técnico":
        estado["habilidad_tecnica"] = 40
        estado["habilidad_negocios"] = 10
    elif origen == "Político":
        estado["habilidad_politica"] = 40
        estado["reputacion"] = 60
    elif origen == "Comerciante":
        estado["habilidad_negocios"] = 40
        estado["dinero_personal"] = 100000
    
    # Aplicar modificadores por Rasgo
    if rasgo == "Carismático":
        estado["habilidad_politica"] += 10
        estado["reputacion"] += 10
    elif rasgo == "Mente Fría":
        estado["habilidad_tecnica"] += 10
        estado["habilidad_negocios"] += 10
    elif rasgo == "Trabajador":
        estado["habilidad_tecnica"] += 5
        estado["habilidad_politica"] += 5
        estado["habilidad_negocios"] += 5
    
    return estado

# ==============================================================================
# HALL OF FAME
# ==============================================================================

def leer_hall_of_fame() -> List[Dict[str, Any]]:
    """Lee el archivo de hall of fame."""
    filepath = "hall_of_fame.json"
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_hall_of_fame(puntos: int, rango: str, estado: Dict[str, Any]):
    """Guarda una entrada en el hall of fame."""
    hof = leer_hall_of_fame()
    entrada = {
        "apellido": estado.get("apellido_dinastia", "Desconocido"),
        "cargo": estado.get("cargo_politico", "Ciudadano"),
        "puntos": puntos,
        "rango": rango,
        "generacion": estado.get("generacion_actual", 1),
    }
    hof.append(entrada)
    hof.sort(key=lambda x: x["puntos"], reverse=True)
    hof = hof[:10]  # Mantener solo top 10
    
    with open("hall_of_fame.json", "w", encoding="utf-8") as f:
        json.dump(hof, f, indent=2, ensure_ascii=False)

# ==============================================================================
# LEGADO Y BIOGRAFÍA
# ==============================================================================

def calcular_legado(estado: Dict[str, Any]) -> tuple[int, str]:
    """Calcula los puntos de legado y el rango del jugador."""
    puntos = 0
    puntos += estado.get("dinero_personal", 0) // 10000
    puntos += estado.get("reputacion", 0) * 100
    puntos += estado.get("aprobacion_publica", 0) * 100
    
    cargo = estado.get("cargo_politico", "Ciudadano")
    if cargo == "Presidente":
        puntos += 5000
    elif cargo == "Gobernador":
        puntos += 2000
    elif cargo == "Diputado":
        puntos += 500
    
    puntos += len(estado.get("corporaciones", {})) * 500
    puntos += len(estado.get("logros", [])) * 200
    
    if puntos >= 10000:
        rango = "Leyenda Política"
    elif puntos >= 5000:
        rango = "Gran Estadista"
    elif puntos >= 2000:
        rango = "Líder Respetado"
    elif puntos >= 500:
        rango = "Figura Pública"
    else:
        rango = "Ciudadano Común"
    
    return puntos, rango

def generar_biografia(estado: Dict[str, Any]) -> str:
    """Genera una biografía textual del legado del jugador."""
    nombre = estado.get("nombre", "Desconocido")
    apellido = estado.get("apellido_dinastia", "")
    cargo = estado.get("cargo_politico", "Ciudadano")
    edad = int(estado.get("edad", 24))
    
    bio = f"BIOGRAFÍA DE LA DINASTÍA {apellido.upper()}\n"
    bio += "=" * 50 + "\n\n"
    bio += f"{nombre} {apellido} nació con la visión de construir un legado.\n"
    bio += f"A los {edad} años, alcanzó el cargo de {cargo}.\n\n"
    
    if estado.get("corporaciones"):
        bio += "Empresas fundadas:\n"
        for key, emp in estado["corporaciones"].items():
            nombre_emp = emp.nombre if hasattr(emp, 'nombre') else key
            nivel = emp.nivel if hasattr(emp, 'nivel') else 1
            bio += f"  - {nombre_emp} (Nivel {nivel})\n"
    
    bio += f"\nLogros desbloqueados: {len(estado.get('logros', []))}\n"
    bio += f"Generación: {estado.get('generacion_actual', 1)}\n"
    
    return bio

def continuar_dinastia(estado: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], str]:
    """Prepara el estado para la siguiente generación."""
    if estado.get("edad", 24) >= 85:
        nuevo_estado = inicializar_estado(
            nombre=random.choice(NOMBRES_PILA),
            apellido=estado.get("apellido_dinastia", "Dinastía"),
            edad=24.0,
            genero="Masculino",
            origen="Técnico",
            ideologia=estado.get("ideologia", "Liberal"),
            rasgo="Trabajador"
        )
        nuevo_estado["generacion_actual"] = estado.get("generacion_actual", 1) + 1
        nuevo_estado["dinero_personal"] = estado.get("dinero_personal", 0) // 2  # Hereda la mitad
        
        msg = f"Ha nacido un nuevo heredero de la Dinastía {estado.get('apellido_dinastia', '')}. La generación {nuevo_estado['generacion_actual']} comienza con ${nuevo_estado['dinero_personal']:,}."
        return nuevo_estado, msg
    
    return None, "Aún no es momento de continuar la dinastía."

# ==============================================================================
# GUARDADO Y CARGA DE ESTADO (JSON)
# ==============================================================================

class EstadoEncoder(json.JSONEncoder):
    """Encoder personalizado para convertir Dataclasses a JSON."""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def guardar_estado(estado: Dict[str, Any], filepath: str = "legacy_save.json"):
    """Guarda el estado actual en un archivo JSON."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(estado, f, cls=EstadoEncoder, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error al guardar estado: {e}")

def reconstruir_entidades(estado: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte los diccionarios JSON de vuelta a instancias de Dataclasses al cargar."""
    # Empresas
    corporaciones = estado.get("corporaciones", {})
    for key, emp_data in corporaciones.items():
        if isinstance(emp_data, dict):
            corporaciones[key] = Empresa(**emp_data)
    
    # Ministros
    ministros = estado.get("ministros", {})
    for key, min_data in ministros.items():
        if isinstance(min_data, dict):
            ministros[key] = Ministro(**min_data)
            
    # Medios
    medios = estado.get("medios", [])
    estado["medios"] = [Medio(**m) if isinstance(m, dict) else m for m in medios]
    
    # Rivales
    rivales = estado.get("rivales", [])
    estado["rivales"] = [Rival(**r) if isinstance(r, dict) else r for r in rivales]
    
    return estado

def cargar_estado(filepath: str = "legacy_save.json") -> Optional[Dict[str, Any]]:
    """Carga un estado guardado y reconstruye las entidades."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            estado = json.load(f)
        return reconstruir_entidades(estado)
    except Exception as e:
        logger.error(f"Error al cargar estado: {e}")
        return None