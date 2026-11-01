import streamlit as st
import plotly.graph_objects as go
from entidades import Empresa, Hijo, Ministro, Medio, Rival

# ==============================================================================
# ESTILOS Y TEMA VISUAL (CSS)
# ==============================================================================

def inyectar_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0a0c10; color: #e0e0e0; font-family: 'Georgia', serif; }
        h1, h2, h3 { color: #d4af37 !important; font-weight: bold; letter-spacing: 1px; }
        .stButton>button { background-color: #d4af37; color: #0a0c10; font-weight: bold; border: none; border-radius: 4px; }
        .stButton>button:hover { background-color: #f1c40f; color: #000; }
        .stChatInput { background-color: #1a1d24; border: 1px solid #d4af37; }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# CABECERA
# ==============================================================================

def render_cabecera(estado: dict):
    mes = int(estado.get("edad", 24) * 12)
    anio = 2026 + (mes // 12)
    mes_nombre = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][mes % 12]
    
    st.markdown(f"<div style='text-align: right; color: #888; font-size: 0.9em;'>{mes_nombre} {anio} | Turno {estado.get('turno', 0)}</div>", unsafe_allow_html=True)
    
    titular = estado.get("titular_periodico", "La calma precede a la tormenta...")
    st.markdown(f"""
    <div style="background-color: #1a1d24; padding: 15px; border-top: 2px solid #e63946; border-bottom: 2px solid #e63946; margin-bottom: 20px;">
        <h3 style="margin: 0; color: #fff; font-style: italic;">📰 {titular}</h3>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR (con FIX del bug de energía > 100)
# ==============================================================================

def render_sidebar(estado: dict):
    with st.sidebar:
        st.title(f"Dinastía {estado.get('apellido_dinastia', '')}")
        st.markdown(f"**{estado.get('nombre', '')}** | {estado.get('cargo_politico', 'Ciudadano')}")
        st.divider()

        st.subheader("👤 Estado Personal")
        col1, col2 = st.columns(2)
        col1.metric("Edad", f"{int(estado.get('edad', 24))} años")
        
        # FIX: Formatear dinero grande para que no se corte
        dinero = estado.get('dinero_personal', 0)
        if dinero >= 1000000:
            dinero_texto = f"${dinero/1000000:.2f}M"
        elif dinero >= 1000:
            dinero_texto = f"${dinero/1000:.0f}K"
        else:
            dinero_texto = f"${dinero:,}"
        col2.metric("Dinero", dinero_texto)
        
        # FIX: Usar min(1.0, valor/100) para que st.progress no explote
        energia = estado.get("energia", 100)
        st.progress(min(1.0, energia / 100), text=f"⚡ Energía: {energia}%")
        
        salud_fisica = estado.get("salud_fisica", 100)
        st.progress(min(1.0, salud_fisica / 100), text=f"❤️ Salud Física: {salud_fisica}%")
        
        salud_mental = estado.get("salud_mental", 100)
        st.progress(min(1.0, salud_mental / 100), text=f"🧠 Salud Mental: {salud_mental}%")
        
        st.subheader("🏛️ Poder e Influencia")
        reputacion = estado.get("reputacion", 50)
        st.progress(min(1.0, reputacion / 100), text=f"🎩 Reputación: {reputacion}")
        
        aprobacion = estado.get("aprobacion_publica", 50)
        st.progress(min(1.0, aprobacion / 100), text=f"👍 Aprobación: {aprobacion}%")
        
        escandalo = estado.get("nivel_escandalo", 0)
        color_escandalo = "#e63946" if escandalo > 50 else "#888"
        st.markdown(f"<div style='color: {color_escandalo}; font-weight: bold;'>🚨 Nivel de Escándalo: {escandalo}%</div>", unsafe_allow_html=True)
        st.progress(min(1.0, escandalo / 100))

        st.divider()
        st.subheader("📊 Habilidades")
        st.progress(min(1.0, estado.get("habilidad_tecnica", 20) / 100), text=f"💻 Técnica: {estado.get('habilidad_tecnica', 20)}")
        st.progress(min(1.0, estado.get("habilidad_politica", 20) / 100), text=f"🗳️ Política: {estado.get('habilidad_politica', 20)}")
        st.progress(min(1.0, estado.get("habilidad_negocios", 20) / 100), text=f"💼 Negocios: {estado.get('habilidad_negocios', 20)}")

        st.divider()
        st.subheader("🤝 Facciones")
        facciones = estado.get("facciones", {})
        for fac, val in facciones.items():
            st.progress(min(1.0, val / 100), text=f"{fac}: {val}")

# ==============================================================================
# PESTAÑAS DE CONTENIDO
# ==============================================================================

def render_tab_gobierno(estado: dict):
    st.subheader("🏛️ Gabinete de Gobierno")
    ministros = estado.get("ministros", {})
    
    if not ministros:
        st.info("📭 Aún no has nombrado ministros. Esta sección se desbloquea al asumir un cargo de poder.")
        return
        
    for area, m in ministros.items():
        nombre = m.nombre if hasattr(m, 'nombre') else m.get('nombre', 'Desconocido')
        eficiencia = m.eficiencia if hasattr(m, 'eficiencia') else m.get('eficiencia', 50)
        lealtad = m.lealtad if hasattr(m, 'lealtad') else m.get('lealtad', 50)
        corrupcion = m.corrupcion if hasattr(m, 'corrupcion') else m.get('corrupcion', 0)
        
        with st.expander(f"👤 {nombre} - Ministro de {area}"):
            st.progress(min(1.0, eficiencia/100), text=f"⚙️ Eficiencia: {eficiencia}%")
            st.progress(min(1.0, lealtad/100), text=f"🤝 Lealtad: {lealtad}%")
            st.progress(min(1.0, corrupcion/100), text=f"💰 Corrupción: {corrupcion}%")

def render_tab_empresas(estado: dict):
    st.subheader("🏢 Imperio Corporativo")
    corporaciones = estado.get("corporaciones", {})
    
    if not corporaciones:
        st.info("📉 No posees empresas. Fundá una desde el panel inferior.")
        return
        
    for key, emp in corporaciones.items():
        nombre = emp.nombre if hasattr(emp, 'nombre') else emp.get('nombre', key)
        nivel = emp.nivel if hasattr(emp, 'nivel') else emp.get('nivel', 1)
        progreso = emp.progreso_nivel if hasattr(emp, 'progreso_nivel') else emp.get('progreso_nivel', 0)
        
        st.markdown(f"### {nombre}")
        st.metric(label="Nivel Actual", value=f"Nivel {nivel}")
        st.progress(min(1.0, progreso/100), text=f"Progreso al Nivel {nivel + 1}: {progreso}%")
        st.divider()

def render_tab_prensa(estado: dict):
    st.subheader("📰 Medios de Comunicación")
    medios = estado.get("medios", [])
    
    if not medios:
        st.info("No hay medios operando.")
        return
        
    for m in medios:
        nombre = m.nombre if hasattr(m, 'nombre') else m.get('nombre', 'Medio')
        apoyo = m.apoyo if hasattr(m, 'apoyo') else m.get('apoyo', 50)
        postura = m.postura if hasattr(m, 'postura') else m.get('postura', 'Neutro')
        
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.markdown(f"**{nombre}**")
        col2.caption(f"Postura: {postura}")
        
        color = "green" if apoyo > 20 else ("red" if apoyo < -20 else "gray")
        col3.markdown(f"<div style='color: {color}; font-weight: bold; text-align: right;'>Apoyo: {apoyo}</div>", unsafe_allow_html=True)

def render_tab_rivales(estado: dict):
    st.subheader("⚔️ Rivales Políticos")
    rivales = estado.get("rivales", [])
    
    if not rivales:
        st.success("✨ No tenés rivales conocidos. ¡Disfrutá la calma!")
        return
        
    for r in rivales:
        nombre = r.nombre if hasattr(r, 'nombre') else r.get('nombre', 'Rival')
        poder = r.poder if hasattr(r, 'poder') else r.get('poder', 30)
        secretos = r.secretos if hasattr(r, 'secretos') else r.get('secretos', [])
        
        with st.expander(f"🕴️ {nombre}"):
            st.progress(min(1.0, poder/100), text=f"Poder Político: {poder}%")
            if secretos:
                st.warning(f"🤫 **Secreto conocido:** {secretos[0]}")
            else:
                st.info("No se conocen secretos de este rival.")

def render_tab_vida(estado: dict):
    st.subheader("👨‍👩‍👧‍👦 Vida y Familia")
    st.write(f"**Pareja:** {estado.get('pareja_nombre', 'Soltero/a')} (Afinidad: {estado.get('pareja_afinidad', 0)}%)")
    st.divider()
    
    hijos = estado.get("hijos", [])
    if not hijos:
        st.info("Aún no tenés herederos.")
        return
        
    for h in hijos:
        nombre = h.nombre if hasattr(h, 'nombre') else h.get('nombre', 'Hijo')
        edad = h.edad if hasattr(h, 'edad') else h.get('edad', 0)
        potencial = h.calcular_potencial_heredero() if hasattr(h, 'calcular_potencial_heredero') else 50
        
        col1, col2 = st.columns(2)
        col1.metric(nombre, f"{edad} años")
        col2.metric("Potencial de Heredero", f"{potencial}/100")

def render_tab_objetivos(estado: dict):
    st.subheader("🎯 Objetivos Dinásticos")
    st.markdown("Completá objetivos para desbloquear bonificaciones permanentes para tu dinastía.")
    st.divider()
    
    objetivos = estado.get("objetivos_dinasticos", [])
    completados = estado.get("objetivos_completados", [])
    bonificaciones = estado.get("bonificaciones_objetivos", [])
    
    if not objetivos:
        st.info("No tenés objetivos dinásticos activos.")
        return
    
    recompensas = {
        "Alcanzar la Presidencia antes de los 55": {
            "nombre": "Mandato Legítimo",
            "desc": "Tu Aprobación Pública nunca puede bajar del 40%",
            "icono": "👑"
        },
        "Acumular $5M en patrimonio": {
            "nombre": "Magnate",
            "desc": "Tu próximo heredero empieza con +20 Negocios y $500K extra",
            "icono": "💰"
        },
        "Fundar una empresa Nivel 4": {
            "nombre": "Monopolio Familiar",
            "desc": "Todas tus empresas generan 25% más de dividendos",
            "icono": "🏢"
        },
        "Sobrevivir a 3 Crisis Nacionales": {
            "nombre": "Acero Templado",
            "desc": "Tu Salud Mental y Física no bajan por escándalos",
            "icono": "🛡️"
        }
    }
    
    for obj in objetivos:
        if obj in completados:
            recompensa = recompensas.get(obj, {})
            st.success(f"✅ **{obj}**\n\n🌟 **Recompensa desbloqueada:** {recompensa.get('icono', '✨')} **{recompensa.get('nombre', 'Bonus')}** - {recompensa.get('desc', 'Bonificación especial')}")
        else:
            st.markdown(f"⬜ **{obj}**\n\n*Completá este objetivo para desbloquear una bonificación permanente.*")
    
    if bonificaciones:
        st.divider()
        st.subheader("🌟 Bonificaciones Activas")
        for bonif in bonificaciones:
            st.info(f"✨ **{bonif}**")

def render_tab_logros(estado: dict):
    st.subheader("🏆 Salón de Logros")
    st.markdown("Desbloqueá logros cumpliendo desafíos a lo largo de tu dinastía.")
    st.divider()
    
    # Importamos las definiciones desde mechanics
    from mechanics import LOGROS_DEFINICIONES
    
    logros_actuales = estado.get("logros", [])
    
    for logro_def in LOGROS_DEFINICIONES:
        is_unlocked = logro_def["id"] in logros_actuales
        if is_unlocked:
            st.success(f"✅ **{logro_def['nombre']}**: {logro_def['desc']}")
        else:
            st.markdown(f"🔒 **???**: {logro_def['desc']}")

def render_tab_graficos(estado: dict):
    st.subheader("📊 Métricas Históricas de la Dinastía")
    patrimonio = estado.get("historial_patrimonio", [])
    aprobacion = estado.get("historial_aprobacion", [])
    turnos = list(range(len(patrimonio)))
    
    if len(patrimonio) < 2:
        st.info("📈 Se necesitan al menos 2 turnos de juego para generar el gráfico histórico.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=turnos, y=patrimonio, name="Patrimonio Personal ($)", line=dict(color="#d4af37", width=3), yaxis="y1"))
    fig.add_trace(go.Scatter(x=turnos, y=aprobacion, name="Aprobación Pública (%)", line=dict(color="#e63946", width=3, dash="dot"), yaxis="y2"))

    fig.update_layout(
        title="Evolución: Riqueza vs. Popularidad",
        xaxis_title="Turnos (Meses)",
        yaxis_title="Patrimonio ($)",
        yaxis2=dict(title="Aprobación (%)", overlaying="y", side="right", range=[0, 100]),
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def render_titular(estado: dict):
    st.markdown(f"### {estado.get('titular_periodico', 'Últimas noticias...')}")

def render_objetivos(estado: dict):
    objetivos = estado.get("objetivos_dinasticos", [])
    completados = estado.get("objetivos_completados", [])
    if objetivos:
        st.markdown("**🎯 Objetivos Dinásticos:**")
        for obj in objetivos:
            if obj in completados:
                st.success(f"✅ {obj}")
            else:
                st.markdown(f"⬜ {obj}")