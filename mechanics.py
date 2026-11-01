import random
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from entidades import Empresa, Hijo, Ministro, Medio, Rival
from state import TIPOS_EMPRESA, PROVINCIAS, NOMBRES_PILA
import prompts

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES LOCALES
# ==============================================================================

COSTO_VIDA_POR_NIVEL = {
    1: 8000, 2: 15000, 3: 25000, 4: 45000, 5: 80000, 6: 150000,
}

SALARIOS_BASE = {
    "Desempleado": 0, "Junior Developer": 150000, "Asesor Político": 120000,
    "Emprendedor": 100000, "Gerente": 450000, "Director": 800000, "CEO": 1500000,
}

FACCIONES_OPUESTAS = {
    "Militares": "Sindicatos",
    "Sindicatos": "Empresarios",
    "Empresarios": "Sindicatos",
    "Iglesia": "Populistas",
}

# ==============================================================================
# FUNCIONES DE UTILIDAD Y SANITIZACIÓN
# ==============================================================================

def sanitizar_accion(texto: str) -> Tuple[bool, str]:
    """Valida que la acción no sea un intento de inyección de prompts."""
    texto_lower = texto.lower()
    palabras_prohibidas = ["ignore previous instructions", "system prompt", "act as", "olvida tus reglas"]
    
    for palabra in palabras_prohibidas:
        if palabra in texto_lower:
            return False, "🚫 Acción bloqueada por seguridad."
            
    if len(texto.strip()) < 3:
        return False, "La acción es demasiado corta."
        
    return True, ""

# ==============================================================================
# LÓGICA DE ECONOMÍA Y TURNO (PASIVO)
# ==============================================================================

def procesar_economia(estado: Dict[str, Any]) -> str:
    """Calcula ingresos, gastos, dividendos e inflación al pasar el tiempo."""
    resumen = []
    
    nivel_vida = estado.get("nivel_calidad_vida", 1)
    costo_vida = COSTO_VIDA_POR_NIVEL.get(nivel_vida, 8000)
    inflacion = estado.get("inflacion", 25.0) / 100.0
    costo_vida_real = int(costo_vida * (1 + inflacion))
    
    estado["dinero_personal"] -= costo_vida_real
    resumen.append(f"💸 Costo de vida: -${costo_vida_real:,}")
    
    trabajo = estado.get("trabajo_actual", "Desempleado")
    sueldo_base = SALARIOS_BASE.get(trabajo, 0)
    bonus_tecnica = estado.get("habilidad_tecnica", 20) / 100.0
    sueldo_final = int(sueldo_base * (1 + bonus_tecnica))
    
    estado["dinero_personal"] += sueldo_final
    estado["ingreso_mensual"] = sueldo_final
    if sueldo_final > 0:
        resumen.append(f"💼 Sueldo ({trabajo}): +${sueldo_final:,}")
        
    corporaciones = estado.get("corporaciones", {})
    dividendos_totales = 0
    habilidad_negocios = estado.get("habilidad_negocios", 20)
    
    for key, empresa in corporaciones.items():
        if isinstance(empresa, Empresa):
            dividendo = empresa.calcular_dividendo_real(habilidad_negocios)
            empresa.progreso_nivel += random.randint(1, 5)
            if empresa.progreso_nivel >= 100 and empresa.nivel < 5:
                empresa.nivel += 1
                empresa.progreso_nivel = 0
                resumen.append(f"📈 ¡{empresa.nombre} subió al Nivel {empresa.nivel}!")
            dividendos_totales += dividendo
            
    if dividendos_totales > 0:
        estado["dinero_personal"] += dividendos_totales
        resumen.append(f"🏢 Dividendos de empresas: +${dividendos_totales:,}")
        
    estado["edad"] = estado.get("edad", 24) + 0.083
    
    return "\n".join(resumen)

# ==============================================================================
# ACCIONES DEL JUGADOR (ACTIVO)
# ==============================================================================

def intentar_fundar_empresa(estado: Dict[str, Any], tipo_empresa: str) -> Tuple[bool, str]:
    """Lógica para fundar una nueva empresa."""
    if tipo_empresa not in TIPOS_EMPRESA:
        return False, f"Tipo de empresa '{tipo_empresa}' no válido."
        
    requisitos = TIPOS_EMPRESA[tipo_empresa]
    
    if estado.get("cargo_politico") == "Presidente":
        return False, "⚖️ Como Presidente tenés conflicto de interés. No podés fundar empresas directamente."
        
    if estado.get("dinero_personal", 0) < requisitos["costo"]:
        return False, f"💸 No tenés fondos. Necesitás ${requisitos['costo']:,} y tenés ${estado.get('dinero_personal', 0):,}."
        
    if estado.get("habilidad_negocios", 0) < requisitos["req_negocios"]:
        return False, f"📊 Habilidad insuficiente. Necesitás {requisitos['req_negocios']} de Negocios."
        
    estado["dinero_personal"] -= requisitos["costo"]
    
    nueva_empresa = Empresa(
        nombre=f"{tipo_empresa} {estado.get('apellido_dinastia', 'S.A.')}",
        tipo=tipo_empresa,
        nivel=1,
        dividendo_base=requisitos["dividendo_base"]
    )
    
    key = tipo_empresa.lower().replace(" ", "_")
    estado["corporaciones"][key] = nueva_empresa
    
    return True, f"🏢 **ÉXITO:** Fundaste {nueva_empresa.nombre}. Generará ${requisitos['dividendo_base']:,} base/mes."

def intentar_estudiar(estado: Dict[str, Any], enfoque: str) -> Tuple[bool, str]:
    """El jugador estudia para subir una habilidad específica."""
    costo_energia = 20
    if estado.get("energia", 0) < costo_energia:
        return False, "😴 Estás muy cansado para estudiar."
        
    estado["energia"] -= costo_energia
    ganancia_base = random.randint(2, 5)
    
    if enfoque == "tecnica":
        estado["habilidad_tecnica"] = min(100, estado.get("habilidad_tecnica", 20) + ganancia_base)
        return True, f"📚 Estudiaste programación/sistemas. +{ganancia_base} Habilidad Técnica."
    elif enfoque == "politica":
        estado["habilidad_politica"] = min(100, estado.get("habilidad_politica", 20) + ganancia_base)
        return True, f"📚 Leíste sobre ciencia política y oratoria. +{ganancia_base} Habilidad Política."
    elif enfoque == "negocios":
        estado["habilidad_negocios"] = min(100, estado.get("habilidad_negocios", 20) + ganancia_base)
        return True, f"📚 Hiciste un curso de finanzas. +{ganancia_base} Habilidad Negocios."
    else:
        return False, "Enfoque no válido."

def intentar_mejorar_vivienda(estado: Dict[str, Any]) -> Tuple[bool, str]:
    """Sube el nivel de calidad de vida."""
    nivel_actual = estado.get("nivel_calidad_vida", 1)
    if nivel_actual >= 6:
        return False, "Ya vivís en la máxima categoría (Mansión)."
        
    costo_mejora = COSTO_VIDA_POR_NIVEL.get(nivel_actual + 1, 15000) * 10
    
    if estado.get("dinero_personal", 0) < costo_mejora:
        return False, f"💸 Mudarse cuesta ${costo_mejora:,}. No tenés suficiente."
        
    estado["dinero_personal"] -= costo_mejora
    estado["nivel_calidad_vida"] = nivel_actual + 1
    estado["salud_mental"] = min(100, estado.get("salud_mental", 100) + 10)
    
    return True, f"🏠 **MEJORA:** Ahora vivís en un lugar mejor (Nivel {nivel_actual + 1}). Tu salud mental mejora, pero tus gastos fijos suben."

# ==============================================================================
# POLÍTICA, CAMPAÑAS Y ELECCIONES
# ==============================================================================

def calcular_exito_campana(estado: Dict[str, Any], cargo_objetivo: str) -> Tuple[bool, str]:
    """Calcula el porcentaje de votos basado en Habilidad Política, Facciones y Opinión."""
    score = (estado.get("aprobacion_publica", 50) * 0.6) + (estado.get("reputacion", 50) * 0.4)
    habilidad_pol = estado.get("habilidad_politica", 20)
    score += habilidad_pol * 0.5
    
    facciones = estado.get("facciones", {})
    if facciones:
        promedio_facciones = sum(facciones.values()) / len(facciones)
        score += (promedio_facciones - 50) * 0.3
        
    fondo = estado.get("fondo_campaña", 0)
    score += (fondo / 100000) * 2
    
    umbrales = {"Diputado": 40, "Gobernador": 60, "Presidente": 75}
    umbral = umbrales.get(cargo_objetivo, 50)
    
    factor_r = random.randint(-10, 10)
    score += factor_r
    score_final = min(100, max(0, score))
    
    if score_final >= umbral:
        return True, f"🏆 ¡Victoria! Obtuviste el {score_final:.1f}% de los votos (Necesitabas {umbral}%). Asumís como {cargo_objetivo}."
    else:
        return False, f"😔 Derrota. Obtuviste el {score_final:.1f}% de los votos (Necesitabas {umbral}%). La oposición se queda en el poder."

def invertir_en_campana(estado: Dict[str, Any], tipo: str) -> Tuple[bool, str]:
    """Gasta dinero personal para mejorar las chances electorales."""
    costo = 50000
    if estado.get("dinero_personal", 0) < costo:
        return False, "💸 No tenés $50,000 para invertir en campaña."
        
    estado["dinero_personal"] -= costo
    estado["fondo_campaña"] = estado.get("fondo_campaña", 0) + costo
    
    if tipo == "publicidad":
        estado["opinion_publica"] = min(100, estado.get("opinion_publica", 50) + 3)
        return True, "📺 Invertiste en publicidad. +3 Opinión Pública."
    elif tipo == "actos":
        estado["reputacion"] = min(100, estado.get("reputacion", 50) + 3)
        return True, "🎤 Invertiste en actos proselitistas. +3 Reputación."
    return False, "Tipo de inversión no válido."

# ==============================================================================
# GABINETE Y MINISTROS
# ==============================================================================

def procesar_efectos_ministros(estado: Dict[str, Any]) -> List[str]:
    """Se ejecuta cada mes. Los ministros afectan las stats del país."""
    efectos = []
    ministros = estado.get("ministros", {})
    
    for area, ministro in ministros.items():
        if not hasattr(ministro, 'eficiencia'): continue
        
        if area == "Economia":
            if ministro.eficiencia > 70:
                estado["inflacion"] = max(0, estado.get("inflacion", 25) - 0.5)
                efectos.append(f"📉 El Ministro de Economía {ministro.nombre} logró bajar la inflación.")
            elif ministro.eficiencia < 40:
                estado["inflacion"] += 1.0
                efectos.append(f"📈 La mala gestión de {ministro.nombre} subió la inflación.")
                
        if ministro.corrupcion > 60:
            estado["nivel_escandalo"] = min(100, estado.get("nivel_escandalo", 0) + 2)
            efectos.append(f"🤫 Rumores de corrupción salpican a {ministro.nombre} (+2 Escándalo).")
            
        if ministro.lealtad < 30 and random.random() < 0.1:
            estado["reputacion"] = max(0, estado.get("reputacion", 50) - 5)
            efectos.append(f"🗞️ {ministro.nombre} filtró información a la prensa. -5 Reputación.")
            
    return efectos

# ==============================================================================
# PRENSA Y MEDIOS
# ==============================================================================

def gestionar_prensa(estado: Dict[str, Any], medio_nombre: str, accion: str) -> Tuple[bool, str]:
    """Interactúa con los medios de comunicación."""
    medios = estado.get("medios", [])
    medio_obj = next((m for m in medios if m.nombre == medio_nombre), None)
    
    if not medio_obj:
        return False, "Ese medio no existe o no opera en el país."
        
    if accion == "pauta":
        if estado.get("dinero_personal", 0) < 30000:
            return False, "No tenés $30,000 para la pauta publicitaria."
        estado["dinero_personal"] -= 30000
        medio_obj.apoyo = min(100, medio_obj.apoyo + 10)
        return True, f"📰 Compraste pauta en {medio_nombre}. Su apoyo subió a {medio_obj.apoyo}."
        
    elif accion == "entrevista":
        exito_chance = estado.get("reputacion", 50)
        if random.randint(1, 100) <= exito_chance:
            medio_obj.apoyo = min(100, medio_obj.apoyo + 15)
            return True, f"🎙️ Entrevista exitosa en {medio_nombre}. Apoyo subió a {medio_obj.apoyo}."
        else:
            medio_obj.apoyo = max(-100, medio_obj.apoyo - 10)
            return False, f"🎙️ La entrevista en {medio_nombre} fue un desastre. Apoyo bajó a {medio_obj.apoyo}."
            
    return False, "Acción no válida."

# ==============================================================================
# LEYES Y DECRETOS
# ==============================================================================

def proponer_ley(estado: Dict[str, Any], nombre_ley: str, descripcion: str) -> Tuple[bool, str]:
    """Simula el debate y aprobación de una ley en el congreso."""
    if estado.get("cargo_politico") not in ["Presidente", "Gobernador"]:
        return False, "Solo podés proponer leyes siendo Gobernador o Presidente."
        
    facciones = estado.get("facciones", {})
    apoyo_promedio = sum(facciones.values()) / len(facciones) if facciones else 50
    
    costo_politico = 10 
    if estado.get("aprobacion_publica", 50) < 40:
        costo_politico += 20
        
    exito_chance = apoyo_promedio - costo_politico + random.randint(-10, 20)
    
    if exito_chance > 50:
        estado["aprobacion_publica"] = max(0, estado.get("aprobacion_publica", 50) - 5)
        estado["reputacion"] = min(100, estado.get("reputacion", 50) + 10)
        return True, f"⚖️ **LEY APROBADA:** '{nombre_ley}' fue sancionada. Tu reputación sube, pero el debate político te costó apoyo."
    else:
        estado["reputacion"] = max(0, estado.get("reputacion", 50) - 10)
        return False, f"❌ **LEY RECHAZADA:** La oposición bloqueó '{nombre_ley}'. Perdiste reputación en el intento."

# ==============================================================================
# ESCÁNDALO Y JUICIO POLÍTICO
# ==============================================================================

def verificar_estado_escandalo(estado: Dict[str, Any]) -> Optional[str]:
    """Chequea si el nivel de escándalo dispara un Juicio Político."""
    nivel = estado.get("nivel_escandalo", 0)
    
    if nivel >= 100 and not estado.get("juicio_politico_activo", False):
        estado["juicio_politico_activo"] = True
        return "🚨 **¡ESCÁNDALO MÁXIMO!** La oposición inició un JUICIO POLÍTICO en tu contra. Tenés 3 turnos para defenderte o serás destituido (Game Over)."
        
    if estado.get("juicio_politico_activo", False):
        defensa = estado.get("reputacion", 0) + estado.get("facciones", {}).get("Militares", 0)
        if defensa > 120:
            estado["juicio_politico_activo"] = False
            estado["nivel_escandalo"] = 50
            estado["juicio_politico_sobrevivido"] = True
            return "⚖️ **SOBREVIVISTE AL JUICIO:** Lograste frenar la destitución, pero tu imagen quedó muy dañada."
        else:
            return "GAME_OVER_JUICIO"
            
    return None

# ==============================================================================
# TENSIÓN DINÁMICA DE FACCIONES (v1.2)
# ==============================================================================

def procesar_tension_facciones(estado: Dict[str, Any]) -> List[str]:
    """Si una facción sube mucho (>75), la facción opuesta baja automáticamente."""
    mensajes = []
    facciones = estado.get("facciones", {})
    
    for faccion, valor in facciones.items():
        if valor > 75 and faccion in FACCIONES_OPUESTAS:
            opuesta = FACCIONES_OPUESTAS[faccion]
            if opuesta in facciones and facciones[opuesta] > 20:
                facciones[opuesta] = max(0, facciones[opuesta] - 10)
                mensajes.append(f"⚠️ Tu acercamiento a los {faccion} molestó a los {opuesta}. (-10 relación)")
                
    return mensajes

# ==============================================================================
# RIVALES ACTIVOS (v1.2)
# ==============================================================================

def procesar_turno_rivales(estado: Dict[str, Any]) -> List[str]:
    """Cada rival tiene una probabilidad de actuar cada turno."""
    mensajes = []
    rivales = estado.get("rivales", [])
    
    acciones_proc = [
        "se mantiene en silencio, observando tus movimientos",
        "refuerza sus alianzas en las sombras",
        "prepara su próxima jugada política",
        "analiza tus debilidades con paciencia",
        "conversa en secreto con otros opositores",
        "espera el momento justo para atacar"
    ]
    
    for rival in rivales:
        if random.random() < 0.20:
            try:
                mensajes_prompt = prompts.generar_prompt_accion_rival(
                    estado, rival.nombre, rival.poder
                )
                respuesta_raw = prompts.llamar_llm(mensajes_prompt, 0, "")
                data = prompts.extraer_json_de_respuesta(respuesta_raw)
                
                accion = data.get("accion", None)
                efectos = data.get("efectos", {})
                cambio_poder = data.get("cambio_poder_rival", 0)
                
                if accion:
                    for stat, valor in efectos.items():
                        if stat in estado and isinstance(valor, (int, float)):
                            if stat in ["reputacion", "aprobacion_publica", "opinion_publica"]:
                                estado[stat] = max(0, min(100, estado[stat] + valor))
                            elif stat == "dinero_personal":
                                estado[stat] += valor
                                
                    rival.poder = max(0, min(100, rival.poder + cambio_poder))
                    mensajes.append(f"🕴️ **{rival.nombre}**: {accion} (Su poder ahora es {rival.poder}%)")
                else:
                    accion_proc = random.choice(acciones_proc)
                    mensajes.append(f"🕴️ **{rival.nombre}** {accion_proc}. (Su poder: {rival.poder}%)")
                    
            except Exception as e:
                logger.error(f"Error procesando acción de rival {rival.nombre}: {e}")
                accion_proc = random.choice(acciones_proc)
                mensajes.append(f"🕴️ **{rival.nombre}** {accion_proc}. (Su poder: {rival.poder}%)")
                
    return mensajes

# ==============================================================================
# EVENTOS ALEATORIOS SORPRESIVOS (v1.2)
# ==============================================================================

def procesar_evento_aleatorio(estado: Dict[str, Any]) -> Tuple[bool, str]:
    """15% de probabilidad por turno de que ocurra un evento inesperado."""
    if random.random() < 0.15:
        try:
            mensajes_prompt = prompts.generar_prompt_evento_aleatorio(estado)
            respuesta_raw = prompts.llamar_llm(mensajes_prompt, 0, "")
            data = prompts.extraer_json_de_respuesta(respuesta_raw)
            
            titulo = data.get("titulo", "Evento Inesperado")
            descripcion = data.get("descripcion", "Algo ocurrió.")
            efectos = data.get("efectos", {})
            
            for stat, valor in efectos.items():
                if stat in estado and isinstance(valor, (int, float)):
                    if stat in ["reputacion", "aprobacion_publica", "energia", "salud_fisica"]:
                        estado[stat] = max(0, min(100, estado[stat] + valor))
                    elif stat == "dinero_personal":
                        estado[stat] += valor
                    elif stat == "nivel_escandalo":
                        estado[stat] = max(0, min(100, estado[stat] + valor))
                        
            return True, f"🎲 **{titulo}**\n{descripcion}"
            
        except Exception as e:
            logger.error(f"Error generando evento aleatorio: {e}")
            return False, ""
            
    return False, ""

# ==============================================================================
# SISTEMA DE LOGROS DINÁMICO (v1.2)
# ==============================================================================

LOGROS_DEFINICIONES = [
    {"id": "primer_millon", "nombre": "Magnate", "desc": "Acumular $1,000,000", "check": lambda e: e.get("dinero_personal", 0) >= 1000000},
    {"id": "presidente_joven", "nombre": "Joven Promesa", "desc": "Ser Presidente antes de los 45", "check": lambda e: e.get("cargo_politico") == "Presidente" and e.get("edad", 100) < 45},
    {"id": "empresa_nivel_3", "nombre": "Empresario", "desc": "Tener una empresa en Nivel 3", "check": lambda e: any(emp.nivel >= 3 for emp in e.get("corporaciones", {}).values() if hasattr(emp, 'nivel'))},
    {"id": "aprobacion_alta", "nombre": "Amado por el Pueblo", "desc": "Alcanzar 90% de Aprobación", "check": lambda e: e.get("aprobacion_publica", 0) >= 90},
    {"id": "sobreviviente", "nombre": "Sobreviviente", "desc": "Sobrevivir a un Juicio Político", "check": lambda e: e.get("juicio_politico_sobrevivido", False)},
    {"id": "dinastia_larga", "nombre": "Legado Eterno", "desc": "Llegar a la Generación 3", "check": lambda e: e.get("generacion_actual", 1) >= 3}
]

def verificar_logros(estado: Dict[str, Any]) -> List[str]:
    """Revisa las condiciones de los logros y desbloquea los que el jugador cumplió."""
    logros_desbloqueados = []
    logros_actuales = set(estado.get("logros", []))
    
    for logro in LOGROS_DEFINICIONES:
        if logro["id"] not in logros_actuales:
            try:
                if logro["check"](estado):
                    estado.setdefault("logros", []).append(logro["id"])
                    logros_desbloqueados.append(logro["nombre"])
            except Exception as e:
                logger.error(f"Error verificando logro {logro['id']}: {e}")
                
    return logros_desbloqueados

# ==============================================================================
# SISTEMA DE OBJETIVOS DINÁSTICOS CON RECOMPENSAS (v1.2.1)
# ==============================================================================

def verificar_objetivos_dinasticos(estado: Dict[str, Any]) -> List[str]:
    """Verifica si se completaron objetivos dinásticos y aplica recompensas."""
    mensajes = []
    objetivos = estado.get("objetivos_dinasticos", [])
    completados = set(estado.get("objetivos_completados", []))
    
    for obj in objetivos:
        if obj not in completados:
            completado = False
            
            if obj == "Alcanzar la Presidencia antes de los 55":
                if estado.get("cargo_politico") == "Presidente" and estado.get("edad", 100) < 55:
                    completado = True
                    estado.setdefault("bonificaciones_objetivos", []).append("Mandato Legítimo")
                    mensajes.append("🌟 **¡OBJETIVO DINÁSTICO CUMPLIDO!** Alcanzaste la Presidencia antes de los 55. Has desbloqueado: **Mandato Legítimo** - Tu Aprobación Pública nunca puede bajar del 40%.")
            
            elif obj == "Acumular $5M en patrimonio":
                if estado.get("dinero_personal", 0) >= 5000000:
                    completado = True
                    estado.setdefault("bonificaciones_objetivos", []).append("Magnate")
                    mensajes.append("🌟 **¡OBJETIVO DINÁSTICO CUMPLIDO!** Acumulaste $5M en patrimonio. Has desbloqueado: **Magnate** - Tu próximo heredero empieza con +20 Negocios y $500K extra.")
            
            elif obj == "Fundar una empresa Nivel 4":
                corporaciones = estado.get("corporaciones", {})
                if any(emp.nivel >= 4 for emp in corporaciones.values() if hasattr(emp, 'nivel')):
                    completado = True
                    estado.setdefault("bonificaciones_objetivos", []).append("Monopolio Familiar")
                    mensajes.append("🌟 **¡OBJETIVO DINÁSTICO CUMPLIDO!** Tienes una empresa en Nivel 4. Has desbloqueado: **Monopolio Familiar** - Todas tus empresas generan 25% más de dividendos.")
            
            elif obj == "Sobrevivir a 3 Crisis Nacionales":
                crisis_sobrevividas = estado.get("crisis_sobrevividas", 0)
                if crisis_sobrevividas >= 3:
                    completado = True
                    estado.setdefault("bonificaciones_objetivos", []).append("Acero Templado")
                    mensajes.append("🌟 **¡OBJETIVO DINÁSTICO CUMPLIDO!** Sobreviviste a 3 Crisis Nacionales. Has desbloqueado: **Acero Templado** - Tu Salud Mental y Física no bajan por escándalos.")
            
            if completado:
                estado.setdefault("objetivos_completados", []).append(obj)
    
    return mensajes

# ==============================================================================
# ROUTER DE ACCIONES DETERMINISTAS
# ==============================================================================

def ejecutar_accion_determinista(estado: Dict[str, Any], texto: str) -> Tuple[bool, str]:
    """Analiza el texto del jugador. Si es una acción mecánica conocida, la ejecuta directamente."""
    t = texto.lower().strip()
    
    logger.info(f"Procesando acción: '{t}'")
    
    if "fundar" in t and "empresa" in t:
        tipo = "Consultora"
        if "tech" in t or "startup" in t or "tecnología" in t: 
            tipo = "Tech Startup"
        elif "inmobiliaria" in t or "casa" in t or "inmueble" in t: 
            tipo = "Inmobiliaria"
        elif "banco" in t or "financiera" in t or "banca" in t: 
            tipo = "Banco"
        
        logger.info(f"Intentando fundar empresa tipo: {tipo}")
        ok, msg = intentar_fundar_empresa(estado, tipo)
        return ok, msg

    if ("crear" in t or "abrir" in t) and ("empresa" in t or "negocio" in t or "compañía" in t):
        tipo = "Consultora"
        if "tech" in t or "startup" in t: 
            tipo = "Tech Startup"
        elif "inmobiliaria" in t: 
            tipo = "Inmobiliaria"
        elif "banco" in t: 
            tipo = "Banco"
        
        ok, msg = intentar_fundar_empresa(estado, tipo)
        return ok, msg

    if "estudiar" in t or "capacitarse" in t or "aprender" in t:
        enfoque = "tecnica"
        if "politica" in t or "oratoria" in t or "política" in t: 
            enfoque = "politica"
        elif "negocio" in t or "finanza" in t or "economia" in t or "economía" in t: 
            enfoque = "negocios"
        
        ok, msg = intentar_estudiar(estado, enfoque)
        return ok, msg

    if "mudar" in t or "mejorar vivienda" in t or "comprar casa" in t or "mudarse" in t:
        ok, msg = intentar_mejorar_vivienda(estado)
        return ok, msg

    if "pauta" in t or "entrevista" in t or "publicidad" in t:
        medio_nombre = None
        for m in estado.get("medios", []):
            if m.nombre.lower() in t: 
                medio_nombre = m.nombre
        if medio_nombre:
            accion = "pauta" if "pauta" in t or "publicidad" in t else "entrevista"
            ok, msg = gestionar_prensa(estado, medio_nombre, accion)
            return ok, msg

    logger.info(f"Acción no detectada como determinista: '{t}'")
    return False, ""

# ==============================================================================
# PROCESADOR PRINCIPAL DE LA IA
# ==============================================================================

def procesar_respuesta(
    respuesta_ia: str, 
    dias_avanzados: int, 
    estado: Dict[str, Any],
    es_inicio: bool = False
) -> Tuple[Dict[str, Any], str, Optional[str]]:
    """Toma la respuesta cruda de la IA, extrae el JSON de efectos, aplica las mecánicas deterministas y retorna el nuevo estado."""
    narrativa = ""
    game_over = None
    
    json_match = re.search(r'\{.*\}', respuesta_ia, re.DOTALL)
    efectos_ia = {}
    
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            narrativa = data.get("narrativa", respuesta_ia)
            efectos_ia = data.get("efectos", {})
        except json.JSONDecodeError:
            narrativa = respuesta_ia
            
    for stat, valor in efectos_ia.items():
        if stat in estado and isinstance(valor, (int, float)):
            if stat in ["reputacion", "opinion_publica", "aprobacion_publica", "energia", "salud_fisica", "salud_mental"]:
                estado[stat] = max(0, min(100, estado[stat] + valor))
            elif stat in ["dinero_personal", "tesoro_nacional"]:
                estado[stat] += valor
                
    if dias_avanzados > 0 and not es_inicio:
        resumen_econ = procesar_economia(estado)
        narrativa += f"\n\n--- *Resumen del mes:* ---\n{resumen_econ}"
        
        efectos_min = procesar_efectos_ministros(estado)
        if efectos_min:
            narrativa += "\n" + "\n".join(efectos_min)
            
        tension_msg = procesar_tension_facciones(estado)
        if tension_msg:
            narrativa += "\n" + "\n".join(tension_msg)
            
        alerta_escandalo = verificar_estado_escandalo(estado)
        if alerta_escandalo == "GAME_OVER_JUICIO":
            game_over = "⚖️ **DESTITUCIÓN:** El Senado te encontró culpable. Tu carrera política terminó en deshonra."
        elif alerta_escandalo:
            narrativa += f"\n\n🚨 {alerta_escandalo}"
            
        if estado.get("edad", 24) >= 85 or estado.get("salud_fisica", 100) <= 0:
            game_over = "💀 **FIN DE UNA ERA:** Has fallecido. Es hora de que tu heredero tome el mando."

    return estado, narrativa, game_over