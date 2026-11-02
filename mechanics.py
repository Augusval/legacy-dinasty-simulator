import random
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from entidades import Empresa, Hijo, Ministro, Medio, Rival
from state import TIPOS_EMPRESA
import prompts

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES LOCALES
# ==============================================================================

COSTO_VIDA_POR_NIVEL = {
    1: 15000, 2: 25000, 3: 40000, 4: 70000, 5: 120000, 6: 200000,
}

# SUELDOS BALANCEADOS
SALARIOS_BASE = {
    "Desempleado": 0, 
    "Junior Developer": 30000,
    "Senior Developer": 60000,
    "CTO": 120000,
    "Emprendedor": 35000,
    "Gerente": 150000,
    "Director": 300000,
    "CEO": 500000,
}

# REQUISITOS DETALLADOS DE TRABAJOS
REQUISITOS_TRABAJO = {
    "Desempleado": {"req_reputacion": 0, "req_tecnica": 0, "req_politica": 0, "req_negocios": 0},
    "Junior Developer": {"req_reputacion": 0, "req_tecnica": 20, "req_politica": 0, "req_negocios": 0},
    "Senior Developer": {"req_reputacion": 20, "req_tecnica": 50, "req_politica": 0, "req_negocios": 0},
    "CTO": {"req_reputacion": 50, "req_tecnica": 80, "req_politica": 0, "req_negocios": 20},
    "Emprendedor": {"req_reputacion": 30, "req_tecnica": 0, "req_politica": 0, "req_negocios": 30},
    "Gerente": {"req_reputacion": 60, "req_tecnica": 0, "req_politica": 0, "req_negocios": 50},
    "Director": {"req_reputacion": 80, "req_tecnica": 0, "req_politica": 0, "req_negocios": 70},
    "CEO": {"req_reputacion": 95, "req_tecnica": 0, "req_politica": 0, "req_negocios": 85},
}

# CAMINOS PROFESIONALES (Cadenas de ascenso lógicas)
CAMINO_TECNICO = ["Desempleado", "Junior Developer", "Senior Developer", "CTO"]
CAMINO_CORPORATIVO = ["Desempleado", "Emprendedor", "Gerente", "Director", "CEO"]

# Mapeo de trabajo actual → siguiente ascenso
ASCENSOS_VALIDOS = {
    "Junior Developer": "Senior Developer",
    "Senior Developer": "CTO",
    "Emprendedor": "Gerente",
    "Gerente": "Director",
    "Director": "CEO",
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
# SISTEMA LABORAL (REFACTORIZADO)
# ==============================================================================

def intentar_buscar_trabajo(estado: Dict[str, Any], tipo_trabajo: str = None) -> Tuple[bool, str]:
    """El jugador busca trabajo. Si no especifica tipo, se le ofrece uno aleatorio según sus stats."""
    trabajo_actual = estado.get("trabajo_actual", "Desempleado")
    
    # Si ya tiene trabajo y no especificó tipo, ofrecer ascenso o cambio lateral
    if trabajo_actual != "Desempleado" and tipo_trabajo is None:
        return False, f"Ya trabajás como **{trabajo_actual}**. Usá *'pedir ascenso'* para buscar una promoción, o *'renunciar'* si querés cambiar de rumbo."
    
    # Si especificó un trabajo, postularse directamente
    if tipo_trabajo:
        return postularse_a_trabajo(estado, tipo_trabajo)
    
    # Si no especificó y está desempleado, ofrecer trabajos disponibles
    if trabajo_actual == "Desempleado":
        trabajos_disponibles = []
        for trabajo, reqs in REQUISITOS_TRABAJO.items():
            if trabajo == "Desempleado":
                continue
            if (estado.get("reputacion", 0) >= reqs["req_reputacion"] and
                estado.get("habilidad_tecnica", 0) >= reqs["req_tecnica"] and
                estado.get("habilidad_politica", 0) >= reqs["req_politica"] and
                estado.get("habilidad_negocios", 0) >= reqs["req_negocios"]):
                trabajos_disponibles.append(trabajo)
        
        if not trabajos_disponibles:
            return False, "📭 No calificás para ningún trabajo disponible. Estudiá para subir tus habilidades o ganá reputación."
        
        # Ofrecer el trabajo de menor nivel que califique
        trabajo_ofrecido = trabajos_disponibles[0]
        return postularse_a_trabajo(estado, trabajo_ofrecido)
    
    return False, "No se pudo procesar la búsqueda de trabajo."

def postularse_a_trabajo(estado: Dict[str, Any], tipo_trabajo: str) -> Tuple[bool, str]:
    """Postulación a un trabajo específico."""
    if tipo_trabajo not in REQUISITOS_TRABAJO:
        trabajos_validos = ", ".join(REQUISITOS_TRABAJO.keys())
        return False, f"Trabajo no válido. Opciones: {trabajos_validos}"
    
    reqs = REQUISITOS_TRABAJO[tipo_trabajo]
    trabajo_actual = estado.get("trabajo_actual", "Desempleado")
    
    # No podés postularte al mismo trabajo
    if tipo_trabajo == trabajo_actual:
        return False, f"Ya trabajás como {tipo_trabajo}."
    
    # Verificar requisitos mínimos
    fallos = []
    if estado.get("reputacion", 0) < reqs["req_reputacion"]:
        fallos.append(f"Reputación {reqs['req_reputacion']} (tenés {estado.get('reputacion', 0)})")
    if estado.get("habilidad_tecnica", 0) < reqs["req_tecnica"]:
        fallos.append(f"Técnica {reqs['req_tecnica']} (tenés {estado.get('habilidad_tecnica', 0)})")
    if estado.get("habilidad_politica", 0) < reqs["req_politica"]:
        fallos.append(f"Política {reqs['req_politica']} (tenés {estado.get('habilidad_politica', 0)})")
    if estado.get("habilidad_negocios", 0) < reqs["req_negocios"]:
        fallos.append(f"Negocios {reqs['req_negocios']} (tenés {estado.get('habilidad_negocios', 0)})")
    
    if fallos:
        return False, f"❌ **No cumplís los requisitos para {tipo_trabajo}:**\n" + "\n".join(f"  • {f}" for f in fallos)
    
    # Calcular probabilidad de éxito
    exceso_reputacion = estado.get("reputacion", 0) - reqs["req_reputacion"]
    exceso_habilidad = 0
    if reqs["req_tecnica"] > 0:
        exceso_habilidad += estado.get("habilidad_tecnica", 0) - reqs["req_tecnica"]
    if reqs["req_politica"] > 0:
        exceso_habilidad += estado.get("habilidad_politica", 0) - reqs["req_politica"]
    if reqs["req_negocios"] > 0:
        exceso_habilidad += estado.get("habilidad_negocios", 0) - reqs["req_negocios"]
    
    prob_exito = 50 + exceso_reputacion + (exceso_habilidad * 0.5) + random.randint(-10, 10)
    prob_exito = max(10, min(95, prob_exito))
    
    tirada = random.randint(1, 100)
    
    if tirada <= prob_exito:
        estado["trabajo_actual"] = tipo_trabajo
        estado["turnos_en_trabajo"] = 0
        sueldo = SALARIOS_BASE.get(tipo_trabajo, 0)
        return True, f"✅ **¡CONTRATADO!** Conseguiste el puesto de **{tipo_trabajo}** con un sueldo de ${sueldo:,}/mes. ¡Felicitaciones!"
    else:
        return False, f"❌ **Rechazado.** No te seleccionaron para {tipo_trabajo}. Seguí estudiando y ganando reputación para mejorar tus chances."

def intentar_pedir_ascenso(estado: Dict[str, Any]) -> Tuple[bool, str]:
    """El jugador pide un ascenso en su trabajo actual."""
    trabajo_actual = estado.get("trabajo_actual", "Desempleado")
    
    if trabajo_actual == "Desempleado":
        return False, "No podés pedir un ascenso si estás desempleado. Usá *'buscar trabajo'* primero."
    
    # Verificar si existe un ascenso válido para este trabajo
    if trabajo_actual not in ASCENSOS_VALIDOS:
        return False, f"No hay un ascenso disponible desde {trabajo_actual}. Considerá cambiar de carrera."
    
    trabajo_siguiente = ASCENSOS_VALIDOS[trabajo_actual]
    reqs_siguiente = REQUISITOS_TRABAJO[trabajo_siguiente]
    
    # Verificar experiencia mínima (6 turnos en el puesto)
    turnos_en_trabajo = estado.get("turnos_en_trabajo", 0)
    if turnos_en_trabajo < 6:
        return False, f"⏳ Necesitás al menos 6 meses de experiencia en {trabajo_actual} para pedir un ascenso. Llevás {turnos_en_trabajo} meses."
    
    # Verificar requisitos del siguiente cargo
    fallos = []
    if estado.get("reputacion", 0) < reqs_siguiente["req_reputacion"]:
        fallos.append(f"Reputación {reqs_siguiente['req_reputacion']} (tenés {estado.get('reputacion', 0)})")
    if estado.get("habilidad_tecnica", 0) < reqs_siguiente["req_tecnica"]:
        fallos.append(f"Técnica {reqs_siguiente['req_tecnica']} (tenés {estado.get('habilidad_tecnica', 0)})")
    if estado.get("habilidad_politica", 0) < reqs_siguiente["req_politica"]:
        fallos.append(f"Política {reqs_siguiente['req_politica']} (tenés {estado.get('habilidad_politica', 0)})")
    if estado.get("habilidad_negocios", 0) < reqs_siguiente["req_negocios"]:
        fallos.append(f"Negocios {reqs_siguiente['req_negocios']} (tenés {estado.get('habilidad_negocios', 0)})")
    
    if fallos:
        return False, f"❌ **Aún no cumplís los requisitos para {trabajo_siguiente}:**\n" + "\n".join(f"  • {f}" for f in fallos)
    
    # Calcular probabilidad de ascenso
    exceso_reputacion = estado.get("reputacion", 0) - reqs_siguiente["req_reputacion"]
    exceso_habilidad = 0
    if reqs_siguiente["req_tecnica"] > 0:
        exceso_habilidad += estado.get("habilidad_tecnica", 0) - reqs_siguiente["req_tecnica"]
    if reqs_siguiente["req_politica"] > 0:
        exceso_habilidad += estado.get("habilidad_politica", 0) - reqs_siguiente["req_politica"]
    if reqs_siguiente["req_negocios"] > 0:
        exceso_habilidad += estado.get("habilidad_negocios", 0) - reqs_siguiente["req_negocios"]
    
    bonus_experiencia = min(20, (turnos_en_trabajo - 6) * 2)
    
    prob_exito = 40 + exceso_reputacion * 2 + exceso_habilidad + bonus_experiencia + random.randint(-15, 15)
    prob_exito = max(10, min(90, prob_exito))
    
    tirada = random.randint(1, 100)
    
    if tirada <= prob_exito:
        estado["trabajo_actual"] = trabajo_siguiente
        estado["turnos_en_trabajo"] = 0
        sueldo = SALARIOS_BASE.get(trabajo_siguiente, 0)
        return True, f"🎉 **¡ASCENDIDO!** Te promovieron a **{trabajo_siguiente}**. Tu nuevo sueldo es ${sueldo:,}/mes. ¡El esfuerzo dio sus frutos!"
    else:
        return False, f"😔 **Ascenso denegado.** La dirección decidió que aún no es momento. Seguí demostrando tu valía en {trabajo_actual}."

def intentar_renunciar(estado: Dict[str, Any]) -> Tuple[bool, str]:
    """El jugador renuncia a su trabajo actual."""
    trabajo_actual = estado.get("trabajo_actual", "Desempleado")
    
    if trabajo_actual == "Desempleado":
        return False, "Ya estás desempleado. No podés renunciar a algo que no tenés."
    
    estado["trabajo_actual"] = "Desempleado"
    estado["turnos_en_trabajo"] = 0
    estado["ingreso_mensual"] = 0
    
    return True, f"📤 **Renunciaste** a tu puesto de {trabajo_actual}. Ahora estás desempleado, pero libre para buscar nuevas oportunidades."

def verificar_despido(estado: Dict[str, Any]) -> Optional[str]:
    """Verifica si el jugador es despedido por bajo rendimiento o escándalo."""
    trabajo_actual = estado.get("trabajo_actual", "Desempleado")
    if trabajo_actual == "Desempleado":
        return None
    
    if estado.get("nivel_escandalo", 0) > 70 and random.random() < 0.20:
        estado["trabajo_actual"] = "Desempleado"
        estado["turnos_en_trabajo"] = 0
        estado["ingreso_mensual"] = 0
        return "🚨 **¡TE DESPIDIERON!** Tu nivel de escándalo era demasiado alto para la empresa. Ahora estás desempleado."
    
    return None

# ==============================================================================
# LÓGICA DE ECONOMÍA Y TURNO (PASIVO)
# ==============================================================================

def procesar_economia(estado: Dict[str, Any]) -> str:
    """Calcula ingresos, gastos, dividendos e inflación al pasar el tiempo."""
    resumen = []
    
    nivel_vida = estado.get("nivel_calidad_vida", 1)
    costo_vida = COSTO_VIDA_POR_NIVEL.get(nivel_vida, 15000)
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
    
    if trabajo != "Desempleado":
        estado["turnos_en_trabajo"] = estado.get("turnos_en_trabajo", 0) + 1
        
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
    
    msg_despido = verificar_despido(estado)
    if msg_despido:
        resumen.append(f"\n⚠️ {msg_despido}")
    
    estado.setdefault("historial_patrimonio", []).append(estado.get("dinero_personal", 0))
    estado.setdefault("historial_aprobacion", []).append(estado.get("aprobacion_publica", 50))
    
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
        
    costo_mejora = COSTO_VIDA_POR_NIVEL.get(nivel_actual + 1, 25000) * 10
    
    if estado.get("dinero_personal", 0) < costo_mejora:
        return False, f"💸 Mudarse cuesta ${costo_mejora:,}. No tenés suficiente."
        
    estado["dinero_personal"] -= costo_mejora
    estado["nivel_calidad_vida"] = nivel_actual + 1
    
    return True, f"🏠 **MEJORA:** Ahora vivís en un lugar mejor (Nivel {nivel_actual + 1}). Tus gastos fijos suben."

# ==============================================================================
# POLÍTICA, CAMPAÑAS Y ELECCIONES
# ==============================================================================

def calcular_exito_campana(estado: Dict[str, Any], cargo_objetivo: str) -> Tuple[bool, str]:
    """Calcula el porcentaje de votos basado en Habilidad Política, Facciones y Aprobación."""
    score = (estado.get("aprobacion_publica", 50) * 0.6) + (estado.get("reputacion", 50) * 0.4)
    habilidad_pol = estado.get("habilidad_politica", 20)
    score += habilidad_pol * 0.5
    
    facciones = estado.get("facciones", {})
    if facciones:
        promedio_facciones = sum(facciones.values()) / len(facciones)
        score += (promedio_facciones - 50) * 0.3
    
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
    
    if tipo == "publicidad":
        estado["aprobacion_publica"] = min(100, estado.get("aprobacion_publica", 50) + 3)
        return True, "📺 Invertiste en publicidad. +3 Aprobación Pública."
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
# TENSIÓN DINÁMICA DE FACCIONES
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
# RIVALES ACTIVOS
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
                            if stat in ["reputacion", "aprobacion_publica"]:
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
# EVENTOS ALEATORIOS SORPRESIVOS
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
                    if stat in ["reputacion", "aprobacion_publica"]:
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
# SISTEMA DE LOGROS (ACTUALIZADO CON NUEVOS CARGOS)
# ==============================================================================

LOGROS_DEFINICIONES = [
    {"id": "primer_millon", "nombre": "Magnate", "desc": "Acumular $1,000,000", "check": lambda e: e.get("dinero_personal", 0) >= 1000000},
    {"id": "presidente_joven", "nombre": "Joven Promesa", "desc": "Ser Presidente antes de los 45", "check": lambda e: e.get("cargo_politico") == "Presidente" and e.get("edad", 100) < 45},
    {"id": "empresa_nivel_3", "nombre": "Empresario", "desc": "Tener una empresa en Nivel 3", "check": lambda e: any(emp.nivel >= 3 for emp in e.get("corporaciones", {}).values() if hasattr(emp, 'nivel'))},
    {"id": "aprobacion_alta", "nombre": "Amado por el Pueblo", "desc": "Alcanzar 90% de Aprobación", "check": lambda e: e.get("aprobacion_publica", 0) >= 90},
    {"id": "sobreviviente", "nombre": "Sobreviviente", "desc": "Sobrevivir a un Juicio Político", "check": lambda e: e.get("juicio_politico_sobrevivido", False)},
    {"id": "dinastia_larga", "nombre": "Legado Eterno", "desc": "Llegar a la Generación 3", "check": lambda e: e.get("generacion_actual", 1) >= 3},
    {"id": "cto", "nombre": "Genio Técnico", "desc": "Alcanzar el puesto de CTO", "check": lambda e: e.get("trabajo_actual") == "CTO"},
    {"id": "ceo", "nombre": "Titán Corporativo", "desc": "Alcanzar el puesto de CEO", "check": lambda e: e.get("trabajo_actual") == "CEO"}
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
# SISTEMA DE OBJETIVOS DINÁSTICOS CON RECOMPENSAS
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
# ROUTER DE ACCIONES DETERMINISTAS (FIX: Acepta ofertas de la IA y Ascensos lógicos)
# ==============================================================================

def ejecutar_accion_determinista(estado: Dict[str, Any], texto: str) -> Tuple[bool, str]:
    """Analiza el texto del jugador. Si es una acción mecánica conocida, la ejecuta directamente."""
    t = texto.lower().strip()
    
    logger.info(f"Procesando acción: '{t}'")
    
    # 1. ACCIONES LABORALES
    if "renunciar" in t or "dejar trabajo" in t or "dejar el trabajo" in t:
        return intentar_renunciar(estado)

    if "pedir ascenso" in t or "ascender" in t or "promoción" in t or "promocion" in t:
        return intentar_pedir_ascenso(estado)

    # FIX: Detecta "aceptar oferta de senior developer" o "postularme a cto"
    if "aceptar" in t or "oferta" in t or "buscar trabajo" in t or "conseguir trabajo" in t or "postular" in t or "aplicar" in t:
        for cargo in REQUISITOS_TRABAJO.keys():
            if cargo.lower() in t:
                return postularse_a_trabajo(estado, cargo)
        # Si dijo "buscar trabajo" a secas
        if "buscar" in t or "trabajo" in t or "empleo" in t:
            return intentar_buscar_trabajo(estado, None)

    # 2. Detectar fundación de empresas
    if "fundar" in t or "crear" in t or "abrir" in t:
        tipo = None
        
        if "consultora" in t:
            tipo = "Consultora"
        elif "tech" in t or "startup" in t or "tecnología" in t or "tecnologia" in t:
            tipo = "Tech Startup"
        elif "inmobiliaria" in t or "casa" in t or "inmueble" in t:
            tipo = "Inmobiliaria"
        elif "banco" in t or "financiera" in t or "banca" in t:
            tipo = "Banco"
        elif "empresa" in t or "negocio" in t or "compañía" in t or "compania" in t:
            tipo = "Consultora"  # Default
            
        if tipo:
            logger.info(f"Intentando fundar empresa tipo: {tipo}")
            ok, msg = intentar_fundar_empresa(estado, tipo)
            return ok, msg

    # 3. Detectar estudiar
    if "estudiar" in t or "capacitarse" in t or "aprender" in t or "curso" in t:
        enfoque = "tecnica"
        if "politica" in t or "oratoria" in t or "política" in t: 
            enfoque = "politica"
        elif "negocio" in t or "finanza" in t or "economia" in t or "economía" in t: 
            enfoque = "negocios"
        
        ok, msg = intentar_estudiar(estado, enfoque)
        return ok, msg

    # 4. Detectar mejorar vivienda
    if "mudar" in t or "mejorar vivienda" in t or "comprar casa" in t or "mudarse" in t:
        ok, msg = intentar_mejorar_vivienda(estado)
        return ok, msg

    # 5. Detectar interacción con prensa
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
            
    # Solo aplicamos efectos a las stats que REALMENTE existen y importan
    stats_validas = ["reputacion", "aprobacion_publica", "nivel_escandalo", "dinero_personal"]
    
    for stat, valor in efectos_ia.items():
        if stat in stats_validas and stat in estado and isinstance(valor, (int, float)):
            if stat == "dinero_personal":
                estado[stat] += valor
            else:
                estado[stat] = max(0, min(100, estado[stat] + valor))
                
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
            
        if estado.get("edad", 24) >= 85:
            game_over = "💀 **FIN DE UNA ERA:** Has fallecido. Es hora de que tu heredero tome el mando."

    return estado, narrativa, game_over