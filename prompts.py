import os
import json
import re
import logging
import time
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
# LLAMADA A LA IA CON REINTENTOS
# ==============================================================================

def llamar_llm(
    mensajes: List[Dict[str, str]], 
    dias_avanzados: int, 
    contexto_extra: str,
    es_inicio: bool = False,
    max_reintentos: int = 3
) -> str:
    """
    Envía los mensajes a Groq con sistema de reintentos automático.
    Si falla 3 veces, retorna un fallback genérico.
    """
    client = get_client()
    
    for intento in range(1, max_reintentos + 1):
        try:
            logger.info(f"Intento {intento}/{max_reintentos} de llamada a IA")
            
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=mensajes,
                temperature=0.7,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            respuesta = completion.choices[0].message.content
            logger.info(f"Respuesta de IA recibida en intento {intento}")
            return respuesta
            
        except Exception as e:
            logger.error(f"Error en intento {intento}: {str(e)}")
            
            if intento < max_reintentos:
                logger.info(f"Reintentando en 2 segundos...")
                time.sleep(2)
            else:
                logger.error(f"Todos los reintentos fallaron. Usando fallback.")
                return json.dumps({
                    "narrativa": "El Game Master está experimentando dificultades técnicas. La situación permanece sin cambios por ahora.",
                    "efectos": {}
                })
    
    return json.dumps({"narrativa": "Error desconocido.", "efectos": {}})

# ==============================================================================
# EXTRACCIÓN DE JSON ROBUSTA
# ==============================================================================

def extraer_json_de_respuesta(texto: str) -> Dict[str, Any]:
    """Extrae el JSON de la respuesta, incluso si hay texto basura."""
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
    """
    Genera los mensajes para pedirle a la IA un evento aleatorio sorpresivo
    basado en el contexto actual del jugador.
    """
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
    """
    Genera los mensajes para pedirle a la IA que decida una acción estratégica para un rival político.
    """
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
    """
    Genera un prompt para narrar la tensión natural entre dos facciones opuestas.
    """
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