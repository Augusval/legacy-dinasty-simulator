# 🏛️ LEGACY: Crónicas Dinásticas

**Un simulador narrativo de dinastías políticas y empresariales en Argentina, potenciado por Inteligencia Artificial.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://legacy-dinasty-simulator.streamlit.app/)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎮 ¿Qué es LEGACY?

LEGACY es un juego de rol narrativo donde creás una dinastía que perdura por generaciones. Comenzás como un ciudadano común en Argentina y, a través de decisiones estratégicas, podés convertirte en un magnate empresarial, un líder político o ambos.

Cada acción que tomás tiene consecuencias a largo plazo. Tus hijos heredarán tu imperio (o tus deudas). Tus rivales conspiran en las sombras. La prensa puede hacer o deshacer tu reputación. Y la historia de Argentina se desarrolla a tu alrededor.

**🔗 Jugar ahora:** [https://legacy-dinasty-simulator.streamlit.app/](https://legacy-dinasty-simulator.streamlit.app/)

---

## ✨ Características Principales

### 🎭 Narrativa Dinámica con IA
- **Game Master impulsado por IA**: Cada acción genera narrativa inmersiva y contextual
- **Sistema de fallback**: Si la IA falla, el juego continúa con narrativa procedural (nunca se rompe)
- **Eventos aleatorios**: Crisis, oportunidades y giros inesperados cada turno

### 💼 Sistema Laboral Interactivo
- **Dos caminos profesionales**: 
  - **Técnico**: Junior Developer → Senior Developer → CTO
  - **Corporativo**: Emprendedor → Gerente → Director → CEO
- **Progresión visual**: Checks verdes (disponible), rojos (bloqueado), amarillos (actual)
- **Ascensos lógicos**: Requieren experiencia (6+ meses) y stats específicos
- **Ofertas de trabajo**: La IA puede ofrecerte cargos que podés aceptar

### 🏛️ Carrera Política
- **Cargos electivos**: Diputado → Gobernador → Presidente
- **Campañas electorales**: Éxito basado en reputación, habilidad política y apoyo de facciones
- **Gabinete de ministros**: Gestioná eficiencia, corrupción y lealtad
- **Juicio político**: Si el escándalo llega al máximo, enfrentás un juicio con 3 turnos para defenderte

### 🏢 Imperio Empresarial
- **4 tipos de empresas**: Tech Startup, Inmobiliaria, Banco, Consultora
- **Sistema de niveles**: Las empresas suben de nivel y generan más dividendos
- **Requisitos de habilidad**: Cada empresa requiere cierto nivel de Negocios
- **Conflicto de interés**: No podés fundar empresas siendo Presidente

### 📊 Sistema de Stats
- **Reputación**: Tu credibilidad pública (0-100)
- **Aprobación Pública**: Popularidad (0-100)
- **Nivel de Escándalo**: Riesgo de juicio político (0-100)
- **Habilidades**: Técnica, Política, Negocios (0-100 cada una)
- **Facciones**: Relación con Militares, Sindicatos, Empresarios, Iglesia, Populistas

### 🎯 Objetivos y Logros
- **Objetivos Dinásticos**: Metas a largo plazo con recompensas permanentes
- **Logros**: 8 logros desbloqueables (Magnate, Joven Promesa, Empresario, Genio Técnico, Titán Corporativo, etc.)

### 👨‍👩‍👧 Sistema de Familia
- **Generaciones dinásticas**: Cuando morís, tu heredero toma el mando
- **Matrimonio estratégico**: Alianzas con otras familias poderosas
- **Herencia**: Tu hijo hereda dinero, empresas y reputación

### 📺 Prensa y Medios
- **3 medios principales**: Clarín, La Nación, Página/12
- **Pautas publicitarias**: Comprá apoyo de medios
- **Entrevistas**: Éxito basado en reputación

### ⚔️ Rivales Activos
- **Opositores con IA**: Actúan independientemente cada turno
- **Poder de rivales**: Sube o baja según sus acciones
- **Secretos**: Cada rival tiene información comprometedora

### 📈 Economía Realista
- **Sueldos balanceados**: Desde $30,000 (Junior) hasta $500,000 (CEO) por mes
- **Costo de vida**: Aumenta con nivel de vivienda (6 niveles)
- **Inflación dinámica**: Afecta costos reales
- **Dividendos de empresas**: Ingresos pasivos que crecen con el tiempo

### 🎨 UI/UX
- **10 pestañas organizadas**: Portada, Trabajo, Gobierno, Empresas, Prensa, Rivales, Familia, Objetivos, Logros, Gráficos
- **Sidebar limpia**: Solo stats que impactan gameplay
- **Gráficos de progreso**: Historial de patrimonio y aprobación
- **Tutorial inicial**: Explicación de mecánicas para nuevos jugadores

---

## 🛠️ Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.14 | Lenguaje principal |
| **Streamlit** | 1.38.0 | Framework web |
| **Groq API** | - | Modelos Llama 3 para IA |
| **pytest** | - | Testing |
| **Git** | - | Versionado |
| **GitHub** | - | Repositorio |
| **Streamlit Cloud** | - | Deploy |

---

## 🚀 Instalación Local

### Requisitos
- Python 3.14 o superior
- Cuenta de Groq con API Key (gratis en [console.groq.com](https://console.groq.com))

### Pasos

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/Augusval/legacy-dinasty-simulator.git
   cd legacy-dinasty-simulator
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar API Key**:
   Crear archivo `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "gsk_tu_api_key_aqui"
   ```

4. **Ejecutar la app**:
   ```bash
   streamlit run app.py
   ```

5. **Abrir en navegador**:
   La app se abrirá automáticamente en `http://localhost:8501`

---

## 🎮 Cómo Jugar

### Inicio
1. Creás tu personaje (nombre, edad, origen, ideología, rasgo)
2. Elegís hasta 3 objetivos dinásticos
3. La IA genera tu historia inicial en Argentina

### Gameplay
- **Escribí acciones en el chat**: "Estudiar negocios", "Fundar consultora", "Dar entrevista a Clarín"
- **Usá los botones de las pestañas**: Acceso rápido a acciones comunes
- **Avanzá el tiempo**: Cada acción pasa 1 mes
- **Gestioná tus stats**: Mantené reputación alta, escándalo bajo, y habilidades balanceadas

### Estrategia
- **Early-game**: Estudiá para subir habilidades, conseguí trabajo, ahorrá para tu primera empresa
- **Mid-game**: Fundá empresas, entrá en política, gestioná facciones
- **Late-game**: Llegá a Presidente o CEO, completá objetivos dinásticos, prepará tu heredero

### Game Over
- **Muerte natural**: A los 85 años, tu heredero toma el mando
- **Juicio político**: Si el escándalo llega a 100% y no te defendés

---

## 🧪 Testing

```bash
python -m pytest test_mechanics.py -v
```

**18 tests cubren**:
- Sistema económico (sueldos, dividendos, inflación)
- Acciones de jugador (estudiar, fundar empresas, mejorar vivienda)
- Política (campañas, leyes)
- Escándalo y juicio político
- Facciones y tensión dinámica
- Logros y objetivos

---

## 📊 Arquitectura

### Estructura de Archivos
```text
legacy-dinasty-simulator/
├── app.py              # UI principal y bucle de juego
├── mechanics.py        # Lógica de juego (acciones, economía, política)
├── prompts.py          # Prompts para IA y llamadas a Groq
├── state.py            # Inicialización de estado y utilidades
├── ui.py               # Componentes de UI (sidebar, tabs, renderizado)
├── entidades.py        # Clases (Empresa, Hijo, Ministro, Medio, Rival)
├── test_mechanics.py   # Suite de tests
├── requirements.txt    # Dependencias
└── .streamlit/
    └── secrets.toml    # API Keys (no subido a Git)
```

### Flujo de Juego
1. **Input del jugador** → Texto en chat o botón de UI
2. **Action Router** → Detecta si es acción determinista o libre
3. **Si es determinista** → Ejecuta código en `mechanics.py`
4. **Si es libre** → Envía a IA con contexto del estado
5. **IA responde** → JSON con narrativa + efectos
6. **Procesar respuesta** → Aplica efectos al estado, genera narrativa
7. **Mecánicas post-acción** → Rivales, eventos aleatorios, logros, objetivos
8. **Renderizar UI** → Actualiza sidebar, chat, tabs
9. **Guardar estado** → Session state de Streamlit

---

## 🤝 Contribuciones

Este es un proyecto personal, pero si tenés ideas o encontrás bugs:

1. **Fork** el repositorio
2. **Creá una branch** (`git checkout -b feature/nueva-feature`)
3. **Commit** tus cambios (`git commit -m 'Add nueva feature'`)
4. **Push** a la branch (`git push origin feature/nueva-feature`)
5. **Abrí un Pull Request**

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Créditos

**Desarrollado por**: Augusto Valentini  
**Año**: 2026  
**Inspirado en**: Juegos de estrategia política como *Democracy*, *Tropico*, y simuladores de vida como *The Sims*

---

## 📧 Contacto

- **GitHub**: [Augusval](https://github.com/Augusval)
- **App en vivo**: [legacy-dinasty-simulator.streamlit.app](https://legacy-dinasty-simulator.streamlit.app/)

---

## 🌟 Features Futuras (Backlog)

- [ ] Sistema de préstamos bancarios
- [ ] Crisis nacionales (recesiones, guerras, pandemias)
- [ ] Alianzas matrimoniales estratégicas
- [ ] Eventos históricos de Argentina
- [ ] Multijugador cooperativo
- [ ] Modo sandbox sin objetivos
- [ ] Sistema de leyes personalizables
- [ ] Mapa de Argentina con provincias gobernables

---

**⭐ Si te gusta el proyecto, dale una estrella en GitHub!**