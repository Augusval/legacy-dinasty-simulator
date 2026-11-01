import random
import streamlit as st
import prompts
import mechanics
import ui
from state import parse_estado, IDEOLOGIAS, OBJETIVOS_DINASTICOS
from data import CRISIS_DECISIONES, TEMAS_DEBATE, NOMBRES_PILA

st.set_page_config(page_title="LEGACY", layout="wide", page_icon="📰")
ui.inyectar_css()
st.title("LEGACY - Crónicas Dinásticas")

MAX_MENSAJES_CHAT = 8

def procesar_accion_jugador(texto):
    """Procesa una acción del jugador, valida intención y actualiza el estado."""
    # 1. Validación básica contra inyección de prompts
    ok, motivo = mechanics.sanitizar_accion(texto)
    if not ok:
        st.error(motivo)
        return

    # 2. Clasificación semántica de intención con IA
    intencion = prompts.clasificar_intencion(texto)
    if not intencion.get("es_valida", True):
        st.warning("🚫 Acción inválida: El Game Master no entiende esa acción o rompe las reglas del mundo.")
        return

    # 3. Agregar la acción al chat
    st.session_state.mensajes.append({"role": "user", "content": f"🎯 Tu acción: {texto}"})

    # 4. Llamar al Game Master y procesar la respuesta (capturando los 3 valores)
    with st.spinner("El Game Master está simulando..."):
        res = prompts.llamar_llm([{"texto": texto}], 7, " ")
        nuevo_estado, narrativa, game_over = mechanics.procesar_respuesta(
            res, 7, [{"texto": texto}], es_inicio=False, estado=st.session_state.estado
        )
        
        # 5. Actualizar el estado y el chat
        st.session_state.estado = nuevo_estado
        st.session_state.mensajes.append({"role": "assistant", "content": narrativa})
        
        # 6. Si hay game over, lo guardamos
        if game_over:
            st.session_state.game_over = game_over
        
        # 7. Detectar nuevos logros y objetivos completados
        logros_anteriores = set(st.session_state.estado.get("logros", []))
        logros_nuevos = set(nuevo_estado.get("logros", [])) - logros_anteriores
        if logros_nuevos:
            for logro in logros_nuevos:
                st.toast(f"🏆 Logro desbloqueado: {logro}", icon="🎖️")
        
        objetivos_anteriores = set(st.session_state.estado.get("objetivos_completados", []))
        objetivos_nuevos = set(nuevo_estado.get("objetivos_completados", [])) - objetivos_anteriores
        if objetivos_nuevos:
            for obj in objetivos_nuevos:
                st.toast(f"🎯 Objetivo cumplido: {obj}", icon="✨")

    st.rerun()


# ==========================================
# PANTALLA DE INICIO (CREACIÓN DE PERSONAJE)
# ==========================================
if not st.session_state.get("juego_iniciado", False):
    st.markdown("## El Comienzo de una Dinastía")
    hof = mechanics.leer_hall_of_fame()
    if hof:
        with st.expander("🏛️ Salón de la Fama Dinástico"):
            for i, entry in enumerate(hof[:5], 1):
                st.markdown(
                    f"{i}. Dinastía {entry['apellido']} · Rango {entry['rango']} · "
                    f"{entry['puntos']:,} pts · {entry['generaciones']} gen. · {entry['cargo']}"
                )

    # Generar nombres aleatorios UNA SOLA VEZ al cargar la pantalla
    if "nombre_inicial" not in st.session_state:
        APELLIDOS_ARGENTINOS = [
            "González", "Rodríguez", "Gómez", "Fernández", "López", 
            "Martínez", "Sánchez", "Pérez", "García", "Romero", 
            "Díaz", "Álvarez", "Moreno", "Muñoz", "Alonso", 
            "Gutiérrez", "Navarro", "Torres", "Domínguez", "Vázquez"
        ]
        st.session_state.nombre_inicial = random.choice(NOMBRES_PILA)
        st.session_state.apellido_inicial = f"Dinastía {random.choice(APELLIDOS_ARGENTINOS)}"

    with st.form("create_game"):
        nombre = st.text_input("Nombre:", value=st.session_state.nombre_inicial)
        apellido = st.text_input("Apellido de la Dinastía:", value=st.session_state.apellido_inicial)
        genero = st.selectbox("Género del personaje:", ["Masculino", "Femenino"])
        origen = st.selectbox("Origen:", ["Técnico", "Político", "Comerciante"])
        ideologia = st.selectbox("Ideología Política:", IDEOLOGIAS)
        historia = (
            "Soy un ciudadano." if origen == "Técnico"
            else "Soy un político." if origen == "Político"
            else "Soy un empresario."
        )
        rasgo = st.selectbox("Rasgo:", ["Carismático", "Mente Fría", "Trabajador"])
        
        st.markdown("### Objetivos Dinásticos (elegí hasta 3)")
        objetivos_seleccionados = st.multiselect(
            "¿Qué querés lograr con tu dinastía?",
            OBJETIVOS_DINASTICOS,
            max_selections=3,
        )

        if st.form_submit_button("Comenzar", type="primary"):
            # Limpiamos las variables para que la PRÓXIMA partida tenga nombres nuevos
            if "nombre_inicial" in st.session_state:
                del st.session_state.nombre_inicial
            if "apellido_inicial" in st.session_state:
                del st.session_state.apellido_inicial
            
            st.session_state.juego_iniciado = True
            st.session_state.game_over = None
            st.session_state.mensajes = []
            st.session_state.hof_guardado = False
            st.session_state.tutorial_visto = False
            st.session_state.sistema = prompts.construir_sistema(nombre, 24, historia, rasgo, origen, ideologia)
            
            estado_inicial = parse_estado(
                {
                    "rasgo": rasgo,
                    "edad": 24,
                    "genero": genero,
                    "origen": origen,
                    "ideologia": ideologia,
                    "apellido_dinastia": apellido,
                    "objetivos_dinasticos": objetivos_seleccionados,
                }
            )
            for faccion, delta in mechanics.IDEOLOGIA_MODIFICADORES.get(ideologia, {}).items():
                actual = estado_inicial["facciones"].get(faccion, 50)
                estado_inicial["facciones"][faccion] = max(0, min(100, actual + delta))
            
            st.session_state.estado = estado_inicial

            with st.spinner("Imprimiendo la primera edición..."):
                res = prompts.llamar_llm([], 7, " ", es_inicio=True)
                nuevo_estado, narrativa, game_over = mechanics.procesar_respuesta(
                    res, 7, [], es_inicio=True, estado=st.session_state.estado
                )
                st.session_state.estado = nuevo_estado
                st.session_state.mensajes.append({"role": "assistant", "content": narrativa})
                if game_over:
                    st.session_state.game_over = game_over
            
            st.toast("🎉 ¡Partida iniciada! Bienvenido a LEGACY.", icon="🏛️")
            st.rerun()

# ==========================================
# PANTALLA DE JUEGO
# ==========================================
else:
    if "estado" not in st.session_state:
        st.session_state.juego_iniciado = False
        st.rerun()
    
    # Inicializar variable de tutorial si no existe
    if "tutorial_visto" not in st.session_state:
        st.session_state.tutorial_visto = False
    
    estado = st.session_state.estado

    # --- TUTORIAL INTERACTIVO (primera vez) ---
    if not st.session_state.tutorial_visto and estado.get("turno", 0) <= 1:
        st.markdown(
            """
            <div class="tutorial-box">
                <h2>🎮 Bienvenido a LEGACY</h2>
                <p><strong>Tu misión:</strong> Construir una dinastía política y empresarial que perdure generaciones.</p>
                <h3>📋 Mecánicas Clave:</h3>
                <ul>
                    <li><strong>💬 Chat con el Game Master:</strong> Escribí acciones en lenguaje natural (ej: "Buscar trabajo", "Pedir aumento", "Mudarme a una casa mejor").</li>
                    <li><strong>💼 Carrera Laboral:</strong> Ascendé de Junior a CEO. Pedí aumentos con cuidado (tienen cooldown).</li>
                    <li><strong>🏠 Calidad de Vida:</strong> Mejora tu vivienda para ganar felicidad, pero aumenta tu costo de vida.</li>
                    <li><strong>🏢 Empresas:</strong> Fundá corporaciones. Crecen solas, pero invertí para acelerar su nivel.</li>
                    <li><strong>⏳ Tiempo:</strong> Cada acción avanza 1 semana. Usá "Dejar pasar el tiempo" para saltar períodos.</li>
                    <li><strong>🗳️ Carrera Política:</strong> Ciudadano → Diputado → Gobernador → Presidente.</li>
                </ul>
                <p><em>Este tutorial no volverá a aparecer. ¡Buena suerte!</em></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("✅ Entendido, comenzar partida", type="primary"):
            st.session_state.tutorial_visto = True
            st.rerun()
        st.stop()

    # --- GAME OVER / LEGADO ---
    if st.session_state.get("game_over"):
        st.error(st.session_state.game_over)
        st.subheader("⚰️ El Fin de una Era")
        
        puntos, rango = mechanics.calcular_legado(estado)
        
        if not st.session_state.get("hof_guardado", False):
            mechanics.guardar_hall_of_fame(puntos, rango, estado)
            st.session_state.hof_guardado = True
            
        st.markdown(f"### Rango de Legado: **{rango}** ({puntos} pts)")
        st.write(f"Generación: **{estado.get('generacion_actual', 1)}**")
        st.write(f"Viviste {int(estado.get('edad', 24))} años. Alcanzaste el cargo de **{estado.get('cargo_politico')}**.")
        st.write(f"Dejaste un patrimonio de ${estado.get('dinero_personal', 0):,}.")
        
        if estado.get("objetivos_completados"):
            st.markdown("**🎯 Objetivos dinásticos cumplidos:**")
            for obj in estado["objetivos_completados"]:
                st.success(f"✓ {obj}")
                
        if estado.get("logros"):
            st.markdown("**🏆 Logros obtenidos:**")
            for logro in estado["logros"]:
                st.success(f"✓ {logro}")
                
        biografia = mechanics.generar_biografia(estado)
        st.download_button(
            "📜 Descargar Biografía de la Dinastía",
            data=biografia,
            file_name=f"legado_{estado.get('apellido_dinastia', 'dinastia').lower()}.txt",
            mime="text/plain",
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👑 Continuar Dinastía", type="primary") and estado.get("hijos"):
                nuevo_estado, mensaje = mechanics.continuar_dinastia(estado)
                if nuevo_estado:
                    st.session_state.estado = nuevo_estado
                    st.session_state.game_over = None
                    st.session_state.hof_guardado = False
                    st.session_state.mensajes.append({"role": "assistant", "content": mensaje})
                    st.rerun()
                else:
                    st.error(mensaje)
        with col2:
            if st.button("🔄 Nueva Partida"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        st.stop()

    # --- CABECERA CON FECHA ---
    ui.render_cabecera(estado)

    # --- SIDEBAR ---
    ui.render_sidebar(estado, mechanics)

    # --- PESTAÑAS PRINCIPALES ---
    tab_cronicas, tab_campaña, tab_gobierno, tab_empresas, tab_vida, tab_rivales, tab_archivo, tab_graficos = st.tabs(
        [
            "Portada", "Campaña Política", "Despacho Presidencial",
            "Imperio Corporativo", "Vida y Familia", "Rivales",
            "Archivo Histórico", "Gráficos",
        ]
    )

    # ==========================================
    # PESTAÑA: PORTADA (CHAT CON EL GAME MASTER)
    # ==========================================
    with tab_cronicas:
        ui.render_titular(estado)
        ui.render_resumen_turno(estado)
        ui.render_objetivos(estado)

        if estado.get("turno", 0) <= 1:
            st.info(
                "👋 **Bienvenido a LEGACY.** Escribí tus acciones en el chat de abajo "
                "(ej: *'Buscar trabajo en una consultora'*, *'Pedir ascenso a Gerente'*, *'Mudarme a una casa con pileta'*). "
                "Cada acción avanza 1 semana. Cuidá tu **energía** y tu **salud**: si colapsás, terminás hospitalizado. "
                "Cuando mueras, tu heredero continuará la dinastía."
            )

        mensajes_visibles = st.session_state.mensajes[-MAX_MENSAJES_CHAT:]
        if len(st.session_state.mensajes) > MAX_MENSAJES_CHAT:
            st.caption(f"📜 Mostrando los últimos {MAX_MENSAJES_CHAT} mensajes. El resto está en el Archivo Histórico.")

        with st.container(height=500):
            for msg in mensajes_visibles:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # --- HOSPITALIZACIÓN BLOQUEANTE ---
        if estado.get("hospitalizado"):
            st.divider()
            st.error("🏥 **ESTÁS HOSPITALIZADO.** Tu cuerpo colapsó por el desgaste. Debés recuperarte antes de volver a actuar.")
            if st.button("🛌 Recuperarme (30 días de internación)", type="primary"):
                st.session_state.mensajes.append({"role": "user", "content": "🏥 *(Pasás 30 días internado recuperándote.)*"})
                with st.spinner("Recuperándote..."):
                    res = prompts.llamar_llm([], 30, "El jugador está hospitalizado recuperándose.")
                    nuevo_estado, narrativa, game_over = mechanics.procesar_respuesta(res, 30, [{"texto": "descansar y recuperarse en el hospital"}], es_inicio=False, estado=st.session_state.estado)
                    st.session_state.estado = nuevo_estado
                    st.session_state.mensajes.append({"role": "assistant", "content": narrativa})
                    if game_over:
                        st.session_state.game_over = game_over
                st.rerun()
            st.stop()

        # --- MINI-JUEGO: LICITACIÓN TURBIA ---
        if estado.get("licitacion_activa"):
            lic = estado["licitacion_activa"]
            st.divider()
            st.error(f"🎮 **MINI-JUEGO: {lic.get('titulo', 'LICITACIÓN TURBIA')}**")
            st.write(lic.get("desc", ""))
            st.write(f"Monto máximo disponible: **${lic.get('monto_max', 0):,}**")
            st.write(f"Riesgo base de ser descubierto: **{lic.get('riesgo_base', 0)}%**")
            
            monto = st.slider(
                "¿Cuánto pedís/aceptás?",
                min_value=0,
                max_value=lic.get("monto_max", 1000000),
                value=lic.get("monto_elegido", 0),
                step=10000,
                key="slider_licitacion"
            )
            riesgo_calculado = lic.get("riesgo_base", 0) + (monto / lic.get("monto_max", 1000000)) * 30
            st.warning(f"⚠️ **Riesgo de escándalo: {int(riesgo_calculado)}%**")
            st.caption("Cuanto más pedís, más plata pero más riesgo de que salga en los medios.")
            
            col1, col2 = st.columns(2)
            if col1.button("✅ Aceptar monto", type="primary"):
                st.session_state.estado["dinero_personal"] += monto
                st.session_state.estado["nivel_corrupcion"] = min(100, st.session_state.estado["nivel_corrupcion"] + int(riesgo_calculado / 2))
                st.session_state.estado["escandalo_acumulado"] = min(100, st.session_state.estado["escandalo_acumulado"] + int(riesgo_calculado))
                if random.randint(1, 100) <= int(riesgo_calculado):
                    st.session_state.estado["reputacion"] = max(0, st.session_state.estado["reputacion"] - 20)
                    st.session_state.estado["opinion_publica"] = max(0, st.session_state.estado["opinion_publica"] - 15)
                    st.error(f"📰 **TE DESCUBRIERON:** Perdiste 20 de reputación y 15 de opinión pública.")
                else:
                    st.success(f"💰 **Operación exitosa:** +${monto:,} a tu fortuna.")
                st.session_state.estado["licitacion_activa"] = {}
                st.rerun()
            if col2.button("❌ Rechazar"):
                st.session_state.estado["reputacion"] = min(100, st.session_state.estado["reputacion"] + 5)
                st.success("Rechazaste la oferta corrupta. +5 reputación.")
                st.session_state.estado["licitacion_activa"] = {}
                st.rerun()
            st.stop()

        # --- MINI-JUEGO: CRISIS EN 3 TURNOS ---
        if estado.get("crisis_minijuego"):
            crisis = estado["crisis_minijuego"]
            st.divider()
            st.error(f"🎮 **MINI-JUEGO: CRISIS {crisis.get('tipo', 'FINANCIERA')}**")
            st.write(f"Turno {crisis.get('turno_actual', 1)} de 3")
            tipo_crisis = crisis.get("tipo", "financiera")
            if tipo_crisis in CRISIS_DECISIONES:
                decisiones = CRISIS_DECISIONES[tipo_crisis]
                turno_actual = crisis.get("turno_actual", 1)
                if turno_actual <= len(decisiones):
                    decision = decisiones[turno_actual - 1]
                    st.write(decision["desc"])
                    cols = st.columns(len(decision["opciones"]))
                    for i, opcion in enumerate(decision["opciones"]):
                        if cols[i].button(opcion["texto"], key=f"crisis_op_{turno_actual}_{i}"):
                            for efecto, valor in opcion["efecto"].items():
                                if efecto in st.session_state.estado:
                                    if isinstance(valor, int):
                                        st.session_state.estado[efecto] = max(0, st.session_state.estado[efecto] + valor)
                                elif efecto in st.session_state.estado.get("facciones", {}):
                                    st.session_state.estado["facciones"][efecto] = max(0, min(100, st.session_state.estado["facciones"][efecto] + valor))
                            crisis["decisiones"].append(opcion["texto"])
                            crisis["turno_actual"] += 1
                            if crisis["turno_actual"] > 3:
                                st.success("✅ Crisis resuelta. Las consecuencias se aplicaron.")
                                st.session_state.estado["crisis_minijuego"] = {}
                            else:
                                st.session_state.estado["crisis_minijuego"] = crisis
                            st.rerun()
            st.stop()

        # --- VENTANA DE DECISIÓN BLOQUEANTE ---
        if estado.get("evento_decision"):
            st.divider()
            ev = estado["evento_decision"]
            st.error(f"⚠️ **EVENTO CRÍTICO: {ev.get('titulo')}**\n\n{ev.get('desc')}")
            col1, col2 = st.columns(2)
            if col1.button(ev["opA"], use_container_width=True, key="ev_opA"):
                op = ev["opA"].lower()
                if "soborno" in op or "pagar" in op or "coima" in op:
                    if st.session_state.estado["dinero_personal"] >= 50000:
                        st.session_state.estado["dinero_personal"] -= 50000
                    else:
                        st.session_state.estado["dinero_personal"] = 0
                        st.session_state.estado["salud_mental"] = max(0, st.session_state.estado["salud_mental"] - 10)
                elif "aceptar" in op:
                    st.session_state.estado["dinero_personal"] += 200000
                    st.session_state.estado["nivel_corrupcion"] = min(100, st.session_state.estado["nivel_corrupcion"] + 15)
                    st.session_state.estado["escandalo_acumulado"] = min(100, st.session_state.estado["escandalo_acumulado"] + 20)
                elif "fuerza" in op:
                    st.session_state.estado["estabilidad_pais"] = max(0, st.session_state.estado["estabilidad_pais"] - 10)
                elif "ee.uu" in op:
                    st.session_state.estado["relaciones_internacionales"]["EE.UU."] = min(100, st.session_state.estado["relaciones_internacionales"]["EE.UU."] + 10)
                    st.session_state.estado["relaciones_internacionales"]["China"] = max(0, st.session_state.estado["relaciones_internacionales"]["China"] - 10)
                elif "inyectar" in op:
                    st.session_state.estado["tesoro_nacional"] -= 1000000
                    st.session_state.estado["aprobacion_publica"] = min(100, st.session_state.estado["aprobacion_publica"] + 10)
                st.session_state.estado["evento_decision"] = {}
                st.rerun()
            if col2.button(ev["opB"], use_container_width=True, key="ev_opB"):
                op = ev["opB"].lower()
                if "negar" in op:
                    st.session_state.estado["reputacion"] = max(0, st.session_state.estado["reputacion"] - 10)
                elif "rechazar" in op:
                    st.session_state.estado["reputacion"] = min(100, st.session_state.estado["reputacion"] + 5)
                elif "dialogar" in op:
                    if st.session_state.estado["dinero_personal"] >= 50000:
                        st.session_state.estado["dinero_personal"] -= 50000
                    else:
                        st.session_state.estado["facciones"]["Sindicatos"] = max(0, st.session_state.estado["facciones"].get("Sindicatos", 50) - 10)
                elif "china" in op:
                    st.session_state.estado["relaciones_internacionales"]["China"] = min(100, st.session_state.estado["relaciones_internacionales"].get("China", 50) + 10)
                    st.session_state.estado["relaciones_internacionales"]["EE.UU."] = max(0, st.session_state.estado["relaciones_internacionales"].get("EE.UU.", 50) - 10)
                elif "nada" in op:
                    st.session_state.estado["aprobacion_publica"] = max(0, st.session_state.estado["aprobacion_publica"] - 15)
                st.session_state.estado["evento_decision"] = {}
                st.rerun()
            st.warning("Debés tomar una decisión para continuar.")
            st.stop()

        # --- CRISIS ACTIVA VISIBLE ---
        if estado.get("crisis_activa"):
            c = estado["crisis_activa"]
            st.warning(f"🚨 **CRISIS NACIONAL ACTIVA: {c['tipo']}** — {c['desc']} *(restan {c['duracion']} meses)*")

        # --- AGOTAMIENTO ---
        if estado.get("energia", 100) < 10:
            st.warning("😮‍💨 **Estás agotado:** tus acciones rinden la mitad y tu salud física se deteriora. Descansá.")

        st.divider()

        # --- SUGERENCIAS DEL GAME MASTER ---
        sugeridas = estado.get("acciones_sugeridas", [])
        if sugeridas:
            st.markdown("**💡 Sugerencias del Game Master:**")
            cols = st.columns(min(3, len(sugeridas)))
            for i, sug in enumerate(sugeridas[:3]):
                if cols[i].button(sug, key=f"sug_{i}", use_container_width=True):
                    procesar_accion_jugador(sug)

        # --- DEJAR PASAR EL TIEMPO SIN ACTUAR ---
        with st.expander("⏳ Dejar pasar el tiempo (sin realizar acciones)"):
            salto = st.selectbox(
                "Tiempo a simular:",
                [7, 30, 90, 365],
                format_func=lambda x: f"{x} días",
                key="sel_salto",
            )
            if st.button("⏭️ AVANZAR TIEMPO", type="primary", key="btn_avanzar"):
                st.session_state.mensajes.append(
                    {"role": "user", "content": f"⏳ *(Dejás pasar {salto} días sin realizar acciones.)*"}
                )
                with st.spinner("Simulando..."):
                    res = prompts.llamar_llm([], salto, "El jugador deja pasar el tiempo.")
                    nuevo_estado, narrativa, game_over = mechanics.procesar_respuesta(res, salto, [], es_inicio=False, estado=st.session_state.estado)
                    st.session_state.estado = nuevo_estado
                    st.session_state.mensajes.append({"role": "assistant", "content": narrativa})
                    if game_over:
                        st.session_state.game_over = game_over
                st.rerun()

        # --- CHAT LIBRE CON EL GAME MASTER ---
        accion = st.chat_input(
            "Escribí tu acción... ej: 'Pedir ascenso a Director', 'Mudarme a una mansión', 'Fundar una empresa de tecnología'"
        )
        if accion:
            procesar_accion_jugador(accion)

    # ==========================================
    # PESTAÑA: CAMPAÑA POLÍTICA
    # ==========================================
    with tab_campaña:
        st.subheader("Campaña Electoral")
        
        # MINI-JUEGO: DEBATE ELECTORAL
        if estado.get("debate_activo"):
            debate = estado["debate_activo"]
            st.divider()
            st.error("🎮 **MINI-JUEGO: DEBATE ELECTORAL**")
            st.write("Elegí tu postura para cada tema:")
            tema_idx = debate.get("tema_actual", 0)
            if tema_idx < len(TEMAS_DEBATE):
                tema = TEMAS_DEBATE[tema_idx]
                st.markdown(f"### Tema {tema_idx + 1}: {tema['tema']}")
                cols = st.columns(3)
                for i, postura in enumerate(tema["posturas"]):
                    if cols[i].button(f"{postura['nombre']}\n{postura['desc']}", key=f"debate_t{tema_idx}_p{i}"):
                        for efecto, valor in postura["efecto"].items():
                            if efecto in st.session_state.estado:
                                if isinstance(valor, int):
                                    st.session_state.estado[efecto] = max(0, min(100, st.session_state.estado[efecto] + valor))
                            elif efecto in st.session_state.estado.get("facciones", {}):
                                st.session_state.estado["facciones"][efecto] = max(0, min(100, st.session_state.estado["facciones"][efecto] + valor))
                        debate["tema_actual"] = tema_idx + 1
                        debate["posturas_elegidas"].append(postura["nombre"])
                        if tema_idx + 1 >= len(TEMAS_DEBATE):
                            st.success("✅ Debate completado. Las posturas se aplicaron.")
                            st.session_state.estado["debate_activo"] = {}
                        else:
                            st.session_state.estado["debate_activo"] = debate
                        st.rerun()
            st.stop()

        if estado.get("campaña_activa"):
            st.info(f"🗳️ **CAMPAÑA EN CURSO para {estado.get('cargo_objetivo')}**")
            st.write(f"Fondo de campaña actual: **${estado.get('fondo_campaña', 0):,}**")
            c1, c2 = st.columns(2)
            if c1.button("Invertir $50k en Publicidad (+Opinión)"):
                if estado["dinero_personal"] >= 50000:
                    st.session_state.estado["dinero_personal"] -= 50000
                    st.session_state.estado["fondo_campaña"] += 50000
                    st.session_state.estado["opinion_publica"] = min(100, estado["opinion_publica"] + 3)
                    st.rerun()
            if c2.button("Invertir $50k en Actos (+Reputación)"):
                if estado["dinero_personal"] >= 50000:
                    st.session_state.estado["dinero_personal"] -= 50000
                    st.session_state.estado["fondo_campaña"] += 50000
                    st.session_state.estado["reputacion"] = min(100, estado["reputacion"] + 3)
                    st.rerun()
            if st.button("🎙️ INICIAR DEBATE (Mini-juego)", type="primary"):
                st.session_state.estado["debate_activo"] = {
                    "tema_actual": 0,
                    "posturas_elegidas": [],
                }
                st.rerun()
            if st.button("🎯 CERRAR CAMPAÑA Y CONOCER EL RESULTADO"):
                exito, msj = mechanics.resolver_eleccion(estado["cargo_objetivo"], estado)
                if exito:
                    st.balloons()
                    st.toast("🏆 ¡Victoria electoral! Felicitaciones.", icon="🎉")
                    st.success(msj)
                else:
                    st.toast("😔 Derrota electoral. Seguí intentando.", icon="💪")
                    st.error(msj)
                st.rerun()
        else:
            if estado.get("cargo_politico") == "Ciudadano":
                if st.button("Lanzar Campaña a Diputado"):
                    st.session_state.estado["campaña_activa"] = True
                    st.session_state.estado["cargo_objetivo"] = "Diputado"
                    st.rerun()
            elif estado.get("cargo_politico") == "Diputado":
                if st.button("Lanzar Campaña a Gobernador"):
                    st.session_state.estado["campaña_activa"] = True
                    st.session_state.estado["cargo_objetivo"] = "Gobernador"
                    st.rerun()
            elif estado.get("cargo_politico") == "Gobernador":
                if st.button("Lanzar Campaña Presidencial"):
                    st.session_state.estado["campaña_activa"] = True
                    st.session_state.estado["cargo_objetivo"] = "Presidente"
                    st.rerun()
            else:
                st.success("Estás en la cima del poder. Disfrutá tu mandato.")
                
        st.divider()
        st.markdown("### 🗺️ Resultado por Provincia (última elección)")
        ui.render_mapa_electoral(estado)

    # ==========================================
    # PESTAÑA: DESPACHO PRESIDENCIAL
    # ==========================================
    with tab_gobierno:
        ui.render_tab_gobierno(estado)

    # ==========================================
    # PESTAÑA: IMPERIO CORPORATIVO
    # ==========================================
    with tab_empresas:
        ui.render_tab_empresas(estado)

    # ==========================================
    # PESTAÑA: VIDA Y FAMILIA
    # ==========================================
    with tab_vida:
        ui.render_tab_vida(estado)

    # ==========================================
    # PESTAÑA: RIVALES
    # ==========================================
    with tab_rivales:
        ui.render_tab_rivales(estado)

    # ==========================================
    # PESTAÑA: ARCHIVO HISTÓRICO
    # ==========================================
    with tab_archivo:
        ui.render_tab_archivo(estado)

    # ==========================================
    # PESTAÑA: GRÁFICOS
    # ==========================================
    with tab_graficos:
        ui.render_tab_graficos(estado)