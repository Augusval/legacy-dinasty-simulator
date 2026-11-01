# 🏛️ LEGACY: Crónicas Dinásticas

Un simulador político y de gestión dinástica impulsado por IA (LLM), construido con Python y Streamlit. Inspirado en la profundidad de *Crusader Kings* y la narrativa de *House of Cards*.

## 🚀 Características Principales
- **Game Master con IA**: Narrativa dinámica y coherente generada por LLM (Groq/OpenAI) que reacciona a las decisiones del jugador, respetando el contexto histórico y las facciones.
- **Sistema de Estado Robusto**: Validación de datos y tipado estricto con `Pydantic` para prevenir inconsistencias y bugs silenciosos.
- **Mecánicas de Juego Profundas**: Gestión de facciones (Militares, Sindicatos, Iglesia, Empresarios), economía, salud, escándalos, mini-juegos de crisis y sucesión generacional.
- **Arquitectura Modular**: Separación estricta de responsabilidades. La lógica de negocio (`mechanics.py`) actúa como una función pura, desacoplada de la UI (`app.py`, `ui.py`), facilitando el testing y el mantenimiento.
- **Persistencia y Legado**: Sistema de guardado en slots y un "Salón de la Fama" que persiste los mejores legados dinásticos entre partidas.

## 🛠️ Stack Tecnológico
- **Backend/Lógica**: Python 3.10+
- **Frontend/UI**: Streamlit, Plotly (visualización de datos), CSS personalizado
- **IA/LLM**: Groq API (Llama 3 / GPT-oss) con parsing robusto de JSON y protección contra Prompt Injection.
- **Validación**: Pydantic para esquemas de estado.

## 🎮 Cómo Jugar
1. Cloná el repositorio: `git clone https://github.com/tu-usuario/legacy.git`
2. Instalá las dependencias: `pip install -r requirements.txt`
3. Configurá tu API key en `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "tu_api_key_aqui"

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://legacy-dinasty-simulator.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **🎮 [JUGAR DEMO EN VIVO AQUÍ](https://legacy-dinasty-simulator.streamlit.app)** *(Sin instalar nada, corre directo en tu navegador)*

Un simulador político y de gestión dinástica impulsado por IA, construido con Python y Streamlit. Inspirado en la profundidad estratégica de *Crusader Kings* y la narrativa de *House of Cards*.
