# 🏛️ LEGACY: Political Dynasty Simulator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://legacy-dinasty-simulator.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-33%20passed-brightgreen)](https://github.com/Augusval/legacy-dinasty-simulator)

> **🎮 [JUGAR VERSIÓN 1.0 EN VIVO](https://legacy-dinasty-simulator.streamlit.app)** *(Sin instalar nada, corre directo en tu navegador)*

Un simulador político y de gestión dinástica impulsado por IA, construido con Python y Streamlit. Inspirado en la profundidad estratégica de *Crusader Kings* y la narrativa de *House of Cards*.

## 🚀 Características Principales
- **🤖 Game Master con IA:** Narrativa dinámica generada por LLM (Groq) con clasificación semántica de intenciones, entendiendo lenguaje natural real en lugar de simples keywords.
- **🏗️ Arquitectura Limpia (Clean Architecture):** Separación estricta de responsabilidades. La lógica de negocio (`mechanics.py`) es 100% pura y desacoplada de la UI (`app.py`, `ui.py`), garantizando testabilidad y mantenimiento.
- **⚖️ Economía y Progresión Balanceada:** Sistema de carreras laborales con cooldowns y topes salariales, más un sistema de empresas escalonado (5 niveles: de Startup a Monopolio) con eventos de riesgo/recompensa.
- **🏠 Calidad de Vida Dinámica:** El costo de vida se ajusta automáticamente según el nivel de vivienda, creando tensión estratégica real entre confort y seguridad financiera.
- **🧪 Calidad de Software Enterprise:** Suite de **33 tests unitarios** con `pytest` que cubren la lógica crítica del negocio (elecciones, golpes de estado, economía, sanitización).
- **🛡️ Seguridad y Robustez:** Validación de esquemas de estado con `Pydantic` y protección activa contra Prompt Injection.

## 🛠️ Stack Tecnológico
- **Lenguaje:** Python 3.10+
- **UI/Frontend:** Streamlit, Plotly (visualización de datos), CSS personalizado
- **IA/LLM:** Groq API (Llama 3) con parsing robusto de JSON
- **Validación:** Pydantic
- **Testing:** Pytest
- **Control de Versiones:** Git, GitHub

## 🎮 Cómo Jugar (Local)
1. Cloná el repositorio: 
   ```bash
   git clone https://github.com/Augusval/legacy-dinasty-simulator.git
   cd legacy-dinasty-simulator
