import os
import json
import re
import streamlit as st
from groq import Groq
from typing import Dict, Any, List, Tuple

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE
# ==============================================================================

def get_client():
    """Inicializa el cliente de Groq usando los secrets de Streamlit."""
    api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
    if not api_key:
        st.error("⚠️ Falta la GROQ_API_KEY en los secrets de Streamlit o variables de entorno.")
        st.stop()
    return Groq(api_key=api_key)

# ==============================================================================
# CONSTRUCTOR DE PROMPTS (Contexto Dinámico)
# ==============================================================================

def construir_sistema(
    nombre: str, 
    edad: float, 
    historia: str, 
    rasgo: str, 
    origen: str, 
    ideologia: str
) -> str:
    """
    Genera el System Prompt base al iniciar la partida.
    """
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
4. Responde SIEMPRE en formato JSON estricto.
"""

def generar_prompt_contexto(estado: Dict[str, Any]) -> str:
    """
    Inyecta el estado actual del juego en el prompt para que la IA sepa qué está pasando.
    """
    # Resumen de stats clave
    stats = (
        f"Edad: {estado.get('edad'):.0f} | "
        f"Dinero: ${estado.get('dinero_personal', 0):,} | "
        f"Energía: {estado.get('energia', 100)} | "
        f"Salud: {estado.get('salud_fisica', 100)} | "
        f"Reputación: {estado.get('reputacion', 50)} | "
        f"Escándalo: {estado.get('nivel_escandalo', 0)}"
    )
    
    # Contexto Político y Laboral
    politico = f"Cargo: {estado.get('cargo_politico')} | Trabajo: {estado.get('trabajo_actual')}"
    
    # Habilidades
    skills = (
        f"Técnica: {estado.get('habilidad_tecnica')} | "
        f"Política: {estado.get('habilidad_politica')} | "
        f"Negocios: {estado.get('habilidad_negocios')}"
    )

    # Ministros (Solo si es Presidente/Gobernador)
    ministros_text = "No tienes gabinete aún."
    if estado.get("ministros"):
        ministros_text = ", ".join([f"{area}: {m.nombre} (Ef: {m.eficiencia}, Leal: {m.lealtad})" for area, m in estado["ministros"].items()])

    # Medios de Prensa
    medios_text = ", ".join([f"{m.nombre} (Apoyo: {m.apoyo})" for m in estado.get("medios", [])])

    return f"""
ESTADO ACTUAL:
[{stats}]
[{politico}]
[Habilidades: {skills}]
[Gabinete: {ministros_text}]
[Prensa: {medios_text}]

RECUERDA: El jugador puede interactuar con sus ministros, la prensa o proponer leyes si tiene el cargo adecuado.
"""

# ==============================================================================
# CLASIFICADOR DE INTENCIÓN (Filtro de seguridad y ruteo)
# ==============================================================================

def clasificar_intencion(texto: str) -> Dict[str, Any]:
    """
    Usa un modelo pequeño y rápido para decidir si la acción es válida 
    o si es un intento de inyección de prompts.
    """
    # Filtro rápido por palabras clave (Regex)
    texto_lower = texto.lower()
    if any(p in texto_lower for p in ["ignore previous", "system prompt", "act as", "olvida tus reglas", "dan mode"]):
        return {"es_valida": False, "razon": "Intento de inyección de prompts detectado."}
        
    if len(texto.strip()) < 3:
        return {"es_valida": False, "razon": "Acción demasiado corta."}

    # Si pasa el filtro básico, es válida para el router
    return {"es_valida": True}

# ==============================================================================
# LLAMADA A LA IA (LLM)
# ==============================================================================

def llamar_llm(
    mensajes: List[Dict[str, str]], 
    dias_avanzados: int, 
    contexto_extra: str,
    es_inicio: bool = False
) -> str:
    """
    Envía los mensajes a Groq y retorna la respuesta cruda.
    """
    client = get_client()
    
    # Construir el System Prompt dinámico
    # Nota: En la v1.1, el system prompt se inyecta en el primer mensaje del historial
    system_prompt = mensajes[0]["content"] if mensajes else ""
    
    if not es_inicio:
        # Inyectar contexto fresco en cada turno
        # Asumimos que el estado se pasa en el último mensaje de usuario o sistema
        # Para simplificar, lo agregamos como un mensaje de sistema intermedio
        pass 

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192", # Modelo potente para narrativa compleja
            messages=mensajes,
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"} # Forzamos JSON
        )
        return completion.choices[0].message.content
    except Exception as e:
        return json.dumps({
            "narrativa": f"Error de conexión con el Game Master: {str(e)}",
            "efectos": {}
        })

# ==============================================================================
# EXTRACCIÓN DE JSON (Robustez)
# ==============================================================================

def extraer_json_de_respuesta(texto: str) -> Dict[str, Any]:
    """
    Extrae el JSON de la respuesta de la IA, incluso si hay texto basura alrededor.
    """
    # Buscar el primer '{' y el último '}'
    inicio = texto.find('{')
    fin = texto.rfind('}')
    
    if inicio != -1 and fin != -1:
        try:
            return json.loads(texto[inicio:fin+1])
        except json.JSONDecodeError:
            pass
            
    # Si falla, retornar estructura por defecto
    return {
        "narrativa": texto,
        "efectos": {}
    }