# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-02

### 🚀 Agregado
- **Nuevas Mecánicas de Juego:**
  - Sistema de Ministros con Lealtad, Eficiencia y Corrupción.
  - Sistema de Prensa y Medios de Comunicación (Clarín, Página 12, TN) con posturas ideológicas.
  - Sistema de Escándalo y Juicio Político (Game Over por destitución).
  - Mecánica real para fundar y escalar Empresas (Consultora, Tech, Inmobiliaria, Banco).
  - Habilidades diferenciadas (Técnica, Política, Negocios) con impacto real en la economía y política.
- **Arquitectura y Código:**
  - Nuevo archivo `entidades.py` usando Dataclasses tipadas (`Empresa`, `Hijo`, `Ministro`, `Medio`, `Rival`).
  - Implementación de `Action Router` en `mechanics.py` para resolver acciones deterministas sin gastar tokens de IA.
  - Pipeline de CI/CD con GitHub Actions (`ci-tests.yml`) para ejecución automática de tests.
  - Dashboard de métricas históricas con Plotly (Patrimonio vs. Aprobación de doble eje).
- **Testing:**
  - 16 tests unitarios en `test_mechanics.py` cubriendo empresas, habilidades, economía y política.

### 🔄 Cambiado
- **Refactorización Masiva:**
  - `app.py` reducido de ~500 líneas a ~150 líneas (pura orquestación).
  - `mechanics.py` reescrito con funciones puras y desacopladas.
  - `state.py` ahora maneja la inicialización inteligente con modificadores de Origen, Rasgo e Ideología.
  - `ui.py` separado en funciones de renderizado declarativo.
- **Balance de Juego:**
  - Objetivos dinásticos rebalanceados para ser alcanzables pero desafiantes.
  - El origen y el rasgo del personaje ahora otorgan stats y modificadores iniciales reales.

### 🗑️ Eliminado
- `data.py` (Constantes redistribuidas a `state.py` y `entidades.py`).
- Más de 3000 líneas de código spaghetti, hardcodeo y lógica duplicada en la UI.

### 🐛 Corregido
- Bug donde los nombres aleatorios se reseteaban al hacer clic en el formulario (uso de `session_state`).
- Las habilidades de Política y Negocios ahora afectan correctamente las campañas y los dividendos.
- Errores de parsing de JSON de la IA manejados con `extraer_json_de_respuesta` robusto.

## [1.0.0] - 2026-10-01

### 🚀 Agregado
- Versión inicial del simulador.
- Integración básica con Groq API (Llama 3).
- Sistema de turnos, economía básica y campañas electorales.
- Deploy inicial en Streamlit Cloud.