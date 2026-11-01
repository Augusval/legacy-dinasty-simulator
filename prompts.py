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
# LOGGING
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
# CLIENTE GROQ
# ==============================================================================

def get_client() -> Groq:
    api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
    if not api_key:
        logger.error("Falta la GROQ_API_KEY")
        st.error("⚠️ Falta la GROQ_API_KEY en los secrets de Streamlit o variables de entorno.")
        st.stop()
    return Groq(api_key=api_key)

# ==============================================================================
# PROMPTS BASE
# ==============================================================================

def construir_sistema(nombre: str, edad: float, historia: str, rasgo: str, origen: str, ideologia: str) -> str:
    return f"""Eres el Game Master de "LEGACY", un simulador político y dinástico ambientado en Argentina.
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
{{"narrativa": "texto de la narrativa", "efectos": {{"stat": valor}}}}"""

def generar_prompt_contexto(estado: Dict[str, Any]) -> str:
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
    texto_lower = texto.lower()
    if any(p in texto_lower for p in ["ignore previous", "system prompt", "act as", "olvida tus reglas", "dan mode"]):
        logger.warning(f"Intento de inyección detectado: {texto}")
        return {"es_valida": False, "razon": "Intento de inyección de prompts detectado."}
        
    if len(texto.strip()) < 3:
        return {"es_valida": False, "razon": "Acción demasiado corta."}

    return {"es_valida": True}

# ==============================================================================
# LLAMADA A IA CON FALLBACK PROCEDURAL (El fix para que nunca falle feo)
# ==============================================================================

def llamar_llm(mensajes: List[Dict[str, str]], dias_avanzados: int, contexto_extra: str, es_inicio: bool = False, max_reintentos: int = 3) -> str:
    """
    Llama a Groq. Si falla después de 3 intentos, retorna una narrativa procedural 
    en formato JSON (NUNCA retorna un mensaje de error feo).
    """
    client = get_client()
    
    for intento in range(1, max_reintentos + 1):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=mensajes,
                temperature=0.7,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error IA intento {intento}: {e}")
            if intento < max_reintentos:
                time.sleep(2)
    
    # FALLBACK: Si todo falló, generar narrativa procedural
    logger.warning("IA falló completamente. Usando narrativa procedural.")
    return _generar_fallback_procedural(mensajes)

def _generar_fallback_procedural(mensajes: List[Dict[str, str]]) -> str:
    """Genera un JSON válido con narrativa procedural cuando la IA falla."""
    accion_usuario = ""
    for msg in reversed(mensajes):
        if msg.get("role") == "user":
            accion_usuario = msg.get("content", "")
            break
    
    plantillas = {
        "empresa": [
            "Los trámites burocráticos avanzan entre papeles y firmas. El mundo de los negocios no perdona la indecisión, pero vos ya tomaste tu decisión.",
            "En una oficina modesta se gesta algo grande. Los números empiezan a tomar forma, y con ellos, el futuro de tu dinastía.",
            "El contador revisa los números con ceño fruncido, pero vos sabés que esta es la jugada correcta. El tiempo lo confirmará."
        ],
        "estudiar": [
            "Las horas de estudio rinden frutos silenciosos. Cada libro leído es un arma más en tu arsenal político.",
            "La disciplina da sus frutos. Te sentís más preparado, más afilado, más peligroso para tus rivales.",
            "Entre apuntes y noches de lectura, tu mente se expande. El conocimiento es el verdadero poder."
        ],
        "politica": [
            "La arena política huele a traición y oportunidad. Das un paso al frente, sabiendo que no hay vuelta atrás.",
            "Los pasillos del poder se abren lentamente. Cada mano que estrechas es un favor que algún día cobrarás.",
            "El discurso está preparado. La multitud espera. Es momento de demostrar por qué merecés estar ahí."
        ],
        "default": [
            "El tiempo pasa implacable. Cada decisión, cada silencio, construye o destruye tu legado.",
            "En las sombras del poder, algo se gesta. No todo depende de vos, pero todo te afecta.",
            "La ciudad sigue su ritmo frenético. Vos, en el centro de todo, calculás tu próximo movimiento."
        ]
    }
    
    accion_lower = accion_usuario.lower()
    if "empresa" in accion_lower or "fundar" in accion_lower:
        tipo = "empresa"
    elif "estudiar" in accion_lower or "aprender" in accion_lower:
        tipo = "estudiar"
    elif "politica" in accion_lower or "diputado" in accion_lower or "presidente" in accion_lower:
        tipo = "politica"
    else:
        tipo = "default"
    
    narrativa = random.choice(plantillas[tipo])
    return json.dumps({"narrativa": narrativa, "efectos": {}}, ensure_ascii=False)

# ==============================================================================
# EXTRACCIÓN JSON
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
            
    return {"narrativa": texto, "efectos": {}}

# ==============================================================================
# PROMPTS PARA EVENTOS Y RIVALES
# ==============================================================================

def generar_prompt_evento_aleatorio(estado: Dict[str, Any]) -> List[Dict[str, str]]:
    """Genera los mensajes para pedirle a la IA un evento aleatorio sorpresivo."""
    contexto = generar_prompt_contexto(estado)
    return [
        {"role": "system", "content": "Genera un evento aleatorio para LEGACY. Responde en JSON estricto: {\"titulo\": \"...\", \"descripcion\": \"...\", \"efectos\": {\"stat\": valor}, \"es_positivo\": true/false}"},
        {"role": "user", "content": f"Contexto del jugador:\n{contexto}"}
    ]

def generar_prompt_accion_rival(estado: Dict[str, Any], rival_nombre: str, rival_poder: int) -> List[Dict[str, str]]:
    """Genera los mensajes para pedirle a la IA que decida una acción estratégica para un rival político."""
    contexto = generar_prompt_contexto(estado)
    return [
        {"role": "system", "content": "Decidí una acción para el rival político. Responde en JSON estricto: {\"accion\": \"...\", \"efectos\": {\"stat\": valor}, \"cambio_poder_rival\": valor}"},
        {"role": "user", "content": f"Rival: {rival_nombre} (Poder: {rival_poder}). Contexto del jugador:\n{contexto}"}
    ]

def generar_prompt_faccion_tension(faccion_a: str, valor_a: int, faccion_b: str, valor_b: int) -> List[Dict[str, str]]:
    """Genera un prompt para narrar la tensión natural entre dos facciones opuestas."""
    return [
        {"role": "system", "content": "Narrá en 2 oraciones la tensión entre facciones. Solo texto narrativo, sin JSON."},
        {"role": "user", "content": f"El jugador subió con {faccion_a} ({valor_a}), molestando a {faccion_b} ({valor_b})."}
    ]