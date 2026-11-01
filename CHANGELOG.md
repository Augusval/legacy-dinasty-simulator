# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-02

### 🚀 Agregado
- **Rivales Activos:** Los rivales políticos ahora toman decisiones propias cada turno (20% de probabilidad) usando IA contextual. Pueden lanzar denuncias, aliarse con facciones o intentar golpes.
- **Eventos Aleatorios Sorpresivos:** 15% de probabilidad por turno de que ocurra un evento inesperado generado por IA (crisis económicas, escándalos de aliados, desastres naturales, oportunidades).
- **Tensión Dinámica de Facciones:** Si una facción sube mucho (>75), la facción opuesta baja automáticamente 10 puntos (ej: acercarse a Militares molesta a Sindicatos).
- **Sistema de Logros:** 6 logros desbloqueables automáticamente (Magnate, Joven Promesa, Empresario, Amado por el Pueblo, Sobreviviente, Legado Eterno).
- **Logging Profesional:** Sistema de logs con `logging` de Python que registra errores, intentos de IA y eventos críticos en `error.log`.
- **Reintentos de IA:** Sistema de 3 reintentos automáticos con fallback elegante si la IA falla, evitando que el juego se rompa.
- **Nueva Pestaña de Logros:** UI dedicada para mostrar logros desbloqueados y bloqueados.
- **4 Tests Nuevos:** Tests para tensión de facciones y desbloqueo de logros (total: 20 tests).

### 🔄 Cambiado
- `prompts.py` ahora incluye generadores de prompts para eventos aleatorios, acciones de rivales y tensión de facciones.
- `mechanics.py` integrado con las nuevas funciones dinámicas que se ejecutan al pasar el tiempo.
- `app.py` actualizado para llamar a las nuevas mecánicas y mostrar la pestaña de logros.

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