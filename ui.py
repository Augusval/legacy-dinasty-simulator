import os
import json
import random
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import mechanics
from data import CRISIS_DECISIONES, TEMAS_DEBATE

CANDIDATOS_MINISTROS = [
    "Lic. Marta Peña", "Dr. Julio Sáenz", "Ing. Lucía Ferreyra",
    "Cp. Andrés Botto", "Ab. Carla Méndez", "Ec. Raúl Pintos",
]

PERSONALIDADES_LOCALES = ["Leal", "Rebelde", "Inútil", "Ambicioso"]

STATS_0_100 = {
    "opinion_publica", "estabilidad_pais", "produccion_industrial",
    "reputacion", "aprobacion_publica",
}


def inyectar_css():
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,700;1,300&family=Inter:wght@400;600;800&display=swap');

/* Animaciones Keyframes */
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(230, 57, 70, 0.3); }
    50% { box-shadow: 0 0 20px rgba(230, 57, 70, 0.6); }
}

@keyframes slide-in {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

.stApp { background: radial-gradient(circle at 50% 0%, #1a1e29 0%, #0a0c10 100%); color: #e2e8f0; }
h1, h2, h3 { font-family: 'Inter', sans-serif !important; font-weight: 800; letter-spacing: -1px; color: #ffffff; }

.titular { 
    font-family: 'Merriweather', serif !important; 
    font-size: 2.2rem; 
    text-align: center; 
    border-top: 2px solid #e63946;  
    border-bottom: 2px solid #e63946; 
    padding: 15px; 
    margin-bottom: 25px; 
    font-weight: 700; 
    color: #e63946 !important; 
    text-shadow: 0px 0px 10px rgba(230, 57, 70, 0.4);
    animation: slide-in 0.5s ease-out;
}

.cabecera-fecha { text-align: center; font-family: 'Inter', sans-serif; font-size: 1rem; color: #94a3b8; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }

.stat-card { 
    background: rgba(26, 30, 41, 0.7); 
    border-left: 4px solid #e63946; 
    border-radius: 8px; 
    padding: 15px; 
    margin-bottom: 10px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
    display: flex; 
    justify-content: space-between; 
    align-items: center;
    transition: transform 0.2s ease;
}
.stat-card:hover { transform: translateX(5px); }
.stat-card .title { font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.stat-card .value { font-size: 1.5rem; font-family: 'Merriweather', serif; color: #fff; font-weight: 700; }

.custom-progress-container { 
    background-color: #1a1e29; 
    border-radius: 10px; 
    height: 12px; 
    width: 100%; 
    margin-bottom: 15px; 
    overflow: hidden; 
    border: 1px solid #333;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
}

.custom-progress-bar { 
    height: 100%; 
    border-radius: 10px; 
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    background-size: 200% 100%;
    animation: shimmer 3s linear infinite;
}

.progress-label { font-size: 0.85rem; color: #cbd5e1; margin-bottom: 4px; display: flex; justify-content: space-between; }

.stChatMessage { 
    background-color: rgba(26, 30, 41, 0.8) !important; 
    border: 1px solid #2a2f3a !important; 
    border-left: 4px solid #e63946 !important; 
    border-radius: 4px !important; 
    padding: 1rem !important; 
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    animation: slide-in 0.3s ease-out;
}
.stChatMessage p { color: #e2e8f0 !important; }

.stTextInput input { 
    background-color: #1a1e29 !important; 
    color: #fff !important; 
    border: 1px solid #444 !important; 
    border-radius: 6px !important;
    transition: border-color 0.3s ease;
}
.stTextInput input:focus { border-color: #e63946 !important; }

.stButton >button { 
    background: linear-gradient(90deg, #e63946 0%, #b91d2b 100%) !important; 
    color: white !important; 
    border: none !important; 
    border-radius: 6px !important; 
    font-weight: 700 !important; 
    box-shadow: 0 4px 10px rgba(230, 57, 70, 0.3); 
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative;
    overflow: hidden;
}
.stButton >button:hover { 
    transform: translateY(-2px) scale(1.02); 
    box-shadow: 0 8px 20px rgba(230, 57, 70, 0.5);
}
.stButton >button:active {
    transform: translateY(0) scale(0.98);
}

/* Tutorial Modal */
.tutorial-box {
    background: linear-gradient(135deg, rgba(26, 30, 41, 0.95) 0%, rgba(10, 12, 16, 0.95) 100%);
    border: 2px solid #e63946;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 8px 32px rgba(230, 57, 70, 0.3);
    animation: pulse-glow 2s ease-in-out infinite;
}

[data-testid="stSidebar"] { background-color: #050608 !important; border-right: 1px solid #1f2430; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
</style>
""",
        unsafe_allow_html=True,
    )


def render_cabecera(estado):
    fecha = mechanics.fecha_legible(estado.get("mes_actual", 0))
    dinastia = estado.get("apellido_dinastia", "") or "Sin Dinastía"
    st.markdown(
        f'<div class="cabecera-fecha">📅 {fecha} · 🏰 Dinastía {dinastia} · '
        f"Generación {estado.get('generacion_actual', 1)} · {estado.get('cargo_politico')} · "
        f"Ideología: {estado.get('ideologia', 'Centro')}</div>",
        unsafe_allow_html=True,
    )


def render_titular(estado):
    titular = estado.get("titular_periodico", "Edición de la mañana")
    st.markdown(f'<div class="titular">{titular}</div>', unsafe_allow_html=True)


def custom_progress(label, value, max_value, color="#e63946"):
    percent = min(100, int((value / max_value) * 100)) if max_value > 0 else 0
    st.markdown(
        f"""
        <div class="progress-label">
            <span>{label}</span>
            <span>{value} / {max_value}</span>
        </div>
        <div class="custom-progress-container">
            <div class="custom-progress-bar" style="width: {percent}%; background-color: {color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_resumen_turno(estado):
    resumen = estado.get("resumen_ultimo_turno", [])
    if resumen:
        st.caption("📊 **Cambios del último turno:** " + " · ".join(resumen))


def render_objetivos(estado):
    objetivos = estado.get("objetivos_dinasticos", [])
    if not objetivos:
        return
    with st.expander(f"🎯 Objetivos Dinásticos ({len(estado.get('objetivos_completados', []))}/{len(objetivos)} cumplidos)"):
        for obj in objetivos:
            if obj in estado.get("objetivos_completados", []):
                st.success(f"✅ {obj}")
            else:
                st.info(f"⏳ {obj}")


def render_grafico_historico(estado):
    if not estado.get("historial_aprobacion"):
        st.info("No hay datos históricos aún.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=estado["historial_aprobacion"],
        mode='lines+markers',
        name='Aprobación Pública',
        line=dict(color='#e63946', width=3)
    ))
    fig.update_layout(
        title="Evolución Histórica (Últimos 20 turnos)",
        xaxis_title="Turno",
        yaxis_title="Porcentaje",
        template="plotly_dark",
        height=400,
        showlegend=True,
        plot_bgcolor='rgba(26, 30, 41, 0.7)',
        paper_bgcolor='rgba(10, 12, 16, 0.7)',
    )
    st.plotly_chart(fig, use_container_width=True)


def render_mapa_electoral(estado):
    mapa = estado.get("mapa_electoral", {})
    if not mapa:
        st.info("Aún no cerraste ninguna elección: cuando lo hagas, acá vas a ver el mapa de apoyo por provincia.")
        return
    df = pd.DataFrame({"provincia": list(mapa.keys()), "apoyo": list(mapa.values())})
    geo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "argentina.geojson")
    if os.path.exists(geo_path):
        with open(geo_path, encoding="utf-8") as f:
            geo = json.load(f)
        fig = px.choropleth(
            df, geojson=geo, locations="provincia", featureidkey="properties.name",
            color="apoyo", range_color=(0, 100), color_continuous_scale="RdBu_r",
            labels={"apoyo": "% de apoyo"},
        )
        fig.update_layout(
            template="plotly_dark", height=500,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            title="Mapa Electoral por Provincia",
            paper_bgcolor='rgba(10, 12, 16, 0.7)',
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.bar(df, x="provincia", y="apoyo", template="plotly_dark", color="apoyo",
                     color_continuous_scale="RdBu_r", labels={"apoyo": "% de apoyo", "provincia": "Provincia"})
        fig.update_layout(title="Apoyo por Provincia (última elección)", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 Tip: colocá un archivo `argentina.geojson` en la carpeta del juego para ver el mapa real en vez de barras.")


def render_sidebar(estado, mechanics_mod):
    with st.sidebar:
        st.title("EL DIARIO")

        # --- TARJETAS PRINCIPALES ---
        st.markdown(
            f"""
            <div class="stat-card">
                <span class="title">Fondos</span>
                <span class="value">${estado.get('dinero_personal', 0):,}</span>
            </div>
            <div class="stat-card">
                <span class="title">Edad</span>
                <span class="value">{int(estado.get('edad', 24))} años</span>
            </div>
            <div class="stat-card">
                <span class="title">Sueldo</span>
                <span class="value" style="font-size: 1rem;">${estado.get('ingreso_mensual', 0):,}/mes</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- TESORO NACIONAL (solo si es Presidente) ---
        if estado.get("cargo_politico") == "Presidente":
            st.divider()
            st.markdown("**🏦 Tesoro Nacional**")
            st.markdown(
                f"""
                <div class="stat-card">
                    <span class="title">Arcas del Estado</span>
                    <span class="value" style="font-size: 1.1rem;">${estado.get('tesoro_nacional', 0):,}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(f"Inflación: {estado.get('inflacion', 0):.1f}%")

        st.divider()

        # --- BARRAS DE ESTADO ---
        custom_progress("🔋 Energía", estado.get("energia", 50), estado.get("energia_max", 100), "#3b82f6")
        custom_progress("⭐ Reputación", estado.get("reputacion", 50), 100, "#f59e0b")
        custom_progress("🚨 Corrupción", estado.get("nivel_corrupcion", 0), 100, "#e63946")
        custom_progress("📰 Escándalo", estado.get("escandalo_acumulado", 0), 100, "#dc2626")

        st.divider()

        # --- SALUD ---
        st.markdown("**🫀 Salud**")
        custom_progress("🫀 Física", estado.get("salud_fisica", 90), 100, "#ef4444")
        custom_progress("🧠 Mental", estado.get("salud_mental", 80), 100, "#a855f7")

        st.divider()

        # --- HABILIDADES ---
        st.markdown("**📊 Habilidades**")
        custom_progress("💻 Técnica", estado.get("habilidad_tecnica", 10), 100, "#10b981")
        custom_progress("🗣️ Política", estado.get("habilidad_politica", 10), 100, "#8b5cf6")
        custom_progress("💼 Negocios", estado.get("habilidad_negocios", 10), 100, "#f97316")

        st.divider()

        # --- FACCIONES (siempre visibles) ---
        st.markdown("**⚖️ Facciones**")
        facciones = estado.get("facciones", {})
        custom_progress("🎖️ Militares", facciones.get("Militares", 50), 100, "#64748b")
        custom_progress("✊ Sindicatos", facciones.get("Sindicatos", 50), 100, "#f97316")
        custom_progress("⛪ Iglesia", facciones.get("Iglesia", 50), 100, "#a855f7")
        custom_progress("💼 Empresarios", facciones.get("Empresarios", 50), 100, "#10b981")

        # --- RELACIONES INTERNACIONALES (solo si es Presidente) ---
        if estado.get("cargo_politico") == "Presidente":
            st.divider()
            st.markdown("**🌍 Relaciones Internacionales**")
            relaciones = estado.get("relaciones_internacionales", {})
            custom_progress("🇺🇸 EE.UU.", relaciones.get("EE.UU.", 50), 100, "#3b82f6")
            custom_progress("🇨🇳 China", relaciones.get("China", 50), 100, "#ef4444")
            custom_progress("🇧🇷 Brasil", relaciones.get("Brasil", 50), 100, "#22c55e")

        # --- LOGROS ---
        st.divider()
        if estado.get("logros"):
            st.markdown("**🏆 Logros**")
            for logro in estado["logros"][-3:]:
                st.success(f"✓ {logro}")

        # --- GUARDAR / CARGAR ---
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar", use_container_width=True):
                mechanics_mod.save_to_disk()
        with col2:
            if st.button("📂 Cargar", use_container_width=True):
                if mechanics_mod.load_from_disk():
                    st.rerun()

        st.markdown("**Slots de Guardado:**")
        for i in range(3):
            if st.button(f"Slot {i+1}", use_container_width=True, key=f"slot_{i}"):
                if mechanics_mod.load_from_slot(i):
                    st.rerun()


def render_tab_gobierno(estado):
    if estado.get("cargo_politico") != "Presidente":
        st.info("Llegá a la Presidencia para gestionar el Gabinete, Leyes y Diplomacia.")
        return
    st.subheader("Despacho Presidencial")

    # --- RESUMEN DE TESORERÍA ---
    st.markdown("### 🏦 Estado de la Nación")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tesoro Nacional", f"${estado.get('tesoro_nacional', 0):,}")
    col2.metric("Inflación", f"{estado.get('inflacion', 0):.1f}%")
    col3.metric("Estabilidad", f"{estado.get('estabilidad_pais', 0)}/100")
    col4.metric("Aprobación", f"{estado.get('aprobacion_publica', 0)}/100")

    st.markdown("### 👔 Gabinete de Ministros")
    for cargo, m in estado["ministros"].items():
        st.write(f"**{cargo}:** {m['nombre']} (Lealtad: {m['lealtad']}%, Corrupción: {m['corrupcion']}%)")
        if m["nombre"] != "Vacante" and m["lealtad"] <= 20:
            st.warning(f"⚠️ {m['nombre']} está al borde de la traición. Despedilo o negociá.")
        if m["nombre"] == "Vacante":
            candidato = st.selectbox(f"Candidato para {cargo}:", CANDIDATOS_MINISTROS, key=f"cand_{cargo}")
            if st.button(f"Nombrar a {candidato}", key=f"nombrar_{cargo}"):
                st.session_state.estado["ministros"][cargo] = {
                    "nombre": candidato,
                    "lealtad": 60,
                    "corrupcion": random.randint(0, 20),
                }
                mechanics.agregar_memoria(st.session_state.estado, f"{candidato} asumió como ministro de {cargo}.")
                st.rerun()
        else:
            if st.button(f"Despedir a Ministro de {cargo}", key=f"despedir_{cargo}"):
                st.session_state.estado["ministros"][cargo] = {
                    "nombre": "Vacante",
                    "lealtad": 50,
                    "corrupcion": 0,
                }
                st.rerun()

    st.markdown("### ⚖️ Leyes Polémicas")
    ideologia = estado.get("ideologia", "Centro")
    for ley in mechanics.LEYES:
        if ley["nombre"] in estado["leyes_aprobadas"]:
            st.success(f"✅ {ley['nombre']} (aprobada)")
            continue
        mult = 1 if ley["afinidad"] == ideologia else 2
        faccion, costo = ley["costo"]
        costo_final = costo * mult
        etiqueta_afin = "afín a tu ideología" if mult == 1 else "CONTRA tu ideología (costo doble)"
        if st.button(
            f"Aprobar {ley['nombre']} ({ley['afinidad']}, {etiqueta_afin}) → -{costo_final} {faccion}",
            key=f"ley_{ley['nombre']}",
        ):
            clave, delta = ley["efecto"]
            actual = st.session_state.estado.get(clave, 0) + delta
            if clave in STATS_0_100:
                actual = max(0, min(100, actual))
            st.session_state.estado[clave] = actual
            st.session_state.estado["facciones"][faccion] = max(
                0, st.session_state.estado["facciones"][faccion] - costo_final
            )
            if mult == 1:
                st.session_state.estado["opinion_publica"] = min(
                    100, st.session_state.estado["opinion_publica"] + 5
                )
            st.session_state.estado["leyes_aprobadas"].append(ley["nombre"])
            mechanics.agregar_memoria(st.session_state.estado, f"Se aprobó la ley {ley['nombre']}.")
            st.rerun()

    st.markdown("### 🌍 Geopolítica")
    if not estado.get("prestamo_fmi"):
        if st.button("Pedir Préstamo al FMI (+$10M, +Deuda)", key="fmi"):
            st.session_state.estado["tesoro_nacional"] += 10000000
            st.session_state.estado["prestamo_fmi"] = True
            st.session_state.estado["relaciones_internacionales"]["EE.UU."] = min(
                100, st.session_state.estado["relaciones_internacionales"]["EE.UU."] + 10
            )
            st.rerun()
    if st.button("Tratado Comercial con China (+$5M, -10 Sindicatos)", key="china_tratado"):
        st.session_state.estado["tesoro_nacional"] += 5000000
        st.session_state.estado["facciones"]["Sindicatos"] = max(0, st.session_state.estado["facciones"]["Sindicatos"] - 10)
        st.rerun()

    st.markdown("### 🏗️ Megaobras Nacionales")
    if estado.get("megaobras_activas"):
        for obra in estado["megaobras_activas"]:
            st.info(f"🚧 **En construcción:** {obra['nombre']} (Faltan {obra['turnos']} meses)")
    for fila in range(0, len(mechanics.MEGAOBRAS), 3):
        cols = st.columns(3)
        for i, obra in enumerate(mechanics.MEGAOBRAS[fila:fila + 3]):
            with cols[i]:
                if st.button(f"{obra['nombre']} (${obra['costo'] // 1000000}M)", key=f"obra_{obra['nombre']}"):
                    if estado.get("tesoro_nacional", 0) >= obra["costo"]:
                        st.session_state.estado["tesoro_nacional"] -= obra["costo"]
                        st.session_state.estado["megaobras_activas"].append(dict(obra))
                        st.rerun()
                    else:
                        st.error("Tesoro insuficiente.")


def render_tab_vida(estado):
    st.subheader("Vida Personal y Familia")
    if estado.get("hospitalizado"):
        st.error("🏥 **Estás hospitalizado.** Recuperate desde la pestaña Portada antes de hacer vida social.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ❤️ Romance")
        if estado.get("pareja_nombre") == "Nadie":
            gen_jugador = estado.get("genero", "Masculino")
            gen_pareja = "Femenino" if gen_jugador == "Masculino" else "Masculino"
            st.info(f"Buscás una pareja del género **{gen_pareja}**.")
            with st.form("form_pareja"):
                nombre_p = st.text_input("Ingresá el nombre de tu pareja:")
                submit_p = st.form_submit_button("Conocer a esta persona")
                if submit_p:
                    if nombre_p.strip():
                        st.session_state.estado["pareja_nombre"] = nombre_p.strip()
                        st.session_state.estado["pareja_genero"] = gen_pareja
                        st.session_state.estado["pareja_afinidad"] = 50
                        st.rerun()
                    else:
                        st.error("Por favor, ingresá un nombre.")
        else:
            st.write(f"Estás en pareja con **{estado['pareja_nombre']}** ({estado.get('pareja_genero', '')}).")
            if st.button("Tener un Hijo"):
                nombre_h = mechanics.generar_nombre_hijo(
                    estado.get("apellido_dinastia", ""), estado.get("hijos", [])
                )
                personalidad = random.choice(PERSONALIDADES_LOCALES)
                st.session_state.estado["hijos"].append(nombre_h)
                st.session_state.estado["hijos_edad"][nombre_h] = 0
                st.session_state.estado["hijos_educacion"][nombre_h] = "Pública"
                st.session_state.estado["hijos_personalidad"][nombre_h] = personalidad
                mechanics.agregar_memoria(st.session_state.estado, f"Nació {nombre_h} ({personalidad}).")
                st.success(f"¡Nació {nombre_h}! Personalidad: {personalidad}")
                st.rerun()
    with col2:
        st.markdown("### 👨‍👩‍ Hijos")
        if not estado.get("hijos"):
            st.info("No tenés hijos.")
        else:
            for idx, hijo in enumerate(estado["hijos"]):
                edad_h = int(estado["hijos_edad"].get(hijo, 0))
                edu = estado["hijos_educacion"].get(hijo, "Pública")
                pers = estado["hijos_personalidad"].get(hijo, "Leal")
                st.write(f"**{hijo}** ({edad_h} años) - Educación: {edu} - Personalidad: {pers}")
                if edad_h >= 5 and edu == "Pública":
                    if st.button(f"Pagar Colegio Privado para {hijo} ($50k)", key=f"edu_{idx}"):
                        if estado.get("dinero_personal", 0) >= 50000:
                            st.session_state.estado["dinero_personal"] -= 50000
                            st.session_state.estado["hijos_educacion"][hijo] = "Privada"
                            st.success(f"{hijo} ahora va a un colegio privado.")
                            st.rerun()
                if edad_h >= 18:
                    st.caption("🎓 Mayor de edad: podría continuar la dinastía.")
                if estado.get("hijo_heredero") == hijo:
                    st.caption("👑 Heredero designado")
                elif st.button(f"Nombrar {hijo} como heredero", key=f"heredero_{idx}"):
                    st.session_state.estado["hijo_heredero"] = hijo
                    st.success(f"{hijo} será tu heredero.")
                    st.rerun()


def render_tab_empresas(estado):
    st.subheader("Imperio Corporativo")
    st.write("Fundá empresas y cobrá dividendos pasivos cada mes.")
    if estado.get("corporaciones"):
        for emp, poder in estado["corporaciones"].items():
            c1, c2 = st.columns([3, 1])
            c1.write(f"🏢 **{emp}** (Poder: {poder}%)")
            if c2.button("💸 Invertir $50k", key=f"inv_{emp}"):
                if estado.get("dinero_personal", 0) >= 50000:
                    st.session_state.estado["dinero_personal"] -= 50000
                    st.session_state.estado["corporaciones"][emp] = min(100, poder + 10)
                    st.success(f"Invertiste en {emp}. Subió al {min(100, poder + 10)}%.")
                    st.rerun()
                else:
                    st.error("No tenés $50k.")
    else:
        st.info("Aún no tenés empresas.")
    st.divider()
    st.markdown("### 🏗️ Fundar Nueva Empresa")
    with st.form("form_nueva_empresa"):
        nombre_emp = st.text_input("Nombre de la corporación:")
        submit = st.form_submit_button("Fundar Empresa ($100k)")
        if submit:
            if not nombre_emp.strip():
                st.error("Poné un nombre.")
            elif estado.get("dinero_personal", 0) < 100000:
                st.error("No tenés los $100k iniciales.")
            elif nombre_emp in estado.get("corporaciones", {}):
                st.error("Ya tenés una empresa con ese nombre.")
            else:
                st.session_state.estado["dinero_personal"] -= 100000
                st.session_state.estado["corporaciones"][nombre_emp] = 10
                st.success(f"¡Fundaste {nombre_emp}!")
                st.rerun()


def render_tab_rivales(estado):
    st.subheader("🎭 Rivales Políticos")
    if not estado.get("rivales"):
        st.info("No tenés rivales identificados aún.")
        return
    st.caption("Los rivales con relación baja te atacan cada turno según su poder. Con relación alta, te respaldan.")

    if estado.get("negociacion_activa"):
        neg = estado["negociacion_activa"]
        st.divider()
        st.error(f"🎮 **NEGOCIACIÓN CON {neg.get('rival_nombre', 'UN RIVAL')}**")
        st.write(neg.get("propuesta", ""))
        cols = st.columns(len(neg.get("opciones", [])))
        for i, opcion in enumerate(neg.get("opciones", [])):
            if cols[i].button(opcion["texto"], key=f"neg_op_{i}"):
                for efecto, valor in opcion["efecto"].items():
                    if efecto == "poder_rival":
                        for r in st.session_state.estado["rivales"]:
                            if r["nombre"] == neg["rival_nombre"]:
                                r["poder"] = max(0, r["poder"] + valor)
                    elif efecto == "poder_jugador":
                        st.session_state.estado["reputacion"] = min(100, st.session_state.estado["reputacion"] + valor)
                    elif efecto == "relacion":
                        for r in st.session_state.estado["rivales"]:
                            if r["nombre"] == neg["rival_nombre"]:
                                r["relacion"] = max(0, min(100, r["relacion"] + valor))
                    elif efecto == "dinero":
                        st.session_state.estado["dinero_personal"] += valor
                    elif efecto == "corrupcion":
                        st.session_state.estado["nivel_corrupcion"] = min(100, st.session_state.estado["nivel_corrupcion"] + valor)
                    elif efecto == "reputacion":
                        st.session_state.estado["reputacion"] = max(0, st.session_state.estado["reputacion"] + valor)
                st.session_state.estado["negociacion_activa"] = {}
                st.rerun()
        return

    for idx, rival in enumerate(estado["rivales"]):
        with st.container():
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{rival['nombre']}** — {rival['cargo']}")
            col1.markdown(f"Relación: {rival['relacion']}% | Poder: {rival['poder']}%")
            if rival["relacion"] < 40:
                col1.warning("⚠️ Hostil: puede atacarte.")
            elif rival["relacion"] > 70:
                col1.success("🤝 Aliado: puede respaldarte.")
            if col2.button("🤝 Negociar (Mini-juego)", key=f"negociar_{idx}"):
                propuesta = mechanics.generar_negociacion_rival(rival)
                st.session_state.estado["negociacion_activa"] = {
                    "rival_nombre": rival["nombre"],
                    "propuesta": propuesta["texto"],
                    "opciones": propuesta["opciones"],
                }
                st.rerun()


def render_tab_archivo(estado):
    st.subheader("📚 Archivo Histórico")
    if not estado.get("archivo_noticias"):
        st.info("No hay noticias archivadas aún.")
        return
    st.markdown("**Últimas 20 noticias:**")
    for noticia in estado["archivo_noticias"][:20]:
        with st.expander(f"Turno {noticia['turno']}: {noticia['titulo']}"):
            st.write(noticia['narrativa'])


def render_tab_graficos(estado):
    st.subheader("📈 Evolución Histórica")
    render_grafico_historico(estado)