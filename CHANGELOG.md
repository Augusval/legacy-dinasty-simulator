# CHANGELOG - LEGACY: Crónicas Dinásticas

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-11-02

### 🎉 Añadido
- **Sistema Laboral Interactivo**: Nueva pestaña "💼 Trabajo" con progresión visual de carreras
- **Dos caminos profesionales**: Camino Técnico (Junior Dev → Senior Dev → CTO) y Camino Corporativo (Emprendedor → Gerente → Director → CEO)
- **Checks visuales**: Verde (disponible), Rojo (bloqueado con requisitos detallados), Amarillo (trabajo actual)
- **Botones de postulación directa**: Al lado de cada cargo disponible
- **Panel de próximo ascenso**: Muestra experiencia requerida y stats necesarios
- **Sistema de ascensos lógicos**: Ya no asciende de Junior Developer a Asesor Político
- **Detección de ofertas de la IA**: Si la IA ofrece "Senior Developer", el jugador puede aceptarlo
- **Nuevos logros**: "Genio Técnico" (alcanzar CTO) y "Titán Corporativo" (alcanzar CEO)
- **Balance económico**: Sueldos reducidos para hacer el early-game más desafiante (Junior Developer: $30,000/mes)

### 🔧 Cambiado
- **Estructura de progresión laboral**: De línea única a dos caminos separados (Técnico y Corporativo)
- **UI de pestaña Trabajo**: De lista de texto a interfaz interactiva con colores y botones
- **Router de acciones**: Ahora detecta "aceptar oferta de [cargo]" y "postularme a [cargo]"

### 🐛 Corregido
- **Bug de ascensos ilógicos**: Junior Developer ya no asciende a Asesor Político
- **Bug de ofertas de IA**: Las ofertas de trabajos como "Senior Developer" ahora son aceptables
- **Bug de acciones duplicadas**: Sistema de bloqueo cuando se procesa una acción

---

## [1.3.0] - 2026-11-01

### 🎉 Añadido
- **Sistema de fallback procedural**: Cuando la IA falla, el juego usa narrativa generada por código
- **Resiliencia del sistema**: El juego nunca se rompe, incluso si Groq está caído

### 🔧 Cambiado
- **Eliminación de stats innecesarias**: Removidas Energía, Salud Física y Salud Mental de la UI
- **Simplificación de UI**: Sidebar más limpia, solo stats que impactan gameplay
- **Modelo de IA actualizado**: Migración de modelos descontinuados de Groq

### 🐛 Corregido
- **Bug de mensajes vacíos**: El chat ya no muestra burbujas en blanco
- **Bug de router de acciones**: "Fundar consultora" ahora funciona sin requerir la palabra "empresa"
- **Bug de Rival**: Agregado parámetro `cargo` faltante en inicialización

### 🧪 Testing
- **18 tests pasando**: Suite de tests actualizada para reflejar cambios de UI

---

## [1.2.0] - 2026-10-28

### 🎉 Añadido
- **Sistema de Facciones**: Militares, Sindicatos, Empresarios, Iglesia, Populistas
- **Tensión dinámica de facciones**: Si una facción sube mucho, la opuesta baja automáticamente
- **Sistema de Logros**: 6 logros desbloqueables (Magnate, Joven Promesa, Empresario, etc.)
- **Objetivos Dinásticos**: Metas a largo plazo con recompensas permanentes
- **Sistema de Ministros**: Gabinete con eficiencia, corrupción y lealtad
- **Eventos aleatorios**: 15% de probabilidad por turno de eventos inesperados
- **Acciones de rivales**: Los rivales actúan con 20% de probabilidad por turno
- **Sistema de Juicio Político**: Si el escándalo llega a 100%, se activa juicio con 3 turnos para defenderse
- **Gráficos de progreso**: Historial de patrimonio y aprobación pública
- **Salón de la Fama**: Top 5 dinastías con más puntos

### 🔧 Cambiado
- **Economía**: Sistema de dividendos de empresas, inflación dinámica, costo de vida por nivel
- **Política**: Campañas electorales con cálculo de votos basado en reputación, habilidad política y facciones
- **Prensa**: Interacción con medios (pautas publicitarias, entrevistas con éxito/fracaso)

---

## [1.1.0] - 2026-10-20

### 🎉 Añadido
- **Sistema de empresas**: 4 tipos (Tech Startup, Inmobiliaria, Banco, Consultora)
- **Sistema de vivienda**: 6 niveles de calidad de vida
- **Sistema de estudio**: 3 enfoques (Técnica, Política, Negocios)
- **Sistema de medios de comunicación**: Clarín, La Nación, Página/12
- **Sistema de rivales**: Opositores con poder y secretos
- **Sistema de familia**: Generaciones dinásticas, herederos, matrimonio
- **Tutorial inicial**: Explicación de mecánicas al comenzar el juego

### 🔧 Cambiado
- **UI**: Sistema de pestañas (Portada, Gobierno, Empresas, Prensa, Rivales, Familia, Objetivos, Logros, Gráficos)
- **Narrativa**: La IA genera contexto inmersivo basado en stats actuales
- **Game Over**: Sistema de legado con biografía descargable y continuación dinástica

---

## [1.0.0] - 2026-10-15

### 🎉 Añadido
- **Simulador de dinastía política/empresarial**: Juego de rol narrativo con IA
- **Sistema de creación de personaje**: Nombre, apellido, edad, género, origen, ideología, rasgo
- **Stats base**: Reputación, Aprobación Pública, Escándalo, Habilidades
- **Sistema de cargos políticos**: Ciudadano → Diputado → Gobernador → Presidente
- **Integración con Groq API**: Modelos Llama para narrativa dinámica
- **Sistema de turnos**: Cada acción avanza el tiempo y procesa economía
- **Persistencia de estado**: Session state de Streamlit
- **Deploy en Streamlit Cloud**: App web accesible públicamente

### 🛠️ Tecnologías
- **Backend**: Python 3.14
- **Framework**: Streamlit 1.38.0
- **IA**: Groq API (modelos Llama 3)
- **Testing**: pytest
- **Versionado**: Git + GitHub
- **Deploy**: Streamlit Cloud

---

## Notas de Desarrollo

### Filosofía de Diseño
- **Resiliencia primero**: El juego nunca se rompe, incluso si la IA falla
- **Progresión significativa**: Cada decisión tiene consecuencias a largo plazo
- **Narrativa inmersiva**: La IA genera contexto rico basado en el estado del jugador
- **Balance desafiante**: El early-game es difícil, los logros se sienten ganados

### Futuras Mejoras (Backlog)
- Sistema de préstamos bancarios
- Mecánica de crisis nacionales (recesiones, guerras, pandemias)
- Sistema de alianzas matrimoniales estratégicas
- Eventos históricos de Argentina
- Multijugador cooperativo
- Modo "sandbox" sin objetivos fijos