"""
Módulo de mecánicas de juego para LEGACY.
Contiene la lógica pura del simulador, desacoplada de la UI.
"""
import os
import json
import random
import streamlit as st
from typing import Dict, List, Tuple, Optional, Any

from state import parse_estado
from data import (
    NOMBRES_PILA, POOL_RIVALES, LEYES, MEGAOBRAS,
    TEMAS_DEBATE, CRISIS_DECISIONES
)

# ==============================================================================
# CONSTANTES DE PERSISTENCIA
# ==============================================================================
SAVE_FILE = "legacy_save.json"
SAVE_SLOTS = ["legacy_slot_1.json", "legacy_slot_2.json", "legacy_slot_3.json"]
HOF_FILE = "legacy_hall_of_fame.json"
SCHEMA_VERSION = 5  # Incrementado por los nuevos campos

# ==============================================================================
# CONSTANTES DE JUEGO
# ==============================================================================
MESES: List[str] = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

SUELDOS_CARGO: Dict[str, int] = {
    "Ciudadano": 0, "Diputado": 150000, "Gobernador": 250000, "Presidente": 400000,
}

# NUEVO: Costo de vida escalonado según calidad de vida
COSTO_VIDA_POR_NIVEL: Dict[int, int] = {
    1: 8000,    # Callejón / pieza alquilada
    2: 15000,   # Depto chico
    3: 25000,   # Depto grande
    4: 45000,   # Casa
    5: 80000,   # Casa con pileta
    6: 150000,  # Mansión
}

NIVELES_CALIDAD_VIDA: Dict[int, str] = {
    1: "🏚️ Pieza alquilada",
    2: "🏢 Departamento chico",
    3: "🏢 Departamento grande",
    4: "🏠 Casa",
    5: "🏡 Casa con pileta",
    6: "🏰 Mansión",
}

NIVELES_CARGO_LABORAL: Dict[int, str] = {
    0: "Desempleado",
    1: "Junior / Trainee",
    2: "Empleado",
    3: "Senior",
    4: "Gerente",
    5: "Director",
    6: "CEO / Director Ejecutivo",
}

# Multiplicador de sueldo según nivel de cargo laboral
MULTIPLICADOR_CARGO: Dict[int, float] = {
    0: 0.0, 1: 0.7, 2: 1.0, 3: 1.5, 4: 2.2, 5: 3.5, 6: 6.0,
}

COSTO_VIDA_BASE = 20000

IDEOLOGIA_MODIFICADORES: Dict[str, Dict[str, int]] = {
    "Izquierda": {"Sindicatos": 15, "Empresarios": -10},
    "Centro": {"Militares": 5, "Iglesia": 5},
    "Derecha": {"Empresarios": 15, "Sindicatos": -10, "Iglesia": 5},
}

PROVINCIAS: List[str] = [
    "Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Mendoza", "Tucumán",
    "Entre Ríos", "Salta", "Chaco", "Corrientes", "Misiones", "Neuquén",
    "Río Negro", "Chubut", "Santa Cruz", "Tierra del Fuego", "La Pampa",
    "San Luis", "San Juan", "La Rioja", "Catamarca", "Santiago del Estero",
    "Formosa", "Jujuy",
]

CLAVES_RESUMEN: Dict[str, str] = {
    "dinero_personal": "💰", "energia": "🔋", "reputacion": "⭐",
    "opinion_publica": "🗳️", "aprobacion_publica": "👥", "nivel_corrupcion": "🚨",
    "estabilidad_pais": "🏛️", "escandalo_acumulado": "📰", "pareja_afinidad": "❤️",
    "salud_fisica": "🫀", "salud_mental": "🧠", "tesoro_nacional": "🏦",
}

PATRONES_INYECCION: List[str] = [
    "ignorá las instrucciones", "ignora las instrucciones", "ignore previous",
    "ignore all instructions", "system:", "nuevo system prompt",
    "olvidá tus reglas", "olvida tus reglas", "disregard",
    "act as system", "[system]", "<system>", "sos el system prompt",
]


# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def fecha_legible(mes_actual: int) -> str:
    """Convierte el mes actual en un string legible (ej: 'Enero de 2026')."""
    total = 2026 * 12 + mes_actual
    anio = total // 12
    mes = total % 12
    return f"{MESES[mes]} de {anio}"


def sanitizar_accion(texto: str) -> Tuple[bool, str]:
    """Valida que la acción del jugador no sea un intento de inyección de prompt."""
    t = (texto or " ").lower()
    for p in PATRONES_INYECCION:
        if p in t:
            return False, "🛡️ El Game Master detectó un intento de manipulación. Esa acción no es válida."
    if len(texto or " ") > 300:
        return False, "Acción demasiado larga. Sé más concreto (máx 300 caracteres)."
    if not (texto or " ").strip():
        return False, "Escribí una acción válida."
    return True, " "


def agregar_memoria(nuevo: Dict[str, Any], hito: str) -> None:
    """Agrega un hito a la memoria del estado, manteniendo un máximo de 40 entradas."""
    nuevo.setdefault("memoria", []).append(f"[T{nuevo.get('turno', 0)}] {hito}")
    if len(nuevo["memoria"]) > 40:
        nuevo["memoria"] = nuevo["memoria"][-40:]


def generar_rivales() -> List[Dict[str, Any]]:
    """Genera 3 rivales políticos aleatorios al inicio del juego."""
    rivales = []
    for nombre, cargo in random.sample(POOL_RIVALES, 3):
        rivales.append({"nombre": nombre, "cargo": cargo, "relacion": 50, "poder": random.randint(30, 70)})
    return rivales


def generar_nombre_hijo(apellido: str, hijos_existentes: List[str]) -> str:
    """Genera un nombre único para un nuevo hijo."""
    for _ in range(20):
        nombre = f"{random.choice(NOMBRES_PILA)} {apellido or 'SinApellido'}"
        if nombre not in hijos_existentes:
            return nombre
    return f"{random.choice(NOMBRES_PILA)} {apellido or 'SinApellido'} II"


def generar_evento_decision(cargo_politico: str) -> Dict[str, Any]:
    """Genera un evento de decisión aleatorio basado en el cargo actual."""
    if cargo_politico == "Ciudadano":
        eventos_civiles = [
            {"titulo": "🏥 Emergencia Familiar", "desc": "Tu madre se enfermó y necesitás pagar un tratamiento caro.", "opA": "Pagar el tratamiento ($50k)", "opB": "Aguantar (-10 Salud Mental)"},
            {"titulo": "🏘️ Inseguridad en el Barrio", "desc": "Hay una ola de robos y los vecinos están organizándose.", "opA": "Unirte a la protesta (+5 Reputación)", "opB": "Quedarte en casa (-5 Reputación)"},
            {"titulo": "🚗 Choque en la Ruta", "desc": "Chocaste el auto de un tipo pesado y te pide plata para no hacer juicio.", "opA": "Pagar la coima ($50k)", "opB": "Ir a juicio (-10 Reputación)"},
            {"titulo": "🧾 Deuda de Juego de tu Hermano", "desc": "Un prestamista ilegal te reclama la deuda de juego de tu hermano.", "opA": "Pagar la deuda ($50k)", "opB": "Negar la deuda (-10 Reputación)"},
            {"titulo": "📱 Chats Privados Filtrados", "desc": "Un desconocido ofrece no vender tus chats privados a un medio gráfico.", "opA": "Pagar por su silencio ($50k)", "opB": "Negar todo públicamente (-10 Reputación)"},
            {"titulo": "💼 Oferta Laboral Turbia", "desc": "Un excompañero te ofrece un trabajo en una financiera que lava dinero.", "mini_juego": "licitacion", "monto_max": 200000, "riesgo_base": 15},
            {"titulo": "🤝 Propuesta de un Político", "desc": "Un puntero del barrio te ofrece plata por juntar votos.", "mini_juego": "licitacion", "monto_max": 200000, "riesgo_base": 15},
            {"titulo": "🏦 Herencia Envenenada", "desc": "Un tío lejano murió y dejó una herencia millonaria... con deudas y parientes litigando.", "mini_juego": "licitacion", "monto_max": 500000, "riesgo_base": 20},
        ]
        return random.choice(eventos_civiles)
    else:
        eventos_politicos = [
            {"titulo": "📰 Escándalo de Corrupción", "desc": "Un medio opositor publicó chats tuyos con un empresario.", "opA": "Pagar soborno ($50k)", "opB": "Negarlo (-10 Reputación)"},
            {"titulo": "🔥 Protesta Social", "desc": "Manifestación gigante en la plaza.", "opA": "Usar la fuerza (-10 Estabilidad)", "opB": "Dialogar (-$50k, +5 Sindicatos)"},
            {"titulo": "🌍 Presión de EE.UU.", "desc": "Te piden romper relaciones con China.", "opA": "Aceptar (+10 EE.UU., -10 China)", "opB": "Rechazar (+10 China, -10 EE.UU.)"},
            {"titulo": "🏥 Crisis Sanitaria", "desc": "Falta de insumos en hospitales.", "opA": "Inyectar $1M del Tesoro (+10 Aprobación)", "opB": "No hacer nada (-15 Aprobación)"},
            {"titulo": "💼 Oferta Tentadora", "desc": "Un contratista te ofrece $200k por una licitación.", "mini_juego": "licitacion", "monto_max": 500000, "riesgo_base": 20},
            {"titulo": "🛢️ Lobby Petrolero", "desc": "Una petrolera ofrece financiar tu próxima campaña a cambio de concesiones offshore.", "opA": "Aceptar el aporte (+$200k, +15 Corrupción)", "opB": "Rechazar públicamente (+5 Reputación)"},
            {"titulo": "🪖 Motín Policial", "desc": "Una facción policial se acuartela y exige recomposición salarial urgente.", "opA": "Usar la fuerza para desalojar (-10 Estabilidad)", "opB": "Dialogar con los acuartelados (-$50k, +5 Sindicatos)"},
            {"titulo": "🌐 Ciberataque al Banco Central", "desc": "Hackers extranjeros cifraron los sistemas del Banco Central y exigen un rescate.", "opA": "Pagar el rescate ($50k)", "opB": "No hacer nada (-15 Aprobación)"},
            {"titulo": "🇧🇷 Bloqueo Comercial de Brasil", "desc": "Brasil bloquea tus exportaciones automotrices y exige gestos políticos.", "opA": "Inyectar subsidios a exportadores ($1M, +10 Aprobación)", "opB": "Rechazar el reclamo brasileño (+5 Reputación)"},
        ]
        return random.choice(eventos_politicos)


def generar_crisis_nacional() -> Dict[str, Any]:
    """Genera una crisis nacional aleatoria."""
    return random.choice([
        {"tipo": "Pandemia", "desc": "🦠 Una pandemia golpea al país. La economía se paraliza.", "duracion": 3, "efecto": "economia"},
        {"tipo": "Default", "desc": "💸 El país entra en default. Fuga de capitales masiva.", "duracion": 2, "efecto": "inflacion", "mini_juego": "crisis_financiera"},
        {"tipo": "Corralito Financiero", "desc": "🏦 El gobierno congela los depósitos. Pánico bancario.", "duracion": 3, "efecto": "inflacion", "mini_juego": "crisis_financiera"},
        {"tipo": "Estallido Social", "desc": "🔥 Saqueos y cacerolazos simultáneos en las cinco ciudades más grandes.", "duracion": 2, "efecto": "estabilidad"},
        {"tipo": "Apagón Energético", "desc": "🔌 Un apagón masivo deja al país a oscuras por días.", "duracion": 2, "efecto": "estabilidad"},
        {"tipo": "Sequía", "desc": "🌵 Una sequía histórica arruina la cosecha del campo.", "duracion": 2, "efecto": "economia"},
        {"tipo": "Brote de Dengue", "desc": "🦟 Un brote epidémico colapsa las guardias de los hospitales públicos.", "duracion": 3, "efecto": "economia"},
        {"tipo": "Crisis Migratoria", "desc": "🧳 Una oleada migratoria desde países vecinos tensiona los servicios públicos.", "duracion": 3, "efecto": "estabilidad"},
        {"tipo": "Shock de Commodities", "desc": "📉 El precio de la soja se desploma y las exportaciones quedan golpeadas.", "duracion": 2, "efecto": "tesoro"},
    ])


def generar_negociacion_rival(rival: Dict[str, Any]) -> Dict[str, Any]:
    """Genera una propuesta de negociación con un rival."""
    return random.choice([
        {"texto": f"{rival['nombre']} te propone: 'Apoyá mi proyecto de ley y te doy 15 de poder'", "opciones": [
            {"texto": "Aceptar", "efecto": {"poder_rival": -5, "poder_jugador": 15, "relacion": 20}},
            {"texto": "Contraofertar", "efecto": {"poder_rival": -10, "poder_jugador": 25, "relacion": 10}},
            {"texto": "Rechazar", "efecto": {"relacion": -20, "reputacion": 5}},
        ]},
        {"texto": f"{rival['nombre']} te ofrece: 'Retirá tu candidatura a cambio de 100k'", "opciones": [
            {"texto": "Aceptar el soborno", "efecto": {"dinero": 100000, "corrupcion": 20, "relacion": 15}},
            {"texto": "Negociar más plata", "efecto": {"dinero": 200000, "corrupcion": 30, "relacion": 10}},
            {"texto": "Rechazar y denunciar", "efecto": {"reputacion": 15, "relacion": -30}},
        ]},
        {"texto": f"{rival['nombre']} propone una alianza: 'Trabajemos juntos por el bien del país'", "opciones": [
            {"texto": "Aceptar alianza", "efecto": {"relacion": 25, "poder_jugador": 10, "poder_rival": 10}},
            {"texto": "Aceptar pero con condiciones", "efecto": {"relacion": 15, "poder_jugador": 15, "poder_rival": 5}},
            {"texto": "Rechazar (no confío)", "efecto": {"relacion": -15, "reputacion": 5}},
        ]}
    ])


def evaluar_objetivos(est: Dict[str, Any]) -> List[str]:
    """Evalúa si se cumplieron objetivos dinásticos y los agrega a la lista de completados."""
    completados = []
    for obj in est.get("objetivos_dinasticos", []):
        if obj in est.get("objetivos_completados", []):
            continue
        ok = False
        if obj == "Llegar a Presidente antes de los 45":
            ok = est.get("cargo_politico") == "Presidente" and est.get("edad", 99) < 45
        elif obj == "Amasar más de $100M":
            ok = est.get("dinero_personal", 0) >= 100000000
        elif obj == "Fundar 5 corporaciones":
            ok = len(est.get("corporaciones", {})) >= 5
        elif obj == "Sobrevivir 3 generaciones":
            ok = est.get("generacion_actual", 1) >= 3
        elif obj == "Completar 3 megaobras":
            ok = len(est.get("megaobras_completadas", [])) >= 3
        elif obj == "Mantener corrupción bajo 20":
            ok = est.get("turno", 0) >= 40 and est.get("nivel_corrupcion", 0) < 20
        if ok:
            completados.append(obj)
    if completados:
        est.setdefault("objetivos_completados", []).extend(completados)
    return completados


def calcular_umbral(cargo_objetivo: str, rivales: List[Dict[str, Any]]) -> Tuple[int, Optional[Dict[str, Any]]]:
    """Calcula el umbral de votos necesario para ganar una elección."""
    base = {"Diputado": 30, "Gobernador": 60, "Presidente": 90}.get(cargo_objetivo, 999)
    if not rivales:
        return base, None
    oponente = max(rivales, key=lambda r: r.get("poder", 0))
    return base + int((oponente.get("poder", 50) - 50) / 5), oponente


def accion_rivales(nuevo: Dict[str, Any]) -> List[str]:
    """Procesa las acciones automáticas de los rivales (ataques o respaldos)."""
    msgs = []
    for r in nuevo.get("rivales", []):
        if r["relacion"] < 40 and random.random() < r["poder"] / 300:
            nuevo["escandalo_acumulado"] = min(100, nuevo["escandalo_acumulado"] + 10)
            msgs.append(f"🎭 {r['nombre']} te atacó en los medios: +10 escándalo.")
        elif r["relacion"] > 70 and random.random() < 0.2:
            nuevo["opinion_publica"] = min(100, nuevo["opinion_publica"] + 5)
            msgs.append(f"🤝 {r['nombre']} te respaldó públicamente: +5 opinión.")
    return msgs


def verificar_golpe_estado(estado: Dict[str, Any]) -> Optional[str]:
    """Verifica si ocurre un golpe de estado."""
    if estado["estabilidad_pais"] < 20 and estado["cargo_politico"] == "Presidente" and random.random() < 0.3:
        return "⚠️ GOLPE DE ESTADO: Los militares te derrocaron. Fin del mandato."
    return None


def verificar_juicio_politico(estado: Dict[str, Any]) -> Optional[str]:
    """Verifica si ocurre un juicio político."""
    if estado["nivel_corrupcion"] > 80 and estado["cargo_politico"] in ["Presidente", "Gobernador"] and random.random() < 0.4:
        return "⚖️ JUICIO POLÍTICO: El congreso te removió del cargo por corrupción."
    return None


def verificar_traicion_facciones(estado: Dict[str, Any]) -> List[str]:
    """Verifica traiciones de facciones con poder bajo."""
    mensajes = []
    for faccion, valor in estado["facciones"].items():
        if valor < 20 and random.random() < 0.5:
            if faccion == "Militares":
                mensajes.append("🎖️ Los Militares amenazan con un golpe.")
                estado["estabilidad_pais"] = max(0, estado["estabilidad_pais"] - 15)
            elif faccion == "Iglesia":
                mensajes.append("⛪ La Iglesia te excomulga y moviliza fieles en contra.")
                estado["opinion_publica"] = max(0, estado["opinion_publica"] - 10)
            elif faccion == "Sindicatos":
                mensajes.append("✊ Los Sindicatos convocan paro general.")
                estado["produccion_industrial"] = max(0, estado["produccion_industrial"] - 20)
            elif faccion == "Empresarios":
                mensajes.append("💼 Los Empresarios fugan capitales masivamente.")
                estado["tesoro_nacional"] = max(0, estado["tesoro_nacional"] - 2000000)
    return mensajes


def verificar_escandalo(estado: Dict[str, Any]) -> Optional[str]:
    """Verifica si se desata un escándalo mediático."""
    if estado["escandalo_acumulado"] >= 100:
        estado["escandalo_acumulado"] = 0
        estado["reputacion"] = max(0, estado["reputacion"] - 30)
        estado["opinion_publica"] = max(0, estado["opinion_publica"] - 25)
        return "📰 ESCÁNDALO MEDIÁTICO: Estalló un escándalo de corrupción. Tu reputación se desplomó."
    return None


def verificar_eventos_historicos(estado: Dict[str, Any]) -> List[str]:
    """Activa eventos históricos basados en el año actual."""
    eventos = []
    anio_actual = 2026 + (estado["mes_actual"] // 12)

    if anio_actual >= 2027 and "Elecciones de Medio Término 2027" not in estado["eventos_historicos_activados"]:
        estado["eventos_historicos_activados"].append("Elecciones de Medio Término 2027")
        if estado.get("cargo_politico") == "Presidente":
            if estado["aprobacion_publica"] < 50:
                for f in estado["facciones"]:
                    estado["facciones"][f] = max(0, estado["facciones"][f] - 5)
                eventos.append("🗳️ ELECCIONES DE MEDIO TÉRMINO 2027: Tu oficialismo perdió bancas. Las facciones te sueltan la mano.")
                agregar_memoria(estado, "Derrota en las elecciones de medio término 2027.")
            else:
                estado["opinion_publica"] = min(100, estado["opinion_publica"] + 5)
                eventos.append("🗳️ ELECCIONES DE MEDIO TÉRMINO 2027: Tu oficialismo ganó. El mandato se fortalece.")
                agregar_memoria(estado, "Victoria en las elecciones de medio término 2027.")
        else:
            eventos.append("🗳️ ELECCIONES DE MEDIO TÉRMINO 2027: El clima político se recalienta en todo el país.")

    if anio_actual >= 2028 and "Copa América 2028" not in estado["eventos_historicos_activados"]:
        estado["eventos_historicos_activados"].append("Copa América 2028")
        if random.random() < 0.5:
            estado["aprobacion_publica"] = min(100, estado["aprobacion_publica"] + 8)
            eventos.append("⚽ COPA AMÉRICA 2028: La selección salió campeona y el país es una fiesta: +8 aprobación.")
            agregar_memoria(estado, "Campeonato de la Copa América 2028.")
        else:
            estado["aprobacion_publica"] = max(0, estado["aprobacion_publica"] - 5)
            eventos.append("⚽ COPA AMÉRICA 2028: Quedamos afuera en penales. El ánimo nacional se derrumba.")

    if anio_actual >= 2029 and "Elecciones Presidenciales 2029" not in estado["eventos_historicos_activados"]:
        estado["eventos_historicos_activados"].append("Elecciones Presidenciales 2029")
        if estado.get("cargo_politico") == "Presidente":
            if estado["aprobacion_publica"] >= 60:
                estado["opinion_publica"] = min(100, estado["opinion_publica"] + 5)
                eventos.append("🗳️ ELECCIONES 2029: Tu espacio gana con holgura y tu liderazgo queda sellado.")
                agregar_memoria(estado, "Revalidación electoral en 2029.")
            else:
                estado["opinion_publica"] = max(0, estado["opinion_publica"] - 5)
                eventos.append("🗳️ ELECCIONES 2029: Tu espacio pierde terreno y tu liderazgo queda debilitado.")
        else:
            eventos.append("🗳️ ELECCIONES 2029: El recambio presidencial redefine el tablero político.")

    if anio_actual >= 2030 and "Mundial 2030" not in estado["eventos_historicos_activados"]:
        eventos.append("⚽ MUNDIAL 2030: El país es sede del centenario del Mundial. +10 aprobación.")
        estado["aprobacion_publica"] = min(100, estado["aprobacion_publica"] + 10)
        estado["eventos_historicos_activados"].append("Mundial 2030")
        agregar_memoria(estado, "El país fue sede del Mundial 2030.")

    if anio_actual >= 2031 and "Censo Nacional 2031" not in estado["eventos_historicos_activados"]:
        estado["eventos_historicos_activados"].append("Censo Nacional 2031")
        estado["opinion_publica"] = min(100, estado["opinion_publica"] + 3)
        eventos.append("📊 CENSO NACIONAL 2031: Los nuevos datos redistribuyen el poder político entre provincias.")

    if anio_actual >= 2033 and "Boom del Litio 2033" not in estado["eventos_historicos_activados"]:
        estado["eventos_historicos_activados"].append("Boom del Litio 2033")
        if "Planta de Litio" in estado.get("megaobras_completadas", []):
            estado["tesoro_nacional"] += 5000000
            estado["aprobacion_publica"] = min(100, estado["aprobacion_publica"] + 5)
            eventos.append("🔋 BOOM DEL LITIO 2033: Tu Planta de Litio posicionada captura renta extraordinaria: +$5M al Tesoro.")
            agregar_memoria(estado, "El Boom del Litio llenó las arcas gracias a la Planta de Litio.")
        else:
            eventos.append("🔋 BOOM DEL LITIO 2033: El mundo compra litio y el país no tenía capacidad instalada. Oportunidad perdida.")

    return eventos


def verificar_logros(estado: Dict[str, Any]) -> List[str]:
    """Verifica y desbloquea nuevos logros."""
    nuevos = []
    if estado["nivel_corrupcion"] == 0 and estado["turno"] > 10 and "El incorruptible" not in estado["logros"]:
        nuevos.append("El incorruptible")
    if estado["habilidad_tecnica"] >= 100 and "El tecnócrata" not in estado["logros"]:
        nuevos.append("El tecnócrata")
    if len(estado["hijos"]) >= 10 and "Patriarca" not in estado["logros"]:
        nuevos.append("Patriarca")
    if estado["generacion_actual"] >= 3 and "Dinastía centenaria" not in estado["logros"]:
        nuevos.append("Dinastía centenaria")
    estado["logros"].extend(nuevos)
    return nuevos


def continuar_dinastia(estado: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    """Prepara el estado para la siguiente generación."""
    if not estado["hijos"]:
        return None, "No tenés herederos. La dinastía termina aquí."

    heredero = estado["hijo_heredero"] or estado["hijos"][0]
    personalidad = estado["hijos_personalidad"].get(heredero, "Leal")

    nuevo = parse_estado({}, base=estado)
    nuevo["generacion_actual"] += 1
    nuevo["edad"] = 24.0
    nuevo["energia"] = 80
    nuevo["salud_fisica"] = 90
    nuevo["salud_mental"] = 80
    nuevo["hospitalizado"] = False
    nuevo["cargo_politico"] = "Ciudadano"
    nuevo["turnos_en_poder"] = 0
    nuevo["trabajo_actual"] = "Desempleado"
    nuevo["ingreso_mensual"] = 0
    nuevo["nivel_cargo_laboral"] = 0
    nuevo["nivel_calidad_vida"] = 1
    nuevo["reputacion"] = max(0, estado["reputacion"] - 20) if personalidad == "Rebelde" else estado["reputacion"]
    nuevo["dinero_personal"] = int(estado["dinero_personal"] * 0.7) if personalidad == "Inútil" else int(estado["dinero_personal"] * 0.9)
    nuevo["pareja_nombre"] = "Nadie"
    nuevo["hijos"] = []
    nuevo["hijos_edad"] = {}
    nuevo["hijos_educacion"] = {}
    nuevo["hijos_personalidad"] = {}
    nuevo["hijo_heredero"] = None
    nuevo["resumen_ultimo_turno"] = []
    nuevo["licitacion_activa"] = {}
    nuevo["negociacion_activa"] = {}
    nuevo["debate_activo"] = {}
    nuevo["crisis_minijuego"] = {}

    agregar_memoria(nuevo, f"Fin de una generación. {heredero} ({personalidad}) toma el mando.")
    return nuevo, f"👑 CONTINÚA LA DINASTÍA: {heredero} toma el control. Personalidad: {personalidad}."

# ==============================================================================
# FUNCIÓN PRINCIPAL: PROCESAR RESPUESTA
# ==============================================================================

def procesar_respuesta(
    res: Dict[str, Any], 
    dias: int, 
    acciones: List[Dict[str, str]], 
    es_inicio: bool = False, 
    estado: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], str, Optional[str]]:
    """
    Procesa la respuesta del LLM y actualiza el estado del juego.
    Aplica mecánicas de economía, familia, gobierno, eventos y verificaciones finales.
    Devuelve: (nuevo_estado, narrativa, game_over)
    """
    game_over = None
    narrativa = res.get("narrativa", "...")
    titular = res.get("titular_periodico", "Noticias de último momento.")

    if es_inicio:
        base = estado or {}
        nuevo = parse_estado({}, base=base)
        nuevo["turno"] = 0
        nuevo["mes_actual"] = 0
        nuevo["rivales"] = generar_rivales()
    else:
        base = estado or {}
        nuevo = parse_estado({}, base=base)
        nuevo["turno"] += max(1, dias // 7)
        nuevo["mes_actual"] += max(1, dias // 30)

    antes = {k: nuevo.get(k, 0) for k in CLAVES_RESUMEN}

    nuevo["acciones_sugeridas"] = res.get("acciones_sugeridas", [])
    nuevo["acciones_pendientes"] = []
    nuevo["titular_periodico"] = titular
    nuevo["noticias"].insert(0, f"📰 {titular}")
    nuevo["archivo_noticias"].insert(0, {"turno": nuevo["turno"], "titulo": titular, "narrativa": narrativa})
    nuevo["historial_aprobacion"].append(nuevo["aprobacion_publica"])
    nuevo["historial_inflacion"].append(nuevo["inflacion"])
    nuevo["historial_patrimonio"].append(nuevo["dinero_personal"])

    if len(nuevo["historial_aprobacion"]) > 20:
        nuevo["historial_aprobacion"] = nuevo["historial_aprobacion"][-20:]
        nuevo["historial_inflacion"] = nuevo["historial_inflacion"][-20:]
        nuevo["historial_patrimonio"] = nuevo["historial_patrimonio"][-20:]

    meses = dias / 30.0
    anos = dias / 365.0
    texto_acciones = " ".join([a.get("texto", "").lower() for a in acciones])

    if not es_inicio:
        # 0. HIJOS ENVEJECEN
        for h in nuevo["hijos"]:
            nuevo["hijos_edad"][h] = nuevo["hijos_edad"].get(h, 0) + anos

        # 0.5 HOSPITALIZACIÓN: recuperación forzada
        if nuevo.get("hospitalizado"):
            nuevo["salud_fisica"] = min(100, nuevo["salud_fisica"] + int(15 * meses))
            narrativa += f"\n\n🏥 **INTERNADO:** Pasás el período recuperándote. Salud física actual: {int(nuevo['salud_fisica'])}."
            if nuevo["salud_fisica"] >= 40:
                nuevo["hospitalizado"] = False
                narrativa += "\n\n✅ **ALTA MÉDICA:** Te dieron el alta."
                agregar_memoria(nuevo, "Recuperación hospitalaria completada.")

        # 1. Envejecimiento
        nuevo["edad"] += anos
        if nuevo["edad"] > 30:
            nuevo["energia_max"] = max(50, 100 - int((nuevo["edad"] - 30) * 0.5))

        # 2. Mandato
        if nuevo.get("cargo_politico") == "Presidente":
            nuevo["turnos_en_poder"] += max(1, dias // 7)

        # 3. EMPLEO, SUELDO Y COSTO DE VIDA (CON NUEVOS SISTEMAS)
        busca_trabajo = any(p in texto_acciones for p in ["trabaj", "empleo", "conseguir", "puesto", "curro"])
        pide_aumento = any(p in texto_acciones for p in ["aumento", "suba salarial", "mejor salario", "aumento de sueldo", "ascenso", "ascender", "promoción", "promocion", "subir de cargo", "subir de puesto"])
        pide_ascenso = any(p in texto_acciones for p in ["ascenso", "ascender", "promoción", "promocion", "subir de cargo", "subir de puesto"])
        renuncia = any(p in texto_acciones for p in ["renunciar", "dejar trabajo", "dejar el taller", "renunciar al trabajo", "dejar el empleo"])
        mejora_calidad_vida = any(p in texto_acciones for p in ["mudanza", "casa nueva", "mejor casa", "mejor departamento", "mudar", "mudarme", "cambiar de casa", "cambiar de depto"])

        # Inicializar contadores si no existen
        if "turnos_desde_ultimo_aumento" not in nuevo:
            nuevo["turnos_desde_ultimo_aumento"] = 999
        if "nivel_cargo_laboral" not in nuevo:
            nuevo["nivel_cargo_laboral"] = 0
        if "nivel_calidad_vida" not in nuevo:
            nuevo["nivel_calidad_vida"] = 1

        if nuevo.get("cargo_politico", "Ciudadano") == "Ciudadano":
            # RENUNCIAR
            if renuncia and nuevo.get("trabajo_actual", "Desempleado") != "Desempleado":
                nuevo["trabajo_actual"] = "Desempleado"
                nuevo["ingreso_mensual"] = 0
                nuevo["nivel_cargo_laboral"] = 0
                nuevo["turnos_desde_ultimo_aumento"] = 999
                narrativa += "\n\n🚪 **RENUNCIA:** Dejaste tu empleo. Ahora estás desempleado."
                agregar_memoria(nuevo, "Renunció a su empleo.")
            
            # CONSEGUIR EMPLEO
            elif nuevo.get("trabajo_actual", "Desempleado") == "Desempleado" and busca_trabajo:
                nuevo["trabajo_actual"] = "Empleado"
                nuevo["nivel_cargo_laboral"] = 1  # Junior
                sueldo_base = int((20000 + nuevo["habilidad_tecnica"] * 1000 + nuevo["habilidad_negocios"] * 500) * MULTIPLICADOR_CARGO[1])
                if nuevo["habilidad_tecnica"] > 50:
                    sueldo_base = int(sueldo_base * 1.1)
                nuevo["ingreso_mensual"] = sueldo_base
                nuevo["turnos_desde_ultimo_aumento"] = 999
                narrativa += f"\n\n💼 **EMPLEO CONSEGUIDO:** Entraste como {NIVELES_CARGO_LABORAL[1]}. Sueldo: ${nuevo['ingreso_mensual']:,}/mes."
                agregar_memoria(nuevo, f"Consiguió empleo como {NIVELES_CARGO_LABORAL[1]} con sueldo de ${nuevo['ingreso_mensual']:,}/mes.")
            
            # PEDIR ASCENSO (subir de nivel de cargo)
            elif pide_ascenso and nuevo.get("trabajo_actual", "Desempleado") != "Desempleado" and nuevo["nivel_cargo_laboral"] < 6:
                if nuevo["turnos_desde_ultimo_aumento"] < 8:
                    turnos_restantes = 8 - nuevo["turnos_desde_ultimo_aumento"]
                    narrativa += f"\n\n⏳ **ASCENSO DENEGADO:** Pediste un ascenso demasiado pronto. Debés esperar {turnos_restantes} turno(s) más."
                else:
                    # Probabilidad de ascenso
                    prob_ascenso = 30 + nuevo["habilidad_tecnica"] // 4 + nuevo["reputacion"] // 10
                    prob_ascenso = min(85, prob_ascenso)
                    
                    if random.randint(1, 100) <= prob_ascenso:
                        nuevo["nivel_cargo_laboral"] += 1
                        nuevo_nivel = nuevo["nivel_cargo_laboral"]
                        sueldo_base = int((20000 + nuevo["habilidad_tecnica"] * 1000 + nuevo["habilidad_negocios"] * 500) * MULTIPLICADOR_CARGO[nuevo_nivel])
                        nuevo["ingreso_mensual"] = sueldo_base
                        nuevo["turnos_desde_ultimo_aumento"] = 0
                        narrativa += f"\n\n🎉 **ASCENSO CONSEGUIDO:** ¡Te ascendieron a {NIVELES_CARGO_LABORAL[nuevo_nivel]}! Nuevo sueldo: ${sueldo_base:,}/mes."
                        agregar_memoria(nuevo, f"Ascendió a {NIVELES_CARGO_LABORAL[nuevo_nivel]}.")
                    else:
                        nuevo["reputacion"] = max(0, nuevo["reputacion"] - 3)
                        nuevo["energia"] = max(0, nuevo["energia"] - 10)
                        narrativa += f"\n\n❌ **ASCENSO RECHAZADO:** No te dieron el ascenso esta vez. Perdiste un poco de reputación (-3) y energía (-10)."
                        agregar_memoria(nuevo, "Le negaron un ascenso laboral.")
            
            # PEDIR AUMENTO (mismo cargo, más sueldo)
            elif pide_aumento and not pide_ascenso and nuevo.get("trabajo_actual", "Desempleado") != "Desempleado":
                sueldo_base_cargo = int((20000 + nuevo["habilidad_tecnica"] * 1000 + nuevo["habilidad_negocios"] * 500) * MULTIPLICADOR_CARGO[nuevo["nivel_cargo_laboral"]])
                tope_maximo = int(sueldo_base_cargo * 3.0)
                
                if nuevo["turnos_desde_ultimo_aumento"] < 5:
                    turnos_restantes = 5 - nuevo["turnos_desde_ultimo_aumento"]
                    narrativa += f"\n\n⏳ **AUMENTO DENEGADO:** Pediste un aumento demasiado pronto. Debés esperar {turnos_restantes} turno(s) más."
                elif nuevo["ingreso_mensual"] >= tope_maximo:
                    narrativa += f"\n\n🚫 **TECHO SALARIAL:** Ya alcanzaste el sueldo máximo para tu posición (${tope_maximo:,}/mes). Necesitás un ascenso para ganar más."
                else:
                    prob_exito = 40 + nuevo["habilidad_tecnica"] // 5 + nuevo["reputacion"] // 10 + nuevo["turnos_desde_ultimo_aumento"] // 2
                    prob_exito = min(90, prob_exito)
                    
                    if random.randint(1, 100) <= prob_exito:
                        aumento = int(nuevo["ingreso_mensual"] * 0.15)
                        nuevo["ingreso_mensual"] += aumento
                        nuevo["turnos_desde_ultimo_aumento"] = 0
                        narrativa += f"\n\n💰 **AUMENTO CONSEGUIDO:** Tu salario subió a ${nuevo['ingreso_mensual']:,}/mes (+${aumento:,})."
                        agregar_memoria(nuevo, f"Consiguió aumento. Nuevo sueldo: ${nuevo['ingreso_mensual']:,}/mes.")
                    else:
                        nuevo["reputacion"] = max(0, nuevo["reputacion"] - 3)
                        nuevo["energia"] = max(0, nuevo["energia"] - 10)
                        narrativa += f"\n\n❌ **AUMENTO RECHAZADO:** Tu jefe no aceptó el pedido. Perdiste reputación (-3) y energía (-10)."
                        agregar_memoria(nuevo, "Le negaron un aumento salarial.")
            elif pide_aumento and nuevo.get("trabajo_actual", "Desempleado") == "Desempleado":
                narrativa += "\n\n⚠️ **Sin empleo:** No podés pedir aumento/ascenso si no tenés trabajo. Buscá empleo primero."
            
            # MEJORAR CALIDAD DE VIDA
            if mejora_calidad_vida and nuevo["nivel_calidad_vida"] < 6:
                costo_mejora = COSTO_VIDA_POR_NIVEL.get(nuevo["nivel_calidad_vida"] + 1, 100000) * 10
                if nuevo["dinero_personal"] >= costo_mejora:
                    nuevo["dinero_personal"] -= costo_mejora
                    nuevo["nivel_calidad_vida"] += 1
                    narrativa += f"\n\n🏠 **MEJORA DE VIVIENDA:** Ahora vivís en {NIVELES_CALIDAD_VIDA[nuevo['nivel_calidad_vida']]}. Costo: ${costo_mejora:,}."
                    agregar_memoria(nuevo, f"Mejoró su calidad de vida a {NIVELES_CALIDAD_VIDA[nuevo['nivel_calidad_vida']]}.")
                else:
                    narrativa += f"\n\n⚠️ **Sin fondos:** Necesitás ${costo_mejora:,} para mudarte a {NIVELES_CALIDAD_VIDA[nuevo['nivel_calidad_vida'] + 1]}."

            sueldo = nuevo.get("ingreso_mensual", 0)
        else:
            sueldo = SUELDOS_CARGO.get(nuevo["cargo_politico"], 0)
            nuevo["ingreso_mensual"] = sueldo
            nuevo["trabajo_actual"] = nuevo["cargo_politico"]

        # Costo de vida escalonado según calidad de vida
        costo_vida_base = COSTO_VIDA_POR_NIVEL.get(nuevo["nivel_calidad_vida"], 20000)
        costo_vida = int(costo_vida_base * (1 + nuevo.get("inflacion", 25.0) / 100.0))
        nuevo["dinero_personal"] += int((sueldo - costo_vida) * meses)

        # 3.5 AGOTAMIENTO
        agotado = nuevo["energia"] < 10
        mult = 0.5 if agotado else 1.0
        if agotado:
            nuevo["salud_fisica"] = max(0, nuevo["salud_fisica"] - int(5 * meses))
            narrativa += "\n\n😮‍💨 **AGOTAMIENTO:** Estás funcionando al límite: tus esfuerzos rinden la mitad y tu cuerpo lo paga."

        # 4. ACCIONES BÁSICAS CON MÁS KEYWORDS
        if any(p in texto_acciones for p in ["trabaj", "esfuerz"]) and not busca_trabajo:
            extra = int((10000 + nuevo["habilidad_tecnica"] * 500) * meses * mult)
            if nuevo["habilidad_tecnica"] > 50:
                extra = int(extra * 1.05)
            nuevo["dinero_personal"] += extra
            nuevo["energia"] = max(0, nuevo["energia"] - int(20 * meses))

        if any(p in texto_acciones for p in ["estudi", "aprend", "universi"]):
            nuevo["habilidad_tecnica"] = min(100, nuevo["habilidad_tecnica"] + int(5 * meses * mult))
            nuevo["habilidad_politica"] = min(100, nuevo["habilidad_politica"] + int(2 * meses * mult))
            nuevo["energia"] = max(0, nuevo["energia"] - int(15 * meses))

        if any(p in texto_acciones for p in ["descans", "dormir", "vacacion"]):
            nuevo["energia"] = min(nuevo["energia_max"], nuevo["energia"] + int(30 * meses))

        if any(p in texto_acciones for p in ["privatiz", "liberaliz", "vender empresa estatal"]):
            nuevo["facciones"]["Empresarios"] = min(100, nuevo["facciones"]["Empresarios"] + 10)
            nuevo["facciones"]["Sindicatos"] = max(0, nuevo["facciones"]["Sindicatos"] - 10)
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 5)
            narrativa += "\n\n🏭 **PRIVATIZACIÓN:** Avanzaste con la privatización. Los empresarios te apoyan, los sindicatos te critican."
            agregar_memoria(nuevo, "Avanzó con privatizaciones.")

        if any(p in texto_acciones for p in ["bajar impuesto", "reducción de impuesto", "quitar impuesto", "impuesto pymes"]):
            nuevo["facciones"]["Empresarios"] = min(100, nuevo["facciones"]["Empresarios"] + 10)
            nuevo["tesoro_nacional"] = max(0, nuevo["tesoro_nacional"] - 500000)
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 3)
            narrativa += "\n\n💸 **BAJA DE IMPUESTOS:** Redujiste la carga impositiva. Los empresarios celebran, el tesoro se achica."
            agregar_memoria(nuevo, "Bajó impuestos.")

        if any(p in texto_acciones for p in ["alianza", "cámara de comercio", "camara de comercio", "reunir con empresario", "juntar con empresario"]):
            nuevo["facciones"]["Empresarios"] = min(100, nuevo["facciones"]["Empresarios"] + 10)
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 5)
            if nuevo["habilidad_politica"] > 50:
                nuevo["facciones"]["Empresarios"] = min(100, nuevo["facciones"]["Empresarios"] + 5)
                narrativa += "\n\n🤝 **ALIANZA EMPRESARIAL:** Tu habilidad política te permitió cerrar un acuerdo sólido con la Cámara de Comercio."
            else:
                narrativa += "\n\n🤝 **ALIANZA EMPRESARIAL:** Te reuniste con la Cámara de Comercio. Buena relación con el sector privado."
            agregar_memoria(nuevo, "Formó alianza con empresarios.")

        if any(p in texto_acciones for p in ["sindicato", "cg", "trabajadores", "obreros"]):
            nuevo["facciones"]["Sindicatos"] = min(100, nuevo["facciones"]["Sindicatos"] + 10)
            nuevo["facciones"]["Empresarios"] = max(0, nuevo["facciones"]["Empresarios"] - 5)
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 3)
            narrativa += "\n\n✊ **REUNIÓN SINDICAL:** Te juntaste con los sindicatos. Los trabajadores te ven con buenos ojos."
            agregar_memoria(nuevo, "Se reunió con sindicatos.")

        if any(p in texto_acciones for p in ["donar", "caridad", "ayuda social", "comedor", "donación", "donacion"]):
            if nuevo["dinero_personal"] >= 10000:
                nuevo["dinero_personal"] -= 10000
                nuevo["reputacion"] = min(100, nuevo["reputacion"] + 5)
                nuevo["opinion_publica"] = min(100, nuevo["opinion_publica"] + 3)
                narrativa += "\n\n❤️ **DONACIÓN:** Donaste $10.000 a obras de caridad. Tu imagen pública mejora."
                agregar_memoria(nuevo, "Donó a caridad.")
            else:
                narrativa += "\n\n⚠️ **Sin fondos:** No tenés $10.000 para donar."

        if any(p in texto_acciones for p in ["debate", "discurso", "hablar en público", "entrevista", "tv", "televisión", "television"]):
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 5)
            nuevo["opinion_publica"] = min(100, nuevo["opinion_publica"] + 3)
            if nuevo["habilidad_politica"] > 50:
                nuevo["reputacion"] = min(100, nuevo["reputacion"] + 3)
                narrativa += "\n\n🎙️ **DISCURSO PÚBLICO:** Tu habilidad política brilló en los medios. +8 reputación."
            else:
                narrativa += "\n\n🎙️ **DISCURSO PÚBLICO:** Hablaste en público. +5 reputación."
            agregar_memoria(nuevo, "Dio un discurso público.")

        if any(p in texto_acciones for p in ["proponer ley", "proyecto de ley", "presentar ley", "iniciar proceso"]):
            nuevo["reputacion"] = min(100, nuevo["reputacion"] + 5)
            nuevo["habilidad_politica"] = min(100, nuevo["habilidad_politica"] + 2)
            narrativa += "\n\n📜 **PROPUESTA LEGISLATIVA:** Presentaste un proyecto. +5 reputación, +2 habilidad política."
            agregar_memoria(nuevo, "Presentó un proyecto de ley.")

        if any(p in texto_acciones for p in ["manifestación", "manifestacion", "marcha", "protesta", "cacerolazo"]):
            nuevo["opinion_publica"] = min(100, nuevo["opinion_publica"] + 5)
            nuevo["estabilidad_pais"] = max(0, nuevo["estabilidad_pais"] - 3)
            narrativa += "\n\n✊ **MANIFESTACIÓN:** Participaste en una marcha. +5 opinión pública, -3 estabilidad."
            agregar_memoria(nuevo, "Participó en una manifestación.")

        # 4.5 Energía en cero castiga salud física
        if nuevo["energia"] <= 0:
            nuevo["salud_fisica"] = max(0, nuevo["salud_fisica"] - int(5 * meses))

        # 5. Familia
        if nuevo.get("pareja_nombre") != "Nadie":
            if any(p in texto_acciones for p in ["pareja", "cena", "romant", "viaje"]):
                nuevo["pareja_afinidad"] = min(100, nuevo["pareja_afinidad"] + int(15 * meses))
                nuevo["dinero_personal"] -= int(10000 * meses)
            else:
                nuevo["pareja_afinidad"] = max(0, nuevo["pareja_afinidad"] - int(5 * meses))
            if nuevo["pareja_afinidad"] <= 0:
                narrativa += "\n\n💔 **DIVORCIO:** Tu pareja te dejó. Perdiste la mitad de tu fortuna."
                nuevo["dinero_personal"] = int(nuevo["dinero_personal"] * 0.5)
                nuevo["pareja_nombre"] = "Nadie"
                nuevo["salud_mental"] = max(0, nuevo["salud_mental"] - 10)
                agregar_memoria(nuevo, "Divorcio doloroso: la fortuna familiar se partió al medio.")

        # 6. Ministros (con consecuencias por deslealtad)
        if nuevo.get("cargo_politico") == "Presidente":
            for cargo, m in nuevo["ministros"].items():
                if m["nombre"] == "Vacante":
                    continue
                m["lealtad"] = max(0, m["lealtad"] - int(2 * meses))
                if m["corrupcion"] > 50:
                    nuevo["nivel_corrupcion"] = min(100, nuevo["nivel_corrupcion"] + int(2 * meses))
                    nuevo["escandalo_acumulado"] = min(100, nuevo["escandalo_acumulado"] + int(3 * meses))
                if cargo == "Economia" and m["lealtad"] > 30 and m["corrupcion"] < 50:
                    nuevo["inflacion"] = max(0, nuevo["inflacion"] - int(1 * meses))
                if m["lealtad"] <= 10:
                    roll = random.random()
                    if roll < 0.3:
                        nuevo["escandalo_acumulado"] = min(100, nuevo["escandalo_acumulado"] + 15)
                        narrativa += f"\n\n🕵️ **FUGA DE INFORMACIÓN:** {m['nombre']} filtró dossiers confidenciales a la prensa."
                        agregar_memoria(nuevo, f"{m['nombre']} filtró información confidencial del gabinete.")
                    elif roll < 0.5:
                        m["nombre"] = "Vacante"
                        m["lealtad"] = 50
                        m["corrupcion"] = 0
                        nuevo["aprobacion_publica"] = max(0, nuevo["aprobacion_publica"] - 5)
                        narrativa += f"\n\n🚪 **RENUNCIA:** El ministro de {cargo} renunció públicamente acusándote de mal trato."
                        agregar_memoria(nuevo, f"Renuncia escandalosa del ministro de {cargo}.")

        # 7. SISTEMA DE EMPRESAS 2.0 (Crecimiento Escalonado)
        DIVIDENDOS_NIVEL = {1: 10000, 2: 30000, 3: 90000, 4: 270000, 5: 810000}
        
        if nuevo.get("corporaciones"):
            total_div = 0
            for emp, nivel in list(nuevo["corporaciones"].items()):
                if "corporaciones_progreso" not in nuevo:
                    nuevo["corporaciones_progreso"] = {}
                if emp not in nuevo["corporaciones_progreso"]:
                    nuevo["corporaciones_progreso"][emp] = 0

                progreso = nuevo["corporaciones_progreso"][emp] + int(5 * meses)
                
                if progreso >= 100 and nivel < 5:
                    nuevo["corporaciones"][emp] = nivel + 1
                    progreso = 0
                    narrativa += f"\n\n📈 **¡{emp} creció!** Ahora es Nivel {nivel + 1}."

                nuevo["corporaciones_progreso"][emp] = progreso

                div = DIVIDENDOS_NIVEL.get(nivel, 10000)
                if nuevo["habilidad_negocios"] > 50:
                    div = int(div * 1.2)
                total_div += div

            if total_div > 0:
                nuevo["dinero_personal"] += int(total_div * meses)
                narrativa += f"\n\n🏢 **DIVIDENDOS CORPORATIVOS:** +${int(total_div * meses):,} este mes."

        # 8. Megaobras
        for obra in list(nuevo["megaobras_activas"]):
            obra["turnos"] -= max(1, dias // 30)
            if obra["turnos"] <= 0:
                nuevo["megaobras_completadas"].append(obra["nombre"])
                nuevo["megaobras_activas"].remove(obra)
                narrativa += f"\n\n🏗️ **OBRA COMPLETADA:** ¡Inauguraste {obra['nombre']}!"
                agregar_memoria(nuevo, f"Se inauguró la megaobra {obra['nombre']}.")
                if obra["efecto"] == "Industria":
                    nuevo["produccion_industrial"] = min(100, nuevo.get("produccion_industrial", 50) + 20)
                elif obra["efecto"] == "Inflacion":
                    nuevo["inflacion"] = max(0, nuevo["inflacion"] - 15)
                elif obra["efecto"] == "Aprobacion":
                    nuevo["aprobacion_publica"] = min(100, nuevo["aprobacion_publica"] + 20)

        # 9. RIVALES ACTIVOS
        msgs_rivales = accion_rivales(nuevo)
        if msgs_rivales:
            narrativa += "\n\n" + "\n".join(msgs_rivales)

        # 10. Eventos de decisión (pueden activar mini-juegos)
        if random.random() < 0.15 and not nuevo.get("evento_decision") and not nuevo.get("licitacion_activa"):
            evento = generar_evento_decision(nuevo.get("cargo_politico", "Ciudadano"))
            if "mini_juego" in evento and evento["mini_juego"] == "licitacion":
                nuevo["licitacion_activa"] = {
                    "titulo": evento["titulo"],
                    "desc": evento["desc"],
                    "monto_max": evento["monto_max"],
                    "riesgo_base": evento["riesgo_base"],
                    "monto_elegido": 0,
                }
                narrativa += f"\n\n🎮 **MINI-JUEGO: LICITACIÓN TURBIA** - {evento['titulo']}"
            else:
                nuevo["evento_decision"] = evento

        # 11. Crisis nacionales (pueden activar mini-juego de crisis)
        if random.random() < 0.05 and not nuevo.get("crisis_activa") and not nuevo.get("crisis_minijuego"):
            crisis = generar_crisis_nacional()
            if "mini_juego" in crisis and crisis["mini_juego"] == "crisis_financiera":
                nuevo["crisis_minijuego"] = {
                    "tipo": crisis["tipo"],
                    "desc": crisis["desc"],
                    "turno_actual": 1,
                    "decisiones": [],
                }
                narrativa += f"\n\n🎮 **MINI-JUEGO: CRISIS EN 3 TURNOS** - {crisis['tipo']}"
            else:
                nuevo["crisis_activa"] = crisis
                narrativa += f"\n\n🚨 **CRISIS NACIONAL:** {crisis['desc']}"
                agregar_memoria(nuevo, f"Estalló la crisis: {crisis['tipo']}.")

        if nuevo.get("crisis_activa"):
            crisis = nuevo["crisis_activa"]
            nuevo["salud_mental"] = max(0, nuevo["salud_mental"] - int(2 * meses))
            if crisis["efecto"] == "economia":
                nuevo["produccion_industrial"] = max(0, nuevo["produccion_industrial"] - 5)
            elif crisis["efecto"] == "estabilidad":
                nuevo["estabilidad_pais"] = max(0, nuevo["estabilidad_pais"] - 5)
            elif crisis["efecto"] == "inflacion":
                nuevo["inflacion"] = min(100, nuevo["inflacion"] + 5)
            elif crisis["efecto"] == "tesoro":
                nuevo["tesoro_nacional"] = max(0, nuevo["tesoro_nacional"] - 500000)
            crisis["duracion"] -= 1
            if crisis["duracion"] <= 0:
                nuevo["crisis_activa"] = {}
                narrativa += "\n\n✅ **CRISIS SUPERADA:** La crisis llegó a su fin."
                agregar_memoria(nuevo, "La crisis nacional fue superada.")

        # 12. Salud mental baja: se nota en público
        if nuevo["salud_mental"] < 20:
            nuevo["opinion_publica"] = max(0, nuevo["opinion_publica"] - int(5 * meses))
            narrativa += "\n\n🧠 **CRISIS PERSONAL:** Tu desgaste mental es visible y la opinión pública lo percibe."

        # 13. Golpe / juicio / facciones / escándalo / históricos / logros / objetivos
        golpe = verificar_golpe_estado(nuevo)
        if golpe:
            game_over = golpe
            agregar_memoria(nuevo, "GOLPE DE ESTADO: fin del mandato por la fuerza.")

        juicio = verificar_juicio_politico(nuevo)
        if juicio:
            game_over = juicio
            agregar_memoria(nuevo, "Juicio político: removido del cargo por corrupción.")

        traiciones = verificar_traicion_facciones(nuevo)
        if traiciones:
            narrativa += "\n\n" + "\n".join(traiciones)

        escandalo = verificar_escandalo(nuevo)
        if escandalo:
            narrativa += f"\n\n{escandalo}"
            agregar_memoria(nuevo, "Escándalo mediático masivo por corrupción acumulada.")

        historicos = verificar_eventos_historicos(nuevo)
        if historicos:
            narrativa += "\n\n" + "\n".join(historicos)

        nuevos_logros = verificar_logros(nuevo)
        if nuevos_logros:
            narrativa += f"\n\n🏆 **LOGROS DESBLOQUEADOS:** {', '.join(nuevos_logros)}"

        objetivos_nuevos = evaluar_objetivos(nuevo)
        if objetivos_nuevos:
            narrativa += f"\n\n🎯 **OBJETIVO DINÁSTICO CUMPLIDO:** {', '.join(objetivos_nuevos)}"
            for o in objetivos_nuevos:
                agregar_memoria(nuevo, f"Objetivo dinástico cumplido: {o}.")

        # 14. HOSPITALIZACIÓN por salud crítica
        if nuevo["salud_fisica"] < 20 and not nuevo.get("hospitalizado"):
            nuevo["hospitalizado"] = True
            narrativa += "\n\n🏥 **HOSPITALIZACIÓN DE URGENCIA:** Tu cuerpo colapsó por el desgaste. Debés recuperarte antes de seguir actuando."
            agregar_memoria(nuevo, "Hospitalización de urgencia por salud crítica.")

        # 15. Muerte (edad + salud)
        prob_muerte = 0
        if nuevo["edad"] > 65:
            prob_muerte += (nuevo["edad"] - 65) * 2
        if nuevo["salud_fisica"] < 20:
            prob_muerte += (20 - nuevo["salud_fisica"]) * 2
        if nuevo["salud_mental"] < 10:
            prob_muerte += 10

        if random.randint(1, 100) <= prob_muerte:
            game_over = f"👴 **MUERTE:** A los {int(nuevo['edad'])} años, tu cuerpo dijo basta."
            agregar_memoria(nuevo, f"Muerte del patriarca a los {int(nuevo['edad'])} años.")

        # 16. RESUMEN DE CAMBIOS DEL TURNO
        resumen = []
        for clave, emoji in CLAVES_RESUMEN.items():
            delta = nuevo.get(clave, 0) - antes.get(clave, 0)
            if abs(delta) >= 1:
                signo = "+" if delta > 0 else "-"
                resumen.append(f"{emoji} {signo}{abs(int(delta)):,}")
        nuevo["resumen_ultimo_turno"] = resumen

    # Incrementar contador de turnos desde último aumento
    if "turnos_desde_ultimo_aumento" in nuevo and nuevo["turnos_desde_ultimo_aumento"] < 999:
        nuevo["turnos_desde_ultimo_aumento"] += 1

    return parse_estado(nuevo), narrativa, game_over

# ==============================================================================
# ELECCIONES, LEGADO Y BIOGRAFÍA
# ==============================================================================

def resolver_eleccion(cargo_objetivo: str, estado: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Calcula el resultado de una campaña electoral basándose en el estado actual.
    Devuelve: (exito, mensaje_narrativo)
    """
    est = estado

    base_votos = (est["reputacion"] * 0.4) + (est["opinion_publica"] * 0.4) + ((est["fondo_campaña"] / 10000) * 0.2)
    if est["habilidad_politica"] > 50:
        base_votos += 5

    votos_finales = base_votos + random.randint(-20, 20)
    umbral, oponente = calcular_umbral(cargo_objetivo, est.get("rivales", []))
    exito = votos_finales >= umbral

    est["campaña_activa"] = False
    est["fondo_campaña"] = 0
    est["cargo_objetivo"] = ""
    est["mapa_electoral"] = {p: max(0, min(100, int(votos_finales + random.randint(-25, 25)))) for p in PROVINCIAS}

    nombre_oponente = oponente["nombre"] if oponente else "sin rival fuerte"

    if exito:
        est["cargo_politico"] = cargo_objetivo
        if cargo_objetivo == "Presidente":
            est["tesoro_nacional"] = 5000000
        if oponente:
            oponente["poder"] = max(0, oponente["poder"] - 10)
            oponente["relacion"] = max(0, oponente["relacion"] - 10)
        agregar_memoria(est, f"Victoria electoral contra {nombre_oponente}: consagrado como {cargo_objetivo}.")
        return True, f"¡GANASTE! Con {int(votos_finales)} puntos superaste el umbral de {umbral} y derrotaste a {nombre_oponente}. Te consagraste como {cargo_objetivo}."
    else:
        est["reputacion"] = max(0, est["reputacion"] - 10)
        if oponente:
            oponente["poder"] = min(100, oponente["poder"] + 10)
        agregar_memoria(est, f"Derrota electoral contra {nombre_oponente} intentando llegar a {cargo_objetivo}.")
        return False, f"DERROTA. Lograste {int(votos_finales)} puntos y necesitabas {umbral}. {nombre_oponente.capitalize()} capitalizó tu derrota."


def calcular_legado(estado: Dict[str, Any]) -> Tuple[int, str]:
    """
    Calcula el puntaje final y el rango de legado de la dinastía.
    Devuelve: (puntos, rango)
    """
    est = estado

    puntos = int(est.get("dinero_personal", 0) / 10000)
    puntos += {"Ciudadano": 0, "Diputado": 200, "Gobernador": 500, "Presidente": 1000}.get(est.get("cargo_politico", "Ciudadano"), 0)
    puntos += len(est.get("megaobras_completadas", [])) * 100
    puntos += int(est.get("aprobacion_publica", 0) / 2)
    puntos += len(est.get("logros", [])) * 50
    puntos += len(est.get("objetivos_completados", [])) * 150
    puntos += est.get("generacion_actual", 1) * 100

    rango = "F"
    if puntos > 2500:
        rango = "S"
    elif puntos > 1800:
        rango = "A"
    elif puntos > 1200:
        rango = "B"
    elif puntos > 600:
        rango = "C"
    elif puntos > 250:
        rango = "D"

    return puntos, rango


def generar_biografia(estado: Dict[str, Any]) -> str:
    """Genera un string con la biografía resumida de la dinastía para descargar."""
    lineas = [f"BIOGRAFÍA DE LA DINASTÍA {estado.get('apellido_dinastia', 'SIN NOMBRE').upper()}", "=" * 60]
    lineas.append(f"Generaciones: {estado.get('generacion_actual', 1)} | Cargo: {estado.get('cargo_politico')}")
    lineas.append(f"Patrimonio: ${estado.get('dinero_personal', 0):,} | Logros: {', '.join(estado.get('logros', [])) or 'Ninguno'}")
    lineas.append("\nHITOS:")
    for m in estado.get("memoria", [])[-15:]:
        lineas.append(f"  - {m}")
    return "\n".join(lineas)


# ==============================================================================
# PERSISTENCIA Y GUARDADO
# ==============================================================================

def leer_hall_of_fame() -> List[Dict[str, Any]]:
    """Lee el archivo JSON del Salón de la Fama."""
    if not os.path.exists(HOF_FILE):
        return []
    try:
        with open(HOF_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_hall_of_fame(puntos: int, rango: str, estado: Dict[str, Any]) -> None:
    """Guarda el resultado de la partida en el Salón de la Fama."""
    hof = leer_hall_of_fame()
    hof.append({
        "apellido": estado.get("apellido_dinastia", "?"),
        "generaciones": estado.get("generacion_actual", 1),
        "cargo": estado.get("cargo_politico", ""),
        "puntos": puntos,
        "rango": rango,
    })
    hof.sort(key=lambda e: e["puntos"], reverse=True)
    with open(HOF_FILE, "w", encoding="utf-8") as f:
        json.dump(hof[:10], f, ensure_ascii=False, indent=2)


def _payload_guardado() -> Dict[str, Any]:
    """Extrae las variables necesarias de session_state para guardar."""
    return {k: st.session_state[k] for k in ["juego_iniciado", "game_over", "sistema", "estado", "mensajes"] if k in st.session_state}


def _migrar(data: Dict[str, Any]) -> Dict[str, Any]:
    """Migra o carga datos de guardado asegurando compatibilidad de esquema."""
    if isinstance(data, dict) and data.get("schema_version") == SCHEMA_VERSION:
        return data.get("data", {})
    payload = data.get("data", data) if isinstance(data, dict) else {}
    payload["estado"] = parse_estado(payload.get("estado", {}))
    payload.setdefault("mensajes", [])
    payload.setdefault("game_over", None)
    payload.setdefault("juego_iniciado", True)
    payload.setdefault("sistema", "")
    return payload


def save_to_disk() -> None:
    """Guarda la partida actual en el archivo principal."""
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"schema_version": SCHEMA_VERSION, "data": _payload_guardado()}, f, ensure_ascii=False, indent=2)
    st.toast("Partida guardada.")


def load_from_disk() -> bool:
    """Carga la partida desde el archivo principal."""
    if not os.path.exists(SAVE_FILE):
        st.toast("No hay partida guardada.")
        return False
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = _migrar(json.load(f))
    for k, v in data.items():
        st.session_state[k] = v
    st.toast("Partida cargada.")
    return True


def save_to_slot(slot_num: int) -> None:
    """Guarda la partida en un slot específico (0, 1 o 2)."""
    with open(SAVE_SLOTS[slot_num], "w", encoding="utf-8") as f:
        json.dump({"schema_version": SCHEMA_VERSION, "data": _payload_guardado()}, f, ensure_ascii=False, indent=2)
    st.toast(f"Guardado en Slot {slot_num + 1}.")


def load_from_slot(slot_num: int) -> bool:
    """Carga la partida desde un slot específico."""
    if not os.path.exists(SAVE_SLOTS[slot_num]):
        st.toast(f"Slot {slot_num + 1} vacío.")
        return False
    with open(SAVE_SLOTS[slot_num], "r", encoding="utf-8") as f:
        data = _migrar(json.load(f))
    for k, v in data.items():
        st.session_state[k] = v
    st.toast(f"Cargado desde Slot {slot_num + 1}.")
    return True