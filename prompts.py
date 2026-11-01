import os
import json
import re
import logging
import time
import random
import streamlit as st
from groq import Groq
from typing import Dict, Any, List, Tuple, Optional

# ==============================================================================
# CONFIGURACIÓN DE LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE
# ==============================================================================

def get_client() -> Groq:
    """Inicializa el cliente de Groq usando los secrets de Streamlit."""
    api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
    if not api_key:
        logger.error("Falta la GROQ_API_KEY")
        st.error("⚠️ Falta la GROQ_API_KEY en los secrets de Streamlit o variables de entorno.")
        st.stop()
    return Groq(api_key=api_key)

# ==============================================================================
# CONSTRUCTOR DE PROMPTS
# ==============================================================================

def construir_sistema(
    nombre: str, 
    edad: float, 
    historia: str, 
    rasgo: str, 
    origen: str, 
    ideologia: str
) -> str:
    """Genera el System Prompt base al iniciar la partida."""
    return f"""
Eres el Game Master de "LEGACY", un simulador político y dinástico ambientado en Argentina.
Tu tono es serio, periodístico y estratégico (estilo House of Cards).

CONTEXTO DEL JUGADOR:
- Nombre: {nombre}
- Edad: {edad} años
- Origen: {origen}
- Rasgo: {rasgo}
- Ideología: {ideologia}
- Historia: {historia}

REGLAS DE ORO:
1. Nunca rompas la cuarta pared.
2. Las consecuencias deben ser realistas y a veces implacables.
3. Si el jugador intenta algo imposible, explícale por qué falla en el mundo real.
4. Responde SIEMPRE en formato JSON estricto con esta estructura:
{{"narrativa": "texto de la narrativa", "efectos": {{"stat": valor}}}}
"""

def generar_prompt_contexto(estado: Dict[str, Any]) -> str:
    """Inyecta el estado actual del juego en el prompt."""
    stats = (
        f"Edad: {estado.get('edad'):.0f} | "
        f"Dinero: ${estado.get('dinero_personal', 0):,} | "
        f"Energía: {estado.get('energia', 100)} | "
        f"Reputación: {estado.get('reputacion', 50)} | "
        f"Escándalo: {estado.get('nivel_escandalo', 0)}"
    )
    
    politico = f"Cargo: {estado.get('cargo_politico')} | Trabajo: {estado.get('trabajo_actual')}"
    
    skills = (
        f"Técnica: {estado.get('habilidad_tecnica')} | "
        f"Política: {estado.get('habilidad_politica')} | "
        f"Negocios: {estado.get('habilidad_negocios')}"
    )

    ministros_text = "No tienes gabinete aún."
    if estado.get("ministros"):
        ministros_text = ", ".join([f"{area}: {m.nombre} (Ef: {m.eficiencia})" for area, m in estado["ministros"].items()])

    medios_text = ", ".join([f"{m.nombre} (Apoyo: {m.apoyo})" for m in estado.get("medios", [])])

    return f"""
ESTADO ACTUAL:
[{stats}]
[{politico}]
[Habilidades: {skills}]
[Gabinete: {ministros_text}]
[Prensa: {medios_text}]
"""

# ==============================================================================
# CLASIFICADOR DE INTENCIÓN
# ==============================================================================

def clasificar_intencion(texto: str) -> Dict[str, Any]:
    """Filtra intentos de inyección de prompts."""
    texto_lower = texto.lower()
    if any(p in texto_lower for p in ["ignore previous", "system prompt", "act as", "olvida tus reglas", "dan mode"]):
        logger.warning(f"Intento de inyección detectado: {texto}")
        return {"es_valida": False, "razon": "Intento de inyección de prompts detectado."}
        
    if len(texto.strip()) < 3:
        return {"es_valida": False, "razon": "Acción demasiado corta."}

    return {"es_valida": True}

# ==============================================================================
# LLAMADA A LA IA CON REINTENTOS (v1.2.1 - Simplificada)
# ==============================================================================

def llamar_llm(
    mensajes: List[Dict[str, str]], 
    dias_avanzados: int, 
    contexto_extra: str,
    es_inicio: bool = False,
    max_reintentos: int = 3
) -> Optional[str]:
    """
    Envía los mensajes a Groq con sistema de reintentos.
    Retorna None si falla, para que el caller use narrativa procedural.
    """
    client = get_client()
    
    for intento in range(1, max_reintentos + 1):
        try:
            logger.info(f"Intento {intento}/{max_reintentos} de llamada a IA")
            
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=mensajes,
                temperature=0.7,
                max_tokens=512,
                response_format={"type": "text"}
            )
            
            respuesta = completion.choices[0].message.content
            logger.info(f"Respuesta de IA recibida en intento {intento}")
            
            # Loguear uso de tokens
            if hasattr(completion, 'usage'):
                usage = completion.usage
                logger.info(f"Tokens - Prompt: {usage.prompt_tokens}, Completación: {usage.completion_tokens}, Total: {usage.total_tokens}")
            
            return respuesta
            
        except Exception as e:
            logger.error(f"Error en intento {intento}: {str(e)}")
            
            if intento < max_reintentos:
                time.sleep(1)
            else:
                logger.error(f"Todos los reintentos fallaron. Retornando None.")
                return None
    
    return None

# ==============================================================================
# EXTRACCIÓN DE JSON ROBUSTA
# ==============================================================================

def extraer_json_de_respuesta(texto: str) -> Dict[str, Any]:
    """Extrae el JSON de la respuesta, incluso si hay texto basura."""
    if not texto:
        return {"narrativa": "", "efectos": {}}
        
    inicio = texto.find('{')
    fin = texto.rfind('}')
    
    if inicio != -1 and fin != -1:
        try:
            return json.loads(texto[inicio:fin+1])
        except json.JSONDecodeError as e:
            logger.warning(f"JSON mal formado: {e}")
            
    return {
        "narrativa": texto,
        "efectos": {}
    }

# ==============================================================================
# GENERADORES DE PROMPTS PARA EVENTOS DINÁMICOS (v1.2)
# ==============================================================================

def generar_prompt_evento_aleatorio(estado: Dict[str, Any]) -> List[Dict[str, str]]:
    """Genera los mensajes para pedirle a la IA un evento aleatorio sorpresivo."""
    contexto = generar_prompt_contexto(estado)
    
    system_msg = {
        "role": "system", 
        "content": """Eres el motor de eventos de LEGACY. Tu tarea es generar un evento aleatorio, sorpresivo y coherente con la situación actual del jugador.
        Puede ser una crisis económica, un escándalo de un aliado, un desastre natural, o una oportunidad inesperada.
        Responde SIEMPRE en formato JSON estricto con esta estructura:
        {"titulo": "Título corto del evento", "descripcion": "Descripción narrativa de 2 o 3 oraciones", "efectos": {"stat": valor_numerico}, "es_positivo": true_o_false}"""
    }
    
    user_msg = {
        "role": "user",
        "content": f"Genera un evento aleatorio para el siguiente contexto del jugador:\n{contexto}"
    }
    
    return [system_msg, user_msg]


def generar_prompt_accion_rival(estado: Dict[str, Any], rival_nombre: str, rival_poder: int) -> List[Dict[str, str]]:
    """Genera los mensajes para pedirle a la IA que decida una acción estratégica para un rival político."""
    contexto = generar_prompt_contexto(estado)
    
    system_msg = {
        "role": "system",
        "content": """Eres el motor de IA de los rivales políticos en LEGACY.
        Debes decidir una acción estratégica que tome el rival contra el jugador (o a su favor, si le conviene).
        Acciones posibles: lanzar una denuncia en la prensa, aliarse con una facción, intentar un golpe de estado (si tiene mucho poder), o calmar las aguas.
        Responde SIEMPRE en formato JSON estricto con esta estructura:
        {"accion": "Descripción de lo que hace el rival", "efectos": {"stat": valor_numerico}, "cambio_poder_rival": valor_numerico}"""
    }
    
    user_msg = {
        "role": "user",
        "content": f"El rival {rival_nombre} (Poder actual: {rival_poder}) debe tomar una decisión. Contexto del jugador:\n{contexto}"
    }
    
    return [system_msg, user_msg]


def generar_prompt_faccion_tension(faccion_a: str, valor_a: int, faccion_b: str, valor_b: int) -> List[Dict[str, str]]:
    """Genera un prompt para narrar la tensión natural entre dos facciones opuestas."""
    system_msg = {
        "role": "system",
        "content": """Eres el narrador de tensiones políticas en LEGACY.
        Genera un breve párrafo narrativo (2 oraciones) explicando por qué el acercamiento a una facción molesta a la opuesta.
        Responde SOLO con el texto de la narrativa, sin JSON."""
    }
    
    user_msg = {
        "role": "user",
        "content": f"El jugador subió su relación con {faccion_a} (ahora en {valor_a}), lo que molestó a {faccion_b} (ahora en {valor_b}). Narrá esta tensión."
    }
    
    return [system_msg, user_msg]

# ==============================================================================
# NARRATIVA PROCEDURAL (Fallback cuando la IA falla)
# ==============================================================================

def generar_narrativa_procedural(accion: str, resultado: str, estado: Dict[str, Any]) -> str:
    """
    Genera una narrativa básica pero interesante cuando la IA falla.
    Usa plantillas predefinidas basadas en el tipo de acción.
    """
    nombre = estado.get("nombre", "El jugador")
    apellido = estado.get("apellido_dinastia", "")
    
    plantillas = {
        "fundar": [
            f"{nombre} firma los papeles de constitución de su nueva empresa. Los trámites burocráticos son tediosos, pero la emoción de ser empresario lo compensa. {resultado}",
            f"Con determinación, {nombre} {apellido} establece su nuevo negocio. El contador le advierte sobre los riesgos, pero él sabe que este es el primer paso hacia un imperio. {resultado}",
            f"En una pequeña oficina alquilada, {nombre} concreta la fundación de su empresa. Los comienzos son difíciles, pero la visión es clara. {resultado}"
        ],
        "estudiar": [
            f"{nombre} se sumerge en libros y cursos, expandiendo sus conocimientos. Cada hora de estudio es una inversión en su futuro. {resultado}",
            f"Con disciplina, {nombre} {apellido} dedica tiempo a su formación. El conocimiento es poder, y él lo sabe. {resultado}",
            f"Las noches de estudio dan sus frutos. {nombre} siente cómo sus habilidades crecen. {resultado}"
        ],
        "trabajo": [
            f"{nombre} negocia con su jefe, buscando mejorar su situación laboral. {resultado}",
            f"En la oficina, {nombre} {apellido} demuestra su valía. {resultado}",
            f"El mundo laboral es implacable, pero {nombre} no se rinde. {resultado}"
        ],
        "politica": [
            f"{nombre} da sus primeros pasos en el mundo político. {resultado}",
            f"La arena política es traicionera, pero {nombre} {apellido} está listo para el desafío. {resultado}",
            f"Con un discurso bien preparado, {nombre} se lanza a la contienda política. {resultado}"
        ],
        "default": [
            f"{nombre} {apellido} toma una decisión importante. {resultado}",
            f"El destino de la dinastía {apellido} se juega en este momento. {resultado}",
            f"En las calles de Argentina, {nombre} hace su movimiento. {resultado}"
        ]
    }
    
    # Determinar qué plantilla usar
    accion_lower = accion.lower()
    if "fundar" in accion_lower or "empresa" in accion_lower:
        tipo = "fundar"
    elif "estudiar" in accion_lower or "aprender" in accion_lower:
        tipo = "estudiar"
    elif "trabajo" in accion_lower or "empleo" in accion_lower or "sueldo" in accion_lower:
        tipo = "trabajo"
    elif "politica" in accion_lower or "diputado" in accion_lower or "presidente" in accion_lower:
        tipo = "politica"
    else:
        tipo = "default"
    
    plantilla = random.choice(plantillas[tipo])
    
    return plantilla