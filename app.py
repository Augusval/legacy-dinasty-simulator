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

st.set_page_config(page_title="LEGACY", layout="wide", page_icon="📰")
ui.inyectar_css()

# Inicialización de Session State
if "juego_iniciado" not in st.session_state:
    st.session_state.juego_iniciado = False
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "tutorial_visto" not in st.session_state:
    st.session_state.tutorial_visto = False
if "procesando" not in st.session_state:
    st.session_state.procesando = False  # FIX: Evita acciones duplicadas

st.title("LEGACY - Crónicas Dinásticas")

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
            estado["turnos_en_trabajo"] = 0
            
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
                
                if narrativa_inicial and narrativa_inicial.strip():
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
                    if msg: st.session_state.mensajes.append({"role": "assistant", "content": msg})
                    st.rerun()
        with col2:
            if st.button("🔄 Nueva Partida", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
        st.stop()

    # --- UI PRINCIPAL ---
    ui.render_cabecera(estado)
    ui.render_sidebar(estado)

    tab_cronicas, tab_trabajo, tab_gobierno, tab_empresas, tab_prensa, tab_rivales, tab_familia, tab_objetivos, tab_logros, tab_graficos = st.tabs([
        "📰 Portada", "💼 Trabajo", "🏛️ Gobierno", "🏢 Empresas", "📺 Prensa", "⚔️ Rivales", "👨‍👩‍👧 Familia", "🎯 Objetivos", "🏆 Logros", "📊 Gráficos"
    ])

    # =====================================================================
    # PESTAÑA PORTADA (Chat principal)
    # =====================================================================
    with tab_cronicas:
        ui.render_titular(estado)

        if not st.session_state.tutorial_visto:
            st.markdown("""
            <div style="background-color: #1a1d24; border-left: 5px solid #d4af37; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #d4af37; margin-top: 0;">📖 Cómo jugar LEGACY</h3>
                <p>Usá las pestañas de arriba para acceder a las diferentes mecánicas. También podés escribir acciones en el chat.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("✅ Entendido, comenzar a jugar", type="primary"):
                st.session_state.tutorial_visto = True
                st.rerun()
            st.stop()

        with st.container(height=400):
            for msg in st.session_state.mensajes[-10:]:
                if msg["content"] and msg["content"].strip():
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if estado.get("juicio_politico_activo"):
            st.error("⚖️ **JUICIO POLÍTICO ACTIVO:** Tenés que defenderte o serás destituido.")
            if st.button("🗣️ Discurso de Defensa (Cuesta 20 Reputación)", type="primary", disabled=st.session_state.get("procesando", False)):
                estado["juicio_politico_activo"] = False
                estado["nivel_escandalo"] = 50
                estado["reputacion"] = max(0, estado["reputacion"] - 20)
                st.session_state.mensajes.append({"role": "assistant", "content": "Lograste frenar el juicio, pero tu imagen quedó muy dañada."})
                st.rerun()
            st.stop()

        st.divider()

        esta_procesando = st.session_state.get("procesando", False)
        
        if esta_procesando:
            st.info("⏳ El Game Master está procesando tu última acción. Por favor esperá...")

        accion = st.chat_input("Escribí tu acción... (ej: 'Estudiar política', 'Pedir ascenso')", disabled=esta_procesando)
        
        if accion and not esta_procesando:
            try:
                # 1. Bloqueamos la UI inmediatamente
                st.session_state.procesando = True
                st.session_state.mensajes.append({"role": "user", "content": f"🎯 {accion}"})
                
                # 2. Intentamos resolver con código puro (Action Router)
                es_determinista, msg_determinista = mechanics.ejecutar_accion_determinista(estado, accion)
                
                if es_determinista:
                    try:
                        contexto = prompts.generar_prompt_contexto(estado)
                        mensajes_chat = [
                            {"role": "system", "content": f"Eres el narrador. El jugador hizo: {accion}. Resultado: {msg_determinista}. Narrá en 2-3 oraciones. Responde SOLO en JSON válido: {{\"narrativa\": \"texto\"}}"},
                            {"role": "user", "content": f"Contexto: {contexto}"}
                        ]
                        respuesta_raw = prompts.llamar_llm(mensajes_chat, 0, "")
                        json_data = prompts.extraer_json_de_respuesta(respuesta_raw)
                        narrativa_final = json_data.get("narrativa", msg_determinista)
                    except Exception as e:
                        logger.warning(f"IA de narración falló, usando mensaje directo: {e}")
                        narrativa_final = msg_determinista
                    
                    if narrativa_final and narrativa_final.strip():
                        st.session_state.mensajes.append({"role": "assistant", "content": narrativa_final})
                    estado["turno"] += 1
                    
                else:
                    # 3. Acción libre, la IA (o el fallback) decide todo
                    with st.spinner("El Game Master está simulando (esto puede tardar unos segundos)..."):
                        try:
                            contexto = prompts.generar_prompt_contexto(estado)
                            mensajes_chat = [
                                {"role": "system", "content": prompts.construir_sistema(estado["nombre"], estado["edad"], "Historia...", estado["rasgo"], "Origen", estado["ideologia"])},
                                {"role": "system", "content": f"CONTEXTO ACTUAL:\n{contexto}"},
                                *st.session_state.mensajes[-6:]
                            ]
                            
                            # AQUÍ TU FUNCIÓN llamar_llm HACE SU MAGIA (REINTENTOS + FALLBACK)
                            respuesta_raw = prompts.llamar_llm(mensajes_chat, 7, "")
                            json_data = prompts.extraer_json_de_respuesta(respuesta_raw)
                            
                            estado, narrativa_final, game_over = mechanics.procesar_respuesta(json_data.get("narrativa", ""), 7, estado)
                            
                            if narrativa_final and narrativa_final.strip():
                                st.session_state.mensajes.append({"role": "assistant", "content": narrativa_final})
                            if game_over:
                                st.session_state.game_over = game_over
                            estado["turno"] += 1
                            
                        except Exception as e:
                            logger.error(f"Error crítico en procesamiento de IA: {e}")
                            st.session_state.mensajes.append({"role": "assistant", "content": "⚠️ **El Game Master se mareó:** Ocurrió un error inesperado, pero tu personaje está a salvo. Intentá de nuevo."})

                # 4. Mecánicas post-acción (rivales, eventos, logros)
                try:
                    for obj_msg in mechanics.verificar_objetivos_dinasticos(estado):
                        if obj_msg and obj_msg.strip(): 
                            st.session_state.mensajes.append({"role": "assistant", "content": obj_msg})
                    
                    evento_ocurrio, msg_evento = mechanics.procesar_evento_aleatorio(estado)
                    if evento_ocurrio and msg_evento and msg_evento.strip():
                        st.session_state.mensajes.append({"role": "assistant", "content": msg_evento})

                    for msg_rival in mechanics.procesar_turno_rivales(estado):
                        if msg_rival and msg_rival.strip(): 
                            st.session_state.mensajes.append({"role": "assistant", "content": msg_rival})

                    for logro in mechanics.verificar_logros(estado):
                        st.toast(f"🏆 Logro desbloqueado: {logro}!", icon="🎖️")
                except Exception as e:
                    logger.error(f"Error en mecánicas post-acción: {e}")

            except Exception as e:
                logger.error(f"Error inesperado en el bucle principal: {e}")
                st.error(f"❌ Error: {str(e)}")
                
            finally:
                # 5. ESTO ES LO MÁS IMPORTANTE: SE EJECUTA SIEMPRE, INCLUSO SI HUBO ERROR
                st.session_state.procesando = False
                st.rerun()

        with st.expander("⏳ Dejar pasar el tiempo"):
            if st.button("⏭️ Avanzar 1 mes (Descansar)", disabled=esta_procesando):
                st.session_state.procesando = True
                estado["turno"] += 1
                resumen = mechanics.procesar_economia(estado)
                if resumen and resumen.strip():
                    st.session_state.mensajes.append({"role": "assistant", "content": f"⏳ *Pasaste el tiempo.*\n\n{resumen}"})
                
                try:
                    for obj_msg in mechanics.verificar_objetivos_dinasticos(estado):
                        if obj_msg and obj_msg.strip(): st.session_state.mensajes.append({"role": "assistant", "content": obj_msg})
                    evento_ocurrio, msg_evento = mechanics.procesar_evento_aleatorio(estado)
                    if evento_ocurrio and msg_evento and msg_evento.strip():
                        st.session_state.mensajes.append({"role": "assistant", "content": msg_evento})
                    for logro in mechanics.verificar_logros(estado):
                        st.toast(f"🏆 Logro desbloqueado: {logro}!", icon="🎖️")
                except Exception:
                    pass
                    
                st.session_state.procesando = False
                st.rerun()

    # =====================================================================
    # PESTAÑA TRABAJO (INTERACTIVA)
    # =====================================================================
    with tab_trabajo:
        st.subheader("💼 Carrera Profesional")
        trabajo_actual = estado.get("trabajo_actual", "Desempleado")
        turnos_en_trabajo = estado.get("turnos_en_trabajo", 0)
        sueldo_base = mechanics.SALARIOS_BASE.get(trabajo_actual, 0)
        sueldo_real = int(sueldo_base * (1 + estado.get("habilidad_tecnica", 0) / 100.0))
        
        st.markdown(f"### Puesto Actual: **{trabajo_actual}**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Sueldo Base", f"${sueldo_base:,}")
        col2.metric("Sueldo Real (con bonus)", f"${sueldo_real:,}")
        col3.metric("Experiencia", f"{turnos_en_trabajo} meses")
        st.divider()
        
        st.markdown("**Acciones Rápidas:**")
        is_processing = st.session_state.get("procesando", False)
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("🔍 Buscar Trabajo", type="primary", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.intentar_buscar_trabajo(estado)
                if msg and msg.strip(): st.session_state.mensajes.append({"role": "assistant", "content": msg})
                estado["turno"] += 1
                st.session_state.procesando = False
                st.rerun()
        with col_b:
            if st.button("📈 Pedir Ascenso", type="primary", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.intentar_pedir_ascenso(estado)
                if msg and msg.strip(): st.session_state.mensajes.append({"role": "assistant", "content": msg})
                estado["turno"] += 1
                st.session_state.procesando = False
                st.rerun()
        with col_c:
            if st.button("📤 Renunciar", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.intentar_renunciar(estado)
                if msg and msg.strip(): st.session_state.mensajes.append({"role": "assistant", "content": msg})
                estado["turno"] += 1
                st.session_state.procesando = False
                st.rerun()

        st.divider()
        st.markdown("**📊 Progresión Laboral Interactiva:**")
        stats_jugador = {"reputacion": estado.get("reputacion", 0), "tecnica": estado.get("habilidad_tecnica", 0), "politica": estado.get("habilidad_politica", 0), "negocios": estado.get("habilidad_negocios", 0)}
        
        for cargo, reqs in mechanics.REQUISITOS_TRABAJO.items():
            if cargo == "Desempleado": continue
            cumple_todo = True
            faltantes = []
            if stats_jugador["reputacion"] < reqs["req_reputacion"]: cumple_todo = False; faltantes.append(f"Rep: {reqs['req_reputacion']}")
            if stats_jugador["tecnica"] < reqs["req_tecnica"]: cumple_todo = False; faltantes.append(f"Tec: {reqs['req_tecnica']}")
            if stats_jugador["politica"] < reqs["req_politica"]: cumple_todo = False; faltantes.append(f"Pol: {reqs['req_politica']}")
            if stats_jugador["negocios"] < reqs["req_negocios"]: cumple_todo = False; faltantes.append(f"Neg: {reqs['req_negocios']}")
            
            es_actual = (cargo == trabajo_actual)
            sueldo_cargo = mechanics.SALARIOS_BASE.get(cargo, 0)
            icono = "🟡" if es_actual else ("✅" if cumple_todo else "❌")
            color = "#d4af37" if es_actual else ("#2ecc71" if cumple_todo else "#e74c3c")
            estado_texto = "← ACTUAL" if es_actual else ("Disponible" if cumple_todo else "Bloqueado")
            
            st.markdown(f"""
            <div style="background-color: #1a1d24; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.2em;">{icono}</span>
                        <strong style="color: {color}; font-size: 1.1em;"> {cargo}</strong>
                        <span style="color: #888; margin-left: 10px;">${sueldo_cargo:,}/mes</span>
                        <span style="color: #666; margin-left: 10px; font-style: italic;">{estado_texto}</span>
                    </div>
            """, unsafe_allow_html=True)
            
            if not es_actual and cumple_todo:
                st.markdown(f"""
                    <div><button onclick="document.querySelector('textarea[aria-label*=\'Escribí\']').value='postularme a {cargo.lower()}'; document.querySelector('button[kind=\'primary\']').click();" style="background-color: #2ecc71; color: white; border: none; padding: 5px 15px; border-radius: 4px; cursor: pointer; font-weight: bold;">Postularme</button></div>
                """, unsafe_allow_html=True)
            elif not es_actual and not cumple_todo:
                st.markdown(f"""<div><span style="color: #e74c3c; font-size: 0.9em;">🔒 Requiere: {', '.join(faltantes)}</span></div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.divider()
        if trabajo_actual in mechanics.ASCENSOS_VALIDOS:
            proximo = mechanics.ASCENSOS_VALIDOS[trabajo_actual]
            reqs_p = mechanics.REQUISITOS_TRABAJO[proximo]
            st.markdown(f"### 🎯 Próximo Ascenso: **{proximo}**")
            st.markdown(f"- Experiencia: 6 meses (llevás {turnos_en_trabajo})")
            st.markdown(f"- Requisitos: Rep {reqs_p['req_reputacion']}, Tec {reqs_p['req_tecnica']}, Neg {reqs_p['req_negocios']}")
            if turnos_en_trabajo < 6:
                st.warning(f"⏳ Te faltan {6 - turnos_en_trabajo} meses de experiencia.")

    # =====================================================================
    # PESTAÑA GOBIERNO
    # =====================================================================
    with tab_gobierno:
        ui.render_tab_gobierno(estado)
        st.divider()
        if estado.get("cargo_politico") == "Ciudadano":
            st.subheader("🗳️ Ingresar a la Política")
            if st.button("🗳️ Postularme a Diputado", type="primary", use_container_width=True, disabled=st.session_state.get("procesando", False)):
                if estado.get("reputacion", 0) < 30:
                    st.session_state.mensajes.append({"role": "assistant", "content": f"❌ Necesitás al menos 30 de Reputación. Tenés {estado.get('reputacion', 50)}."})
                else:
                    ok, msg = mechanics.calcular_exito_campana(estado, "Diputado")
                    if ok:
                        estado["cargo_politico"] = "Diputado"
                        estado["turnos_en_poder"] = 0
                    st.session_state.mensajes.append({"role": "assistant", "content": msg})
                estado["turno"] += 1
                st.rerun()

    # =====================================================================
    # PESTAÑA EMPRESAS
    # =====================================================================
    with tab_empresas:
        ui.render_tab_empresas(estado)
        st.divider()
        st.subheader("🏢 Fundar Nueva Empresa")
        is_processing = st.session_state.get("procesando", False)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💻 Fundar Tech Startup\n(Costo: $250K | Req: 50 Negocios)", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.ejecutar_accion_determinista(estado, "fundar tech startup")
                if msg and msg[1]: st.session_state.mensajes.append({"role": "assistant", "content": msg[1]})
                estado["turno"] += 1; st.rerun()
        with col2:
            if st.button("🏠 Fundar Inmobiliaria\n(Costo: $500K | Req: 70 Negocios)", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.ejecutar_accion_determinista(estado, "fundar inmobiliaria")
                if msg and msg[1]: st.session_state.mensajes.append({"role": "assistant", "content": msg[1]})
                estado["turno"] += 1; st.rerun()
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("🏦 Fundar Banco\n(Costo: $1M | Req: 85 Negocios)", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.ejecutar_accion_determinista(estado, "fundar banco")
                if msg and msg[1]: st.session_state.mensajes.append({"role": "assistant", "content": msg[1]})
                estado["turno"] += 1; st.rerun()
        with col4:
            if st.button("📊 Fundar Consultora\n(Costo: $100K | Req: 30 Negocios)", use_container_width=True, disabled=is_processing):
                ok, msg = mechanics.ejecutar_accion_determinista(estado, "fundar consultora")
                if msg and msg[1]: st.session_state.mensajes.append({"role": "assistant", "content": msg[1]})
                estado["turno"] += 1; st.rerun()

    # =====================================================================
    # OTRAS PESTAÑAS
    # =====================================================================
    with tab_prensa:
        ui.render_tab_prensa(estado)
    with tab_rivales:
        ui.render_tab_rivales(estado)
    with tab_familia:
        ui.render_tab_familia(estado)
    with tab_objetivos:
        ui.render_tab_objetivos(estado)
    with tab_logros:
        ui.render_tab_logros(estado)
    with tab_graficos:
        ui.render_tab_graficos(estado)