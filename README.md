# 🏛️ LEGACY: Political Dynasty Simulator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://legacy-dinasty-simulator.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI/CD Tests](https://github.com/Augusval/legacy-dinasty-simulator/actions/workflows/ci-tests.yml/badge.svg)](https://github.com/Augusval/legacy-dinasty-simulator/actions/workflows/ci-tests.yml)

> **🎮 [JUGAR VERSIÓN 1.1 EN VIVO](https://legacy-dinasty-simulator.streamlit.app)** *(Sin instalar nada, corre directo en tu navegador)*

Simulador político, económico y de gestión dinástica impulsado por IA (LLM). Inspirado en la profundidad estratégica de *Crusader Kings* y la narrativa de *House of Cards*.

## 🚀 Características Principales (v1.1)

### 🏗️ Arquitectura de Software
- **Clean Architecture & Dataclasses:** Separación estricta de responsabilidades. La lógica de negocio (`mechanics.py`) está 100% desacoplada de la UI (`app.py`, `ui.py`) y utiliza Dataclasses tipadas (`entidades.py`) en lugar de diccionarios anidados.
- **Action Router System:** Sistema híbrido que resuelve acciones mecánicas deterministas (ej: fundar empresas, estudiar) en código puro para ahorrar tokens de IA, delegando solo la narrativa y eventos complejos al LLM.
- **CI/CD con GitHub Actions:** Pipeline automatizado que ejecuta 16 tests unitarios con `pytest` en cada push, garantizando la estabilidad del motor de juego.

### 🎮 Mecánicas de Juego Profundas
- **Habilidades con Impacto Real:** Técnica (sueldos y megaobras), Política (campañas y debates) y Negocios (fundación y dividendos de empresas).
- **Gabinete de Ministros:** Nombrá ministros con stats de Eficiencia, Lealtad y Corrupción. Un ministro corrupto aumentará tu escándalo en silencio; uno ineficiente disparará la inflación.
- **Prensa y Narrativa:** 3 medios de comunicación con posturas ideológicas. Comprá pauta o da entrevistas para manipular la opinión pública.
- **Sistema de Escándalo y Juicio Político:** Si tu nivel de escándalo llega a 100, se dispara un Juicio Político. Si no te defendés, perdés la partida por destitución.
- **Imperio Corporativo:** Fundá empresas (Consultora, Tech, Inmobiliaria, Banco) que escalan de nivel y generan dividendos pasivos multiplicados por tu Habilidad en Negocios.

## 🛠️ Stack Tecnológico
- **Backend/Lógica:** Python 3.10+ (Dataclasses, Type Hinting)
- **Frontend/UI:** Streamlit, Plotly (Visualización de datos históricos)
- **IA/LLM:** Groq API (Llama 3) con parsing robusto de JSON
- **Testing:** Pytest (16 tests unitarios pasando)
- **Control de Versiones:** Git, GitHub Actions (CI/CD)

## 🎮 Cómo Jugar (Local)
1. Cloná el repositorio: 
   `git clone https://github.com/Augusval/legacy-dinasty-simulator.git && cd legacy-dinasty-simulator`
2. Instalá las dependencias: 
   `pip install -r requirements.txt`
3. Configurá tu API key creando un archivo `.streamlit/secrets.toml`:
   `GROQ_API_KEY = "tu_api_key_aqui"`
4. Ejecutá la aplicación: 
   `streamlit run app.py`

## 🧪 Testing
El proyecto cuenta con pruebas unitarias automatizadas para garantizar la estabilidad de la lógica de negocio:
`python -m pytest test_mechanics.py -v`
*(Resultado esperado: 16 passed)*

---
*Desarrollado como proyecto de portafolio para demostrar habilidades en arquitectura de software, integración de IA, CI/CD y desarrollo de productos interactivos.*