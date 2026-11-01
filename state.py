from typing import Dict, List, Any, Optional
import random
from entidades import Empresa, Hijo, Ministro, Medio, Rival, Ley

# ==============================================================================
# CONSTANTES DEL JUEGO
# ==============================================================================

IDEOLOGIAS = [
    "Conservador", "Liberal", "Socialdemócrata", "Socialista", 
    "Nacionalista", "Populista", "Tecnócrata"
]

OBJETIVOS_DINASTICOS = [
    "Alcanzar la Presidencia antes de los 55 años",
    "Acumular $5 millones en patrimonio familiar",
    "Fundar una empresa y llevarla al Nivel 4",
    "Mantener la Aprobación Pública sobre 60% durante 20 turnos",
    "Sobrevivir a 3 Crisis Nacionales sin perder el cargo",
    "Lograr que tu heredero tenga más de 80 de potencial"
]

NOMBRES_PILA = [
    "Juan", "María", "Carlos", "Ana", "Pedro", "Laura", "Diego", "Sofía",
    "Martín", "Valentina", "Lucas", "Camila", "Santiago", "Isabella",
    "Mateo", "Catalina", "Joaquín", "Mariana", "Benjamín", "Luciana"
]

PROVINCIAS = [
    "Buenos Aires", "Córdoba", "Santa Fe", "Mendoza", "Tucumán",
    "Entre Ríos", "Salta", "Chaco", "Corrientes", "Misiones",
    "San Juan", "Río Negro", "Neuquén", "Formosa", "Chubut"
]

# Modificadores iniciales por Ideología
IDEOLOGIA_MODIFICADORES = {
    "Conservador": {"Iglesia": 15, "Militares": 10, "Sindicatos": -10},
    "Liberal": {"Empresarios": 20, "Sindicatos": -15},
    "Socialdemócrata": {"Sindicatos": 15, "Empresarios": -10},
    "Socialista": {"Sindicatos": 25, "Empresarios": -25, "Militares": -10},
    "Nacionalista": {"Militares": 20, "Empresarios": -5},
    "Populista": {"Sindicatos": 10, "Empresarios": -5, "Iglesia": -5},
    "Tecnócrata": {"Empresarios": 10, "Sindicatos": -5}
}

# Modificadores por Origen (Stats iniciales)
ORIGEN_MODIFICADORES = {
    "Técnico": {"habilidad_tecnica": 20, "habilidad_politica": -10, "trabajo_actual": "Junior Developer", "ingreso_mensual": 150000},
    "Político": {"habilidad_politica": 20, "habilidad_negocios": -10, "reputacion": 10, "trabajo_actual": "Asesor Político", "ingreso_mensual": 120000},
    "Comerciante": {"habilidad_negocios": 20, "habilidad_tecnica": -10, "dinero_personal": 30000, "trabajo_actual": "Emprendedor", "ingreso_mensual": 100000}
}

# Modificadores por Rasgo (Buffs pasivos)
RASGO_MODIFICADORES = {
    "Carismático": {"opinion_publica": 15, "energia_max": 0},
    "Mente Fría": {"salud_mental": 20, "energia_max": 0},
    "Trabajador": {"energia_max": 30, "salud_mental": 0}
}

# Tipos de empresas fundables
TIPOS_EMPRESA = {
    "Consultora": {"costo": 100000, "dividendo_base": 15000, "req_negocios": 30},
    "Tech Startup": {"costo": 250000, "dividendo_base": 35000, "req_negocios": 50},
    "Inmobiliaria": {"costo": 500000, "dividendo_base": 70000, "req_negocios": 70},
    "Banco": {"costo": 1000000, "dividendo_base": 150000, "req_negocios": 85},
}

# ==============================================================================
# GENERACIÓN DE ESTADO INICIAL
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
    """
    Crea el diccionario de estado inicial aplicando los modificadores 
    de Origen, Ideología y Rasgo.
    """
    
    # 1. Estado base (valores por defecto para todos)
    estado = {
        "nombre": nombre,
        "apellido_dinastia": apellido,
        "edad": float(edad),
        "genero": genero,
        "ideologia": ideologia,
        "rasgo": rasgo,
        
        "turno": 0,
        "mes_actual": 0,
        "energia": 100,
        "energia_max": 100,
        "salud_fisica": 100,
        "salud_mental": 100,
        "dinero_personal": 50000,
        "ingreso_mensual": 0,
        "trabajo_actual": "Desempleado",
        
        "nivel_calidad_vida": 1,
        "turnos_desde_ultimo_aumento": 999,
        
        # Habilidades (Base 20)
        "habilidad_tecnica": 20,
        "habilidad_politica": 20,
        "habilidad_negocios": 20,
        
        # Stats sociales
        "reputacion": 50,
        "opinion_publica": 50,
        "aprobacion_publica": 50,
        "nivel_escandalo": 0,
        "nivel_corrupcion": 10,
        
        # Política
        "cargo_politico": "Ciudadano",
        "turnos_en_poder": 0,
        "generacion_actual": 1,
        "mapa_electoral": {p: 50 for p in PROVINCIAS},
        
        # Facciones
        "facciones": {"Militares": 50, "Sindicatos": 50, "Iglesia": 50, "Empresarios": 50},
        
        # Listas y objetos (Usando las nuevas Dataclasses)
        "hijos": [],
        "rivales": [Rival(nombre=f"Opositor {random.choice(NOMBRES_PILA)}", cargo="Diputado", poder=40)],
        "medios": [
            Medio(nombre="El Clarín", postura="Liberal", apoyo=50),
            Medio(nombre="Página 12", postura="Progresista", apoyo=50),
            Medio(nombre="TN", postura="Centrista", apoyo=60)
        ],
        "ministros": {},
        "corporaciones": {}, # Diccionario de objetos Empresa
        
        # Historial para gráficos
        "historial_patrimonio": [],
        "historial_aprobacion": [],
        "historial_inflacion": [],
        
        # UI y narrativa
        "memoria": [],
        "noticias": [],
        "archivo_noticias": [],
        "resumen_ultimo_turno": [],
        "acciones_sugeridas": [],
        "titular_periodico": f"Comienza la era de la Dinastía {apellido}.",
        
        # Flags de estado
        "hospitalizado": False,
        "campaña_activa": False,
        "juicio_politico_activo": False,
        
        # Mini-juegos y eventos
        "evento_decision": {},
        "licitacion_activa": {},
        "crisis_activa": {},
        "crisis_minijuego": {},
        "debate_activo": {},
        
        # Objetivos
        "objetivos_dinasticos": [],
        "objetivos_completados": [],
        "logros": [],
    }

    # 2. Aplicar modificadores de ORIGEN
    if origen in ORIGEN_MODIFICADORES:
        for stat, valor in ORIGEN_MODIFICADORES[origen].items():
            if stat in estado:
                if isinstance(estado[stat], int) or isinstance(estado[stat], float):
                    estado[stat] += valor
                else:
                    estado[stat] = valor # Para strings como trabajo_actual

    # 3. Aplicar modificadores de RASGO
    if rasgo in RASGO_MODIFICADORES:
        for stat, valor in RASGO_MODIFICADORES[rasgo].items():
            if stat in estado:
                estado[stat] += valor
                
    # Asegurar que la energía no supere el máximo (por el rasgo Trabajador)
    estado["energia"] = estado["energia_max"]

    # 4. Aplicar modificadores de IDEOLOGÍA a las facciones
    if ideologia in IDEOLOGIA_MODIFICADORES:
        for faccion, delta in IDEOLOGIA_MODIFICADORES[ideologia].items():
            if faccion in estado["facciones"]:
                estado["facciones"][faccion] = max(0, min(100, estado["facciones"][faccion] + delta))

    return estado

import json
import os
from entidades import Empresa, Hijo, Ministro, Medio, Rival

# ==============================================================================
# FUNCIONES AUXILIARES Y DE NARRATIVA
# ==============================================================================

def agregar_memoria(estado: Dict[str, Any], evento: str, max_memoria: int = 15):
    """Agrega un evento a la memoria a corto plazo, manteniendo el límite."""
    if "memoria" not in estado:
        estado["memoria"] = []
    estado["memoria"].append(evento)
    if len(estado["memoria"]) > max_memoria:
        estado["memoria"].pop(0)

def calcular_legado(estado: Dict[str, Any]) -> tuple[int, str]:
    """Calcula el puntaje final y el rango de la dinastía."""
    puntos = 0
    
    # 1. Patrimonio
    puntos += estado.get("dinero_personal", 0) // 10000
    
    # 2. Rango Político
    rangos_puntos = {
        "Ciudadano": 0, "Diputado": 100, "Gobernador": 300, "Presidente": 1000
    }
    puntos += rangos_puntos.get(estado.get("cargo_politico", "Ciudadano"), 0)
    
    # 3. Generaciones
    puntos += estado.get("generacion_actual", 1) * 500
    
    # 4. Empresas
    corporaciones = estado.get("corporaciones", {})
    for emp in corporaciones.values():
        if isinstance(emp, Empresa):
            puntos += emp.nivel * 200
        elif isinstance(emp, dict): # Por si carga de un JSON viejo
            puntos += emp.get("nivel", 1) * 200

    # 5. Potencial del Heredero
    hijos = estado.get("hijos", [])
    if hijos:
        mejor_hijo = max(hijos, key=lambda h: h.calcular_potencial_heredero() if isinstance(h, Hijo) else 50)
        potencial = mejor_hijo.calcular_potencial_heredero() if isinstance(mejor_hijo, Hijo) else 50
        puntos += potencial * 10

    # Determinar Rango
    if puntos > 5000: rango = "Leyenda Nacional"
    elif puntos > 2000: rango = "Padre de la Patria"
    elif puntos > 1000: rango = "Oligarca Poderoso"
    elif puntos > 500: rango = "Familia Adinerada"
    else: rango = "Historia Olvidada"

    return puntos, rango

def generar_biografia(estado: Dict[str, Any]) -> str:
    """Genera un texto resumen para descargar al final de la partida."""
    nombre = estado.get("nombre", "Desconocido")
    apellido = estado.get("apellido_dinastia", "X")
    cargo = estado.get("cargo_politico", "Ciudadano")
    edad = int(estado.get("edad", 0))
    patrimonio = estado.get("dinero_personal", 0)
    puntos, rango = calcular_legado(estado)
    
    bio = f"""
    ==========================================
    BIOGRAFÍA DE LA DINASTÍA {apellido.upper()}
    ==========================================
    
    Protagonista: {nombre} {apellido}
    Cargo máximo alcanzado: {cargo}
    Años vividos: {edad}
    Patrimonio final: ${patrimonio:,}
    
    RANGO DE LEGADO: {rango} ({puntos} pts)
    Generación alcanzada: {estado.get('generacion_actual', 1)}
    
    ------------------------------------------
    LOGROS Y EVENTOS CLAVE:
    ------------------------------------------
    """
    for evento in estado.get("memoria", []):
        bio += f"- {evento}\n"
        
    bio += "\n=========================================="
    return bio

def continuar_dinastia(estado: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], str]:
    """Prepara el estado para la siguiente generación."""
    hijos = estado.get("hijos", [])
    if not hijos:
        return None, "No tenés herederos para continuar la dinastía. Fin del juego."
    
    # Elegir al mejor heredero
    mejor_hijo = max(hijos, key=lambda h: h.calcular_potencial_heredero())
    
    nuevo_estado = estado.copy()
    nuevo_estado["nombre"] = mejor_hijo.nombre
    nuevo_estado["edad"] = 18.0
    nuevo_estado["generacion_actual"] = estado.get("generacion_actual", 1) + 1
    nuevo_estado["turno"] = 0
    nuevo_estado["cargo_politico"] = "Ciudadano"
    nuevo_estado["energia"] = 100
    nuevo_estado["salud_fisica"] = 100
    nuevo_estado["salud_mental"] = 100
    
    # Bonus por potencial del heredero
    potencial = mejor_hijo.calcular_potencial_heredero()
    if potencial > 80:
        nuevo_estado["reputacion"] += 20
        nuevo_estado["dinero_personal"] += 100000
        mensaje = f"👑 Tu hijo {mejor_hijo.nombre} asume el mando. ¡Es un genio! (+20 Reputación, +$100k)"
    elif potencial > 50:
        mensaje = f"👑 Tu hijo {mejor_hijo.nombre} asume el mando. Es un líder competente."
    else:
        nuevo_estado["reputacion"] -= 10
        mensaje = f"👑 Tu hijo {mejor_hijo.nombre} asume el mando. Lamentablemente, no está a la altura. (-10 Reputación)"
        
    nuevo_estado["hijos"] = []
    nuevo_estado["memoria"] = [f"Comienza la generación {nuevo_estado['generacion_actual']} con {mejor_hijo.nombre}."]
    
    return nuevo_estado, mensaje

# ==============================================================================
# SISTEMA DE GUARDADO Y CARGA (Adaptado a Dataclasses)
# ==============================================================================

class EstadoEncoder(json.JSONEncoder):
    """Convierte Dataclasses a diccionarios para poder guardarlas en JSON."""
    def default(self, obj):
        if hasattr(obj, '__dataclass_fields__'):
            return obj.__dict__
        return super().default(obj)

def guardar_estado(estado: Dict[str, Any], filepath: str = "legacy_save.json"):
    """Guarda el estado actual en un archivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(estado, f, cls=EstadoEncoder, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar: {e}")

def reconstruir_entidades(estado: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte los diccionarios cargados de JSON de vuelta a Dataclasses."""
    # Corporaciones
    corps = estado.get("corporaciones", {})
    for key, val in corps.items():
        if isinstance(val, dict) and "nombre" in val:
            corps[key] = Empresa(**val)
            
    # Hijos
    hijos = estado.get("hijos", [])
    estado["hijos"] = [Hijo(**h) if isinstance(h, dict) else h for h in hijos]
    
    # Rivales
    rivales = estado.get("rivales", [])
    estado["rivales"] = [Rival(**r) if isinstance(r, dict) else r for r in rivales]
    
    # Medios
    medios = estado.get("medios", [])
    estado["medios"] = [Medio(**m) if isinstance(m, dict) else m for m in medios]
    
    # Ministros
    ministros = estado.get("ministros", {})
    for key, val in ministros.items():
        if isinstance(val, dict) and "nombre" in val:
            ministros[key] = Ministro(**val)
            
    return estado

def cargar_estado(filepath: str = "legacy_save.json") -> Optional[Dict[str, Any]]:
    """Carga el estado desde un archivo JSON y reconstruye las entidades."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        return reconstruir_entidades(estado)
    except Exception as e:
        print(f"Error al cargar: {e}")
        return None

# ==============================================================================
# SALÓN DE LA FAMA (Hall of Fame)
# ==============================================================================

HOF_FILE = "hall_of_fame.json"

def leer_hall_of_fame() -> List[Dict[str, Any]]:
    if not os.path.exists(HOF_FILE):
        return []
    try:
        with open(HOF_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def guardar_hall_of_fame(puntos: int, rango: str, estado: Dict[str, Any]):
    hof = leer_hall_of_fame()
    entrada = {
        "apellido": estado.get("apellido_dinastia", "Desconocida"),
        "rango": rango,
        "puntos": puntos,
        "generaciones": estado.get("generacion_actual", 1),
        "cargo": estado.get("cargo_politico", "Ciudadano"),
        "fecha": "2026" # Podrías usar datetime.now().strftime("%Y-%m-%d")
    }
    hof.append(entrada)
    hof.sort(key=lambda x: x["puntos"], reverse=True)
    
    with open(HOF_FILE, 'w', encoding='utf-8') as f:
        json.dump(hof[:10], f, indent=4, ensure_ascii=False) # Guardar top 10