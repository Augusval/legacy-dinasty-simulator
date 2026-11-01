import random
import logging
import streamlit as st
import prompts
import mechanics
import ui
from state import inicializar_estado, leer_hall_of_fame, NOMBRES_PILA
from entidades import Empresa, Hijo, Ministro, Medio, Rival

# ==============================================================================
# CONFIGURACIÓN INICIAL
# ==============================================================================

logger = logging.getLogger(__name__)

st.set_page_config(page_title="LEGACY v1.2", layout="wide", page_icon="📰")
ui.inyectar_css()

if "juego_iniciado" not in st.session_state:
    st.session_state.juego_iniciado = False
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "tutorial_visto" not in st.session_state:
    st.session_state.tutorial_visto = False

st.title("LEGACY - Crónicas Dinásticas v1.2")

# ==============================================================================
# PANTALLA DE INICIO
# ==============================================================================

if not st.session_state.juego_iniciado:
    st.markdown("## El Comienzo de una Dinastía")
    
    hof = leer_hall_of_fame()
    if hof:
        with st.expander("🏛️ Salón de la Fama Dinástico"):
            for i, entry in enumerate(hof[:5], 1):
                st.markdown(f"{i}. **{entry['apellido']}** | {entry['cargo']} | {entry['puntos']:,} pts")

    if "nombre_inicial" not in st.session_state:
        APELLIDOS_ARGENTINOS = ["González", "Rodríguez", "Gómez", "Fernández", "López", "Martínez", "Sánchez", "Pérez"]
        st.session_state.nombre_inicial = random.choice(NOMBRES_PILA)
        st.session_state.apellido_inicial = random.choice(APELLIDOS_ARGENTINOS)

    with st.form("create_game"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre:", value=st.session_state.nombre_inicial)
            genero = st.selectbox("Género:", ["Masculino", "Femenino"])
            edad = st.number_input("Edad inicial:", min_value=18, max_value=65, value=24, step=1)
        with col2:
            apellido = st.text_input("Apellido de la Dinastía:", value=st.session_state.apellido_inicial)
            origen = st.selectbox("Origen:", ["Técnico", "Político", "Comerciante"])
            ideologia = st.selectbox("Ideología:", ["Conservador", "Liberal", "Socialdemócrata", "Socialista", "Nacionalista", "Populista", "Tecnócrata"])
            
        rasgo = st.selectbox("Rasgo de Personalidad:", ["Carismático", "Mente Fría", "Trabajador"])
        
        objetivos = st.multiselect(
            "Objetivos Dinásticos (Elegí hasta 3):",
            ["Alcanzar la Presidencia antes de los 55", "Acumular $5M en patrimonio", "Fundar una empresa Nivel 4", "Sobrevivir a 3 Crisis Nacionales"],
            max_selections=3
        )

        if st.form_submit_button("Comenzar Dinastía", type="primary", use_container_width=True):
            del st.session_state.nombre_inicial
            del st.session_state.apellido_inicial
            
            estado = inicializar_estado(nombre, apellido, edad, genero, origen, ideologia, rasgo)
            estado["objetivos_dinasticos"] = objetivos
            estado["objetivos_completados"] = []
            estado["bonificaciones_objetivos"] = []
            
            st.session_state.estado = estado
            st.session_state.juego_iniciado = True
            st.session_state.game_over = None
            st.session_state.hof_guardado = False
            
            system_prompt = prompts.construir_sistema(nombre, edad, "Soy un ciudadano.", rasgo, origen, ideologia)
            mensajes_iniciales = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Inicia el juego describiendo la situación actual del personaje y su entorno en Argentina. Responde en JSON: {\"narrativa\": \"...\", \"efectos\": {}}"}
            ]
            
            with st.spinner("El Game Master está preparando el escenario..."):
                respuesta_raw = prompts.llamar_llm(mensajes_iniciales, 0, "", es_inicio=True)
                json_data = prompts.extraer_json_de_respuesta(respuesta_raw)
                
                narrativa_inicial = json_data.get("narrativa", f"Bienvenido a LEGACY, {nombre} {apellido}. Tenés {edad} años y vivís en Argentina. Tu historia comienza ahora.")
                
                st.session_state.mensajes.append({"role": "assistant", "content": narrativa_inicial})
                st.session_state.estado["titular_periodico"] = f"Comienza la era de la Dinastía {apellido}."
                
            st.rerun()
    st.stop()

# ==============================================================================
# PANTALLA DE JUEGO (BUCLE PRINCIPAL)
# ==============================================================================
else:
    estado = st.session_state.estado

    # --- GAME OVER ---
    if st.session_state.get("game_over"):
        st.error(st.session_state.game_over)
        st.subheader("⚰️ El Fin de una Era")
        
        from state import calcular_legado, generar_biografia, continuar_dinastia, guardar_hall_of_fame
        puntos, rango = calcular_legado(estado)
        
        if not st.session_state.get("hof_guardado", False):
            guardar_hall_of_fame(puntos, rango, estado)
            st.session_state.hof_guardado = True
            
        st.markdown(f"### Rango de Legado: **{rango}** ({puntos} pts)")
        st.write(f"Generación: **{estado.get('generacion_actual', 1)}** | Cargo máximo: **{estado.get('cargo_politico')}**")
        
        biografia = generar_biografia(estado)
        st.download_button("📜 Descargar Biografía", data=biografia, file_name=f"legado_{estado.get('apellido_dinastia')}.txt")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👑 Continuar Dinastía", type="primary", use_container_width=True):
                nuevo_estado, msg = continuar_dinastia(estado)
                if nuevo_estado:
                    st.session_state.estado = nuevo_estado
                    st.session_state.game_over = None
                    st.session_state.hof_guardado = False
                    st.session_state.mensajes.append({"role": "assistant", "content": msg})
                    st.rerun()
        with col2:
            if st.button("🔄 Nueva Partida", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
        st.stop()

    # --- UI PRINCIPAL ---
    ui.render_cabecera(estado)
    ui.render_sidebar(estado)

    tab_cronicas, tab_gobierno, tab_empresas, tab_prensa, tab_rivales, tab_vida, tab_objetivos, tab_logros, tab_graficos = st.tabs([
        "📰 Portada", "🏛️ Gobierno", "🏢 Empresas", "📺 Prensa", "⚔️ Rivales", "👨‍👩‍👧 Familia", "🎯 Objetivos", "🏆 Logros", "📊 Gráficos"
    ])

    # =====================================================================
    # PESTAÑA PORTADA (Chat principal)
    # =====================================================================
    with tab_cronicas:
        ui.render_titular(estado)

        # Tutorial inicial
        if not st.session_state.tutorial_visto:
            st.markdown("""
            <div style="background-color: #1a1d24; border-left: 5px solid #d4af37; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #d4af37; margin-top: 0;">📖 Cómo jugar LEGACY</h3>
                <p>Bienvenido a tu dinastía política. Usá las pestañas de arriba para acceder a las diferentes mecánicas:</p>
                <ul>
                    <li>🏛️ <b>Gobierno:</b> Postulate a cargos políticos y gestioná tu gabinete.</li>
                    <li>🏢 <b>Empresas:</b> Fundá y gestioná tu imperio corporativo.</li>
                    <li>📺 <b>Prensa:</b> Influí en la opinión pública a través de los medios.</li>
                    <li>🎯 <b>Objetivos:</b> Revisá tus metas dinásticas y sus recompensas.</li>
                </ul>
                <p><i>También podés escribir cualquier acción en el chat de abajo.</i></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✅ Entendido, comenzar a jugar", type="primary"):
                st.session_state.tutorial_visto = True
                st.rerun()
            st.stop()

        # Historial de chat
        with st.container(height=400):
            for msg in st.session_state.mensajes[-10:]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Estados especiales
        if estado.get("hospitalizado"):
            st.warning("🏥 Estás hospitalizado. Debés recuperarte.")
            if st.button("🛌 Descansar 30 días", type="primary"):
                estado["hospitalizado"] = False
                estado["edad"] += 0.083 * 30
                estado["salud_fisica"] = min(100, estado["salud_fisica"] + 50)
                st.session_state.mensajes.append({"role": "assistant", "content": "Te recuperaste en el hospital. Pasaron 30 días."})
                st.rerun()
            st.stop()

        if estado.get("juicio_politico_activo"):
            st.error("⚖️ **JUICIO POLÍTICO ACTIVO:** Tenés que defenderte o serás destituido.")
            if st.button("🗣️ Discurso de Defensa (Cuesta 20 Reputación)", type="primary"):
                estado["juicio_politico_activo"] = False
                estado["nivel_escandalo"] = 50
                estado["reputacion"] = max(0, estado["reputacion"] - 20)
                st.session_state.mensajes.append({"role": "assistant", "content": "Lograste frenar el juicio, pero tu imagen quedó muy dañada."})
                st.rerun()
            st.stop()

        st.divider()

        # Input del chat
        accion = st.chat_input("Escribí tu acción... (ej: 'Estudiar política', 'Dar entrevista a Clarín')")
        
        if accion:
            st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
            
            # 1. Intentar resolver con código puro (Action Router)
            es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
            
            if es_determinista:
                # La acción se ejecutó en código. Pedimos a la IA que la narre.
                try:
                    contexto = prompts.generar_prompt_contexto(estado)
                    mensajes_chat = [
                        {"role": "system", "content": f"Eres el narrador de LEGACY. El jugador hizo: {accion}. Resultado mecánico: {msg_determinista}. Narrá en 2-3 oraciones inmersivas lo que pasó. Responde en JSON: {{\"narrativa\": \"texto\", \"efectos\": {{}}}}"},
                        {"role": "user", "content": f"Contexto: {contexto}"}
                    ]
                    respuesta_raw = prompts.llamar_llm(mensajes_chat, 0, "")
                    json_data = prompts.extraer_json_de_respuesta(respuesta_raw)
                    narrativa_final = json_data.get("narrativa", msg_determinista)
                except Exception as e:
                    logger.warning(f"IA de narración falló: {e}")
                    narrativa_final = msg_determinista
                
                st.session_state.mensajes.append({"role": "assistant", "content": narrativa_final})
                estado["turno"] += 1
                estado["energia"] = max(0, estado["energia"] - 10)
                
            else:
                # 2. Acción libre, la IA decide todo
                with st.spinner("El Game Master está simulando..."):
                    contexto = prompts.generar_prompt_contexto(estado)
                    mensajes_chat = [
                        {"role": "system", "content": prompts.construir_sistema(estado["nombre"], estado["edad"], "Historia...", estado["rasgo"], "Origen", estado["ideologia"])},
                        {"role": "system", "content": f"CONTEXTO ACTUAL:\n{contexto}"},
                        *st.session_state.mensajes[-6:]
                    ]
                    
                    respuesta_raw = prompts.llamar_llm(mensajes_chat, 7, "")
                    json_data = prompts.extraer_json_de_respuesta(respuesta_raw)
                    
                    estado, narrativa_final, game_over = mechanics.procesar_respuesta(
                        json_data.get("narrativa", ""), 7, estado
                    )
                    
                    st.session_state.mensajes.append({"role": "assistant", "content": narrativa_final})
                    if game_over:
                        st.session_state.game_over = game_over
                    
                    estado["turno"] += 1
                    estado["energia"] = max(0, estado["energia"] - 10)

            # --- MECÁNICAS DINÁMICAS POST-ACCIÓN ---
            objetivos_nuevos = mechanics.verificar_objetivos_dinasticos(estado)
            for obj_msg in objetivos_nuevos:
                st.session_state.mensajes.append({"role": "assistant", "content": obj_msg})
            
            evento_ocurrio, msg_evento = mechanics.procesar_evento_aleatorio(estado)
            if evento_ocurrio:
                st.session_state.mensajes.append({"role": "assistant", "content": msg_evento})

            acciones_rivales = mechanics.procesar_turno_rivales(estado)
            for msg_rival in acciones_rivales:
                st.session_state.mensajes.append({"role": "assistant", "content": msg_rival})

            nuevos_logros = mechanics.verificar_logros(estado)
            for logro in nuevos_logros:
                st.toast(f"🏆 Logro desbloqueado: {logro}!", icon="🎖️")
                
            st.rerun()

        # Botón para avanzar tiempo
        with st.expander("⏳ Dejar pasar el tiempo"):
            if st.button("⏭️ Avanzar 1 mes (Descansar)"):
                estado["turno"] += 1
                estado["energia"] = min(100, estado["energia"] + 30)
                resumen = mechanics.procesar_economia(estado)
                st.session_state.mensajes.append({"role": "assistant", "content": f"⏳ *Pasaste el tiempo descansando.*\n\n{resumen}"})
                
                objetivos_nuevos = mechanics.verificar_objetivos_dinasticos(estado)
                for obj_msg in objetivos_nuevos:
                    st.session_state.mensajes.append({"role": "assistant", "content": obj_msg})
                
                evento_ocurrio, msg_evento = mechanics.procesar_evento_aleatorio(estado)
                if evento_ocurrio:
                    st.session_state.mensajes.append({"role": "assistant", "content": msg_evento})
                    
                nuevos_logros = mechanics.verificar_logros(estado)
                for logro in nuevos_logros:
                    st.toast(f"🏆 Logro desbloqueado: {logro}!", icon="🎖️")
                    
                st.rerun()

    # =====================================================================
    # PESTAÑA GOBIERNO
    # =====================================================================
    with tab_gobierno:
        ui.render_tab_gobierno(estado)
        st.divider()
        
        if estado.get("cargo_politico") == "Ciudadano":
            st.subheader("🗳️ Ingresar a la Política")
            st.markdown("Postulate a un cargo público para comenzar tu carrera política.")
            
            if st.button("🗳️ Postularme a Diputado", type="primary", use_container_width=True):
                accion = "postularme a diputado"
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                if estado.get("reputacion", 0) < 30:
                    st.session_state.mensajes.append({"role": "assistant", "content": f"❌ **Requisitos insuficientes:** Necesitás al menos 30 de Reputación para postularte a Diputado. Tu reputación actual es {estado.get('reputacion', 50)}."})
                else:
                    ok, msg = mechanics.calcular_exito_campana(estado, "Diputado")
                    if ok:
                        estado["cargo_politico"] = "Diputado"
                        estado["turnos_en_poder"] = 0
                    st.session_state.mensajes.append({"role": "assistant", "content": msg})
                
                estado["turno"] += 1
                estado["energia"] = max(0, estado["energia"] - 20)
                st.rerun()

    # =====================================================================
    # PESTAÑA EMPRESAS
    # =====================================================================
    with tab_empresas:
        ui.render_tab_empresas(estado)
        st.divider()
        
        st.subheader("🏢 Fundar Nueva Empresa")
        st.markdown("Creá tu imperio corporativo. Cada tipo de empresa tiene diferentes requisitos y dividendos.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💻 Fundar Tech Startup\n(Costo: $250K | Req: 50 Negocios)", use_container_width=True):
                accion = "fundar empresa tech"
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
                st.session_state.mensajes.append({"role": "assistant", "content": msg_determinista})
                
                if es_determinista:
                    estado["turno"] += 1
                    estado["energia"] = max(0, estado["energia"] - 15)
                
                st.rerun()
        
        with col2:
            if st.button("🏠 Fundar Inmobiliaria\n(Costo: $500K | Req: 70 Negocios)", use_container_width=True):
                accion = "fundar inmobiliaria"
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
                st.session_state.mensajes.append({"role": "assistant", "content": msg_determinista})
                
                if es_determinista:
                    estado["turno"] += 1
                    estado["energia"] = max(0, estado["energia"] - 15)
                
                st.rerun()
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("🏦 Fundar Banco\n(Costo: $1M | Req: 85 Negocios)", use_container_width=True):
                accion = "fundar banco"
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
                st.session_state.mensajes.append({"role": "assistant", "content": msg_determinista})
                
                if es_determinista:
                    estado["turno"] += 1
                    estado["energia"] = max(0, estado["energia"] - 15)
                
                st.rerun()
        
        with col4:
            if st.button("📊 Fundar Consultora\n(Costo: $100K | Req: 30 Negocios)", use_container_width=True):
                accion = "fundar consultora"
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
                st.session_state.mensajes.append({"role": "assistant", "content": msg_determinista})
                
                if es_determinista:
                    estado["turno"] += 1
                    estado["energia"] = max(0, estado["energia"] - 15)
                
                st.rerun()

    # =====================================================================
    # PESTAÑA PRENSA
    # =====================================================================
    with tab_prensa:
        ui.render_tab_prensa(estado)

    # =====================================================================
    # PESTAÑA RIVALES
    # =====================================================================
    with tab_rivales:
        ui.render_tab_rivales(estado)

    # =====================================================================
    # PESTAÑA FAMILIA
    # =====================================================================
    with tab_vida:
        ui.render_tab_vida(estado)

    # =====================================================================
    # PESTAÑA OBJETIVOS
    # =====================================================================
    with tab_objetivos:
        ui.render_tab_objetivos(estado)

    # =====================================================================
    # PESTAÑA LOGROS
    # =====================================================================
    with tab_logros:
        ui.render_tab_logros(estado)
                
    # =====================================================================
    # PESTAÑA GRÁFICOS
    # =====================================================================
    with tab_graficos:
        ui.render_tab_graficos(estado)