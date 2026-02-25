import streamlit as st
import pandas as pd
import time
import os
import json
import datetime
from dotenv import load_dotenv
from google import genai
from PIL import Image

# --- 1. CONFIGURACIÓN E IA ---
load_dotenv()
st.set_page_config(page_title="FitChef AI Pro", layout="wide", page_icon="🥗")

# --- CONFIGURACIÓN DE SEGURIDAD PARA LA NUBE ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    IA_ACTIVA = True
except Exception as e:
    IA_ACTIVA = False

# --- 2. MEMORIA DE LA APP (Sistema Operativo Total) ---
if 'perfil' not in st.session_state:
    st.session_state.perfil = {
        'sexo': 'Hombre', 'perfil_hormonal': 'Ninguno', 'presupuesto': 'Moderado',
        'edad': 30, 'peso': 75.0, 'altura': 175, 'actividad': 'Moderada',
        'objetivo': 'Estética Funcional', 'dias_entreno': 3,
        'experiencia': 'Intermedio (1-3 años)', 'lugar_entreno': 'Gimnasio Comercial', 'horario_entreno': 'Tarde',
        'dieta_tipo': 'Omnívora', 'alergias': '', 'n_comidas': 4, 'ayuno': False, 'suplementos': '',
        'lesiones': '', 'sueno': 'Normal (6-8h)', 'estres': 'Moderado',
        'utensilios': ['Sartén', 'Horno'], 'tiempo_cocina': 30
    }
# Nutrición
if 'despensa' not in st.session_state: st.session_state.despensa = []
if 'plan_estructurado' not in st.session_state: st.session_state.plan_estructurado = None
if 'comidas_completadas' not in st.session_state: st.session_state.comidas_completadas = []
if 'gustos_positivos' not in st.session_state: st.session_state.gustos_positivos = []
if 'gustos_negativos' not in st.session_state: st.session_state.gustos_negativos = []
if 'agua_bebida' not in st.session_state: st.session_state.agua_bebida = 0.0
if 'meta_agua' not in st.session_state: st.session_state.meta_agua = 2.5

# Entrenamiento y Progreso (NUEVO)
if 'rutina_estructurada' not in st.session_state: st.session_state.rutina_estructurada = None
if 'ejercicios_completados' not in st.session_state: st.session_state.ejercicios_completados = []
if 'historial_cargas' not in st.session_state: st.session_state.historial_cargas = {}
if 'galeria_espejo' not in st.session_state: st.session_state.galeria_espejo = []
if 'historial_biometrico' not in st.session_state: 
    st.session_state.historial_biometrico = pd.DataFrame(columns=["Fecha", "Peso (kg)", "Grasa (%)", "Cintura (cm)", "Pasos", "FC Reposo", "Digestión", "Fatiga SNC"])

if 'racha_nutricion' not in st.session_state: st.session_state.racha_nutricion = 0
if 'racha_entreno' not in st.session_state: st.session_state.racha_entreno = 0

def generar_ics(plan_json):
    """Genera archivo .ics para el calendario"""
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FitChef AI//ES"]
    dias_map = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    hoy = datetime.date.today()
    for dia_nombre, comidas in plan_json.items():
        if dia_nombre not in dias_map: continue
        delta_dias = (dias_map[dia_nombre] - hoy.weekday()) % 7
        fecha_evento = hoy + datetime.timedelta(days=delta_dias)
        hora_comida = 9 
        for comida in comidas:
            dt_start = fecha_evento.strftime("%Y%m%d") + f"T{hora_comida:02d}0000"
            dt_end = fecha_evento.strftime("%Y%m%d") + f"T{hora_comida+1:02d}0000"
            lineas.extend(["BEGIN:VEVENT", f"SUMMARY:🍽️ {comida['tipo']} - {comida['plato']}", f"DESCRIPTION:Ingredientes: {', '.join(comida['ingredientes'])}", f"DTSTART:{dt_start}", f"DTEND:{dt_end}", "END:VEVENT"])
            hora_comida += 3 
    lineas.append("END:VCALENDAR")
    return "\n".join(lineas)

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("🛡️ FitChef AI")
    st.subheader("🔥 Tus Rachas")
    col_r1, col_r2 = st.columns(2)
    with col_r1: st.metric(label="🥗 Nutrición", value=f"{st.session_state.racha_nutricion} pts")
    with col_r2: st.metric(label="🏋️ Entreno", value=f"{st.session_state.racha_entreno} días")
    
    st.subheader("💧 Hidratación Hoy")
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1: st.metric(label=f"Agua (Meta: {st.session_state.meta_agua}L)", value=f"{st.session_state.agua_bebida:.2f} L")
    with col_w2: 
        if st.button("🥤 +0.25L"): st.session_state.agua_bebida += 0.25; st.rerun()
    st.divider()

# --- 4. NAVEGACIÓN INTERACTIVA ACTUALIZADA ---
if 'menu_val' not in st.session_state:
    st.session_state.menu_val = "🏠 Inicio"

def cambiar_pestana(nombre):
    st.session_state.menu_val = nombre
    st.rerun()

opciones_menu = ["🏠 Inicio", "🥗 Nutrición Pro", "🏋️‍♂️ Entrenador IA", "🍷 Vida Social", "🩸 Progreso", "👤 Perfil"]
menu = st.radio(
    "Navegación:", 
    opciones_menu, 
    index=opciones_menu.index(st.session_state.menu_val),
    horizontal=True
)

st.divider()

# ==========================================
# 🏠 PANTALLA: INICIO (PÁGINA CERO)
# ==========================================
if menu == "🏠 Inicio":
    st.title("🚀 FitChef AI")
    st.subheader(f"Bienvenida a tu mejor versión, {st.session_state.perfil.get('objetivo', 'Guerrera').split()[-1]}")
    
    st.image("https://images.unsplash.com/photo-1594882645126-14020914d58d?q=80&w=2085&auto=format&fit=crop", use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🥗 Racha Dieta", f"{st.session_state.racha_nutricion} d")
    with c2: st.metric("💪 Racha Entreno", f"{st.session_state.racha_entreno} d")
    with c3: st.metric("💧 Meta Agua", f"{st.session_state.meta_agua}L")

    st.markdown("""
    ### 🌟 ¿Qué hacemos hoy?
    Selecciona una opción en el menú superior o usa estos accesos rápidos:
    """)
    
    # Botones que funcionan y te llevan a las pestañas
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("🥗 IR A NUTRICIÓN", use_container_width=True): cambiar_pestana("🥗 Nutrición Pro")
        if st.button("🍷 VIDA SOCIAL", use_container_width=True): cambiar_pestana("🍷 Vida Social")
    with c_btn2:
        if st.button("🏋️‍♂️ IR A ENTRENAMIENTO", use_container_width=True): cambiar_pestana("🏋️‍♂️ Entrenador IA")
        if st.button("👤 CONFIGURAR PERFIL", use_container_width=True, type="primary"): cambiar_pestana("👤 Perfil")

    st.info("💡 **Tip de hoy:** Beber un vaso de agua antes de cada comida mejora tu digestión y saciedad.")

# ==========================================
# 👤 PANTALLA: PERFIL GOD-TIER (COMPLETO)
# ==========================================
elif menu == "👤 Perfil":
    with st.form("perfil_completo"):
        st.subheader("👤 Perfil God-Tier")
        
        with st.expander("1. Biometría y Salud Femenina"):
            sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], index=0 if st.session_state.perfil.get('sexo') == 'Hombre' else 1)
            perfil_hormonal = "Ninguno"
            if sexo == "Mujer":
                perfil_hormonal = st.selectbox("Fase Hormonal", ["Ninguno", "Fase Folicular (Post-regla)", "Fase Lútea (Pre-regla)", "SOP", "Endometriosis", "Embarazo", "Postparto", "Menopausia", "⚠️ RED-S (Falta de regla)"], index=0)
            
            col_bio1, col_bio2, col_bio3 = st.columns(3)
            with col_bio1: edad = st.number_input("Edad", 14, 90, st.session_state.perfil['edad'])
            with col_bio2: altura = st.number_input("Altura (cm)", 100, 250, st.session_state.perfil['altura'])
            with col_bio3: peso = st.number_input("Peso (kg)", 30.0, 200.0, st.session_state.perfil['peso'])
            
            actividad = st.selectbox("NEAT Diario", ["Sedentaria", "Ligera", "Moderada", "Muy Activa"], index=2)

        with st.expander("2. Objetivos y Logística de Entreno"):
            obj = st.selectbox("Programa (Objetivo)", [
                "Estética Funcional", "Powerbuilding (Fuerza + Volumen)", 
                "Shredding (Definición Extrema)", "Recomposición Femenina (Focus Glúteo)", 
                "Atleta Híbrido", "Longevidad y Salud Articular"
            ], index=0)
            experiencia = st.selectbox("Nivel", ["Principiante (<1 año)", "Intermedio (1-3 años)", "Avanzado (+3 años)"], index=1)
            col_ent1, col_ent2 = st.columns(2)
            with col_ent1: lugar_entreno = st.selectbox("Lugar", ["Gimnasio Comercial", "Home Gym (Mancuernas)", "Calistenia (Parque/Peso corporal)"])
            with col_ent2: horario_entreno = st.selectbox("Horario habitual", ["Mañana (Ayunas)", "Mañana (Tras desayunar)", "Tarde", "Noche"])
            dias_gym = st.slider("Días de entreno", 1, 6, st.session_state.perfil['dias_entreno'])

        with st.expander("3. Nutrición y Presupuesto"):
            presupuesto = st.select_slider("Presupuesto", options=["Económico", "Moderado", "Premium"], value=st.session_state.perfil.get('presupuesto', 'Moderado'))
            dieta_tipo = st.selectbox("Tipo de Dieta", ["Omnívora", "Vegetariana", "Vegana", "Keto", "Pescetariana"])
            col_nut1, col_nut2 = st.columns(2)
            with col_nut1: n_comidas = st.number_input("Comidas/día", 1, 8, st.session_state.perfil['n_comidas'])
            with col_nut2: ayuno = st.toggle("¿Haces Ayuno Intermitente?", value=st.session_state.perfil['ayuno'])
            alergias = st.text_input("Alergias", value=st.session_state.perfil['alergias'])
            suplementos = st.text_input("Suplementos", value=st.session_state.perfil['suplementos'])

        with st.expander("4. Clínica y Recuperación"):
            lesiones = st.text_area("Lesiones/Patologías", value=st.session_state.perfil['lesiones'])
            col_clin1, col_clin2 = st.columns(2)
            with col_clin1: sueno = st.selectbox("Sueño", ["Poco (<6h)", "Normal (6-8h)", "Óptimo (>8h)"], index=1)
            with col_clin2: estres = st.selectbox("Estrés", ["Bajo", "Moderado", "Alto"], index=1)
            
        with st.expander("5. 🧠 Memoria Gastronómica IA"):
            gustos_pos_str = st.text_area("AMAS (Ingredientes/Platos):", value=", ".join(st.session_state.gustos_positivos))
            gustos_neg_str = st.text_area("ODIAS (Lo que no quieres ver):", value=", ".join(st.session_state.gustos_negativos))
        
        if st.form_submit_button("💾 Actualizar y Guardar"):
            st.session_state.perfil.update({
                'sexo': sexo, 'perfil_hormonal': perfil_hormonal, 'presupuesto': presupuesto,
                'edad': edad, 'peso': peso, 'altura': altura, 'actividad': actividad, 'objetivo': obj, 
                'experiencia': experiencia, 'lugar_entreno': lugar_entreno, 'horario_entreno': horario_entreno,
                'dias_entreno': dias_gym, 'dieta_tipo': dieta_tipo, 'alergias': alergias, 
                'n_comidas': n_comidas, 'ayuno': ayuno, 'suplementos': suplementos, 'lesiones': lesiones, 
                'sueno': sueno, 'estres': estres
            })
            st.session_state.gustos_positivos = [g.strip() for g in gustos_pos_str.split(",") if g.strip()]
            st.session_state.gustos_negativos = [g.strip() for g in gustos_neg_str.split(",") if g.strip()]
            st.success("¡Perfil actualizado! Tus variables se han guardado.")
            st.rerun()

# ==========================================
# PANTALLA: NUTRICIÓN PRO
# ==========================================
elif menu == "🥗 Nutrición Pro":
    st.header("🥗 Tu Central Nutricional")
    with st.expander("🛒 Mi Despensa y Escáner", expanded=not bool(st.session_state.plan_estructurado)):
        t_nev, t_lis, t_bar, t_voz, t_man = st.tabs(["📸 Nevera", "📝 Lista", "🔢 Barras", "🎤 Voz", "⌨️ Manual"])
        with t_nev:
            st.write("📸 **Escáner de Nevera**")
            usar_cam_nev = st.toggle("Usar cámara en vivo", key="tg_nev")
            if usar_cam_nev:
                foto_final = st.camera_input("Enfoca tus ingredientes", key="cam_nev")
            else:
                foto_final = st.file_uploader("📷 Haz una foto o sube imagen", type=['jpg', 'png'], key="up_nev")
            
            if foto_final and IA_ACTIVA:
                with st.spinner("Detectando..."):
                    res = client.models.generate_content(model='gemini-2.5-flash', contents=["Ingredientes en español, separados por comas.", Image.open(foto_final)])
                    st.session_state.despensa.extend([i.strip().lower() for i in res.text.split(",") if i.strip()])
                    st.session_state.despensa = list(set(st.session_state.despensa))
                    st.success("¡Ingredientes añadidos!")
        with t_man:
            manual = st.text_input("Añadir a mano (ej: pollo, arroz)")
            if st.button("Añadir"): 
                st.session_state.despensa.extend([i.strip().lower() for i in manual.split(",") if i.strip()])
                st.session_state.despensa = list(set(st.session_state.despensa))
                st.rerun()

        if st.session_state.despensa:
            st.info(f"🥑 **En casa:** {', '.join(st.session_state.despensa).title()}")
            if st.button("🗑️ Vaciar Despensa"): st.session_state.despensa = []; st.rerun()

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1: btn_despensa = st.button("🚀 GENERAR PLAN USANDO MI DESPENSA", type="primary", use_container_width=True)
    with col_g2: btn_cero = st.button("🛒 GENERAR DESDE CERO (Hacer la compra)", use_container_width=True)

    if (btn_despensa or btn_cero) and IA_ACTIVA:
        with st.spinner("Estructurando semana..."):
            p = st.session_state.perfil
            des_usar = st.session_state.despensa if btn_despensa else []
            prompt_json = f"""
            Nutricionista clínico. Crea menú de 7 días. Objetivo: {p['objetivo']}. Lesiones: {p['lesiones']}. Hormonas: {p['perfil_hormonal']}.
            ⚠️ REGLA MÉDICA: Si el Perfil Hormonal es 'RED-S', PROHIBIDO el déficit calórico. Si es 'Endometriosis', dieta antiinflamatoria.
            DESPENSA: {des_usar}. FAVORITOS: {st.session_state.gustos_positivos}. PROHIBIDOS: {st.session_state.gustos_negativos}.
            DEVUELVE SOLO UN JSON: {{ "Lunes": [ {{"tipo": "Desayuno", "plato": "Nombre", "ingredientes": ["ing1"]}} ] }}
            """
            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_json)
            texto_limpio = res.text.replace("```json", "").replace("```", "").strip()
            st.session_state.plan_estructurado = json.loads(texto_limpio)
            st.session_state.comidas_completadas = [] 

    if st.session_state.plan_estructurado:
        st.subheader("📅 Tu Agenda Interactiva")
        ics_data = generar_ics(st.session_state.plan_estructurado)
        c_cal, c_txt = st.columns(2)
        with c_cal: st.download_button("📅 Google Calendar", data=ics_data, file_name="FitChef.ics")
        with c_txt: st.download_button("📄 Descargar TXT", data=json.dumps(st.session_state.plan_estructurado, indent=2), file_name="Plan.txt")
        
        dia_sel = st.selectbox("Día:", list(st.session_state.plan_estructurado.keys()))
        comidas = st.session_state.plan_estructurado.get(dia_sel, [])
        
        for i, comida in enumerate(comidas):
            id_c = f"{dia_sel}_{i}"
            st.markdown(f"**🕒 {comida['tipo']}**: {comida['plato']}")
            if id_c in st.session_state.comidas_completadas:
                st.success("✅ Completado")
            else:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✅ Hecho", key=f"y_{id_c}"):
                        st.session_state.comidas_completadas.append(id_c)
                        st.session_state.racha_nutricion += 1
                        for ing in comida['ingredientes']:
                            if ing.lower() in st.session_state.despensa: st.session_state.despensa.remove(ing.lower())
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Otro", key=f"n_{id_c}"): st.session_state[f"cam_{id_c}"] = True

        # Alerta Stock
        ing_hoy = [ing for c in comidas for ing in c.get('ingredientes', [])]
        faltan = [i for i in ing_hoy if i.lower() not in st.session_state.despensa]
        if faltan:
            st.error("⚠️ Faltan estos ingredientes hoy:")
            for it in set(faltan): st.checkbox(it.capitalize(), key=f"chk_{it}")

        # Consumo Extra
        st.divider()
        snack = st.text_input("🍽️ Consumo extra manual:")
        if st.button("Restar snack") and snack:
            for s in snack.split(","):
                s = s.strip().lower()
                if s in st.session_state.despensa: st.session_state.despensa.remove(s)
            st.rerun()

    st.divider()
    st.subheader("👨‍🍳 Modo Chef")
    p_chef = st.text_input("¿Qué cocinamos?")
    if st.button("Cocinar 🍳") and p_chef:
        res_r = client.models.generate_content(model='gemini-2.5-flash', contents=f"Receta de {p_chef}. Utensilios: {st.session_state.perfil['utensilios']}.")
        st.markdown(res_r.text)

# ==========================================
# PANTALLA: VIDA SOCIAL
# ==========================================
elif menu == "🍷 Vida Social":
    st.header("🍷 Vida Social")
    t_carta, t_plato, t_resaca = st.tabs(["📜 Carta", "📸 Plato Libre", "🤕 Noche Loca"])
    
    with t_carta:
        st.write("📜 **Escáner de Menús**")
        usar_cam_carta = st.toggle("Usar cámara en vivo", key="tg_carta")
        if usar_cam_carta:
            f_carta = st.camera_input("Enfoca la carta", key="cam_carta_live")
        else:
            f_carta = st.file_uploader("📷 Haz foto a la carta o sube imagen", type=['jpg', 'png'], key="up_carta")
            
        if f_carta and IA_ACTIVA:
            with st.spinner("Analizando carta..."):
                res = client.models.generate_content(model='gemini-2.5-flash', contents=["Recomienda 2 platos sanos del menú.", Image.open(f_carta)])
                st.markdown(res.text)

    with t_plato:
        st.subheader("📸 Analizador de Plato Libre")
        usar_cam_plato = st.toggle("Usar cámara en vivo", key="tg_plato")
        if usar_cam_plato:
            foto_p = st.camera_input("Enfoca tu plato", key="cam_plato_live")
        else:
            foto_p = st.file_uploader("📷 Haz foto al plato o sube imagen", type=['jpg', 'png', 'jpeg'], key="up_plato")
            
        if foto_p and IA_ACTIVA:
            with st.spinner("Calculando..."):
                res = client.models.generate_content(model='gemini-2.5-flash', contents=["Analiza macros y calorías.", Image.open(foto_p)])
                st.markdown(res.text)
                nuevo_fav = st.text_input("❤️ ¿Guardar en favoritos?", key="fav_plato")
                if st.button("Guardar Plato") and nuevo_fav:
                    st.session_state.gustos_positivos.append(nuevo_fav)
                    st.success("Guardado en tu memoria.")
    with t_resaca:
        st.subheader("🤕 Protocolo de Recuperación: Noche Loca")
        st.write("Dime la verdad para que la IA pueda salvarte el día.")
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            intensidad = st.select_slider("🔥 Intensidad de la noche", options=range(1, 11), value=5)
            comida_basura = st.toggle("🍔 ¿Hubo comida basura / ultraprocesados?")
        with c_res2:
            estado_hoy = st.selectbox("💀 Estado actual", ["Supervivencia (Muerte)", "Zombie (Funcional)", "Resacoso pero Guerrero"])
            hidratacion_ayer = st.slider("💧 ¿Bebiste agua entre copas? (1-10)", 1, 10, 3)

        if st.button("🚑 ACTIVAR PROTOCOLO S.O.S", type="primary", use_container_width=True):
            with st.spinner("Calculando daños en tu sistema..."):
                # Lógica de penalización y ajuste
                st.session_state.racha_nutricion = 0
                st.session_state.meta_agua = 4.0 if intensidad > 5 else 3.5
                
                # Prompt específico para recuperación
                p_resaca = f"""
                Protocolo para {st.session_state.perfil['objetivo']}. 
                Noche nivel {intensidad}/10. Comida basura: {comida_basura}. Estado: {estado_hoy}.
                Genera: 1. Bebida electrolítica casera. 2. Ajuste de entreno (¿Descarga?). 3. Comida clave para detox hepático.
                """
                res_resaca = client.models.generate_content(model='gemini-2.5-flash', contents=p_resaca)
                
                st.error(f"🚨 **PROTOCOLO ACTIVADO:** Tu racha se ha reseteado. Meta agua hoy: {st.session_state.meta_agua}L.")
                st.markdown(res_resaca.text)
                if intensidad > 8 or estado_hoy == "Supervivencia (Muerte)":
                    st.warning("⚠️ **ALERTA ENTRENAMIENTO:** Hoy la IA recomienda descanso total o movilidad muy suave. No fuerces el corazón.")
# ==========================================
# PANTALLA: ENTRENADOR IA (JSON INTERACTIVO)
# ==========================================
elif menu == "🏋️‍♂️ Entrenador IA":
    p = st.session_state.perfil
    st.header(f"🏋️‍♂️ Central de Entrenamiento: {p['objetivo']}")
    
    st.info(f"📍 Lugar: {p['lugar_entreno']} | 🕰️ Horario: {p['horario_entreno']} | 💪 Nivel: {p['experiencia']}")

    if st.button("🧠 Generar Rutina Interactiva", type="primary") and IA_ACTIVA:
        with st.spinner("Programando mesociclo interactivo, calentamientos y vídeos..."):
            prompt_rutina = f"""
            Eres un entrenador de élite. Crea rutina de {p['dias_entreno']} días.
            Objetivo: {p['objetivo']}. Experiencia: {p['experiencia']}. Lugar: {p['lugar_entreno']}. 
            Lesiones: {p['lesiones']}. Hormonas: {p['perfil_hormonal']}.
            
            DEVUELVE SOLO UN ARCHIVO JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA:
            {{
              "Día 1: Empuje": {{
                "calentamiento": "Explicación del calentamiento específico de 5 min...",
                "ejercicios": [
                  {{"nombre": "Press Banca", "series": 3, "reps": "8-10", "video": "Busca en YouTube: Press Banca Técnica"}}
                ]
              }},
              "Día 2: Pierna": {{ ... }}
            }}
            """
            try:
                res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_rutina)
                texto_limpio = res.text.replace("```json", "").replace("```", "").strip()
                st.session_state.rutina_estructurada = json.loads(texto_limpio)
                st.session_state.ejercicios_completados = []
            except Exception as e:
                st.error("Error al estructurar el JSON. Inténtalo de nuevo.")

    if st.session_state.rutina_estructurada:
        dias_rutina = list(st.session_state.rutina_estructurada.keys())
        dia_entreno = st.selectbox("¿Qué toca hoy?", dias_rutina)
        
        datos_dia = st.session_state.rutina_estructurada[dia_entreno]
        
        st.warning(f"🔥 **Calentamiento Inteligente:**\n{datos_dia.get('calentamiento', 'Movilidad general 5 min.')}")
        st.divider()

        for i, ej in enumerate(datos_dia.get('ejercicios', [])):
            id_ej = f"{dia_entreno}_{i}"
            st.markdown(f"### 🎯 {ej['nombre']}")
            st.caption(f"📺 {ej.get('video', 'Buscar técnica en YouTube')}")
            
            col_e1, col_e2, col_e3 = st.columns([1, 1, 1])
            with col_e1: st.markdown(f"**Series:** {ej['series']} | **Reps:** {ej['reps']}")
            with col_e2:
                # Registro RPE y Cargas
                carga = st.number_input("Carga (kg)", 0.0, 300.0, step=2.5, key=f"kg_{id_ej}")
                rpe = st.slider("RPE (Esfuerzo 1-10)", 1, 10, 8, key=f"rpe_{id_ej}")
            with col_e3:
                st.write("")
                st.write("")
                if st.button("✅ Registrar y Completar", key=f"done_{id_ej}", type="primary"):
                    st.session_state.historial_cargas[ej['nombre']] = {"kg": carga, "rpe": rpe}
                    st.success("Guardado en tu historial de fuerza.")
                
                # BOTÓN SUSTITUCIÓN IA
                if st.button("🔄 Máquina Ocupada", key=f"swap_{id_ej}"):
                    with st.spinner("Buscando alternativa..."):
                        prompt_cambio = f"Estoy en {p['lugar_entreno']}. Me toca hacer {ej['nombre']} pero está ocupado. Tengo {p['lesiones']}. Dime SOLO el nombre de un ejercicio alternativo directo."
                        if IA_ACTIVA:
                            res_cambio = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_cambio)
                            st.error(f"👉 **Haz esto en su lugar:** {res_cambio.text}")
            st.divider()
            
        if st.button("🏅 FINALIZAR ENTRENAMIENTO DE HOY", use_container_width=True):
            st.session_state.racha_entreno += 1
            st.success("¡Brutal! Racha de entreno aumentada. ¡A recuperar!")
            st.balloons()
            st.divider()
        st.subheader("⏱️ Cronómetro de Descanso")
        desc = st.selectbox("Tiempo", ["60 seg", "90 seg", "2 min", "3 min"])
        if st.button("Iniciar Descanso"): 
            st.warning(f"⏳ {desc} de recuperación iniciados. ¡Coge aire!")

# ==========================================
# PANTALLA: PROGRESO, SALUD Y EL ESPEJO (BLOQUE INTEGRAL)
# ==========================================
else:
    st.header("🩸 Dashboard de Salud Total")
    
    # DEFINICIÓN DE PESTAÑAS (Aquí estaba el error)
    t_medidas, t_espejo, t_sangre = st.tabs(["📉 Métricas Clínicas", "📸 El Espejo", "🧪 Análisis de Sangre"])
    
    with t_medidas:
        with st.form("registro_salud"):
            st.subheader("Métricas Físicas")
            c1, c2, c3, c4 = st.columns(4)
            with c1: m_peso = st.number_input("Peso (kg)", 40.0, 200.0, st.session_state.perfil.get('peso', 75.0), step=0.1)
            with c2: m_grasa = st.number_input("Grasa (%)", 3.0, 60.0, 15.0, step=0.1)
            with c3: m_cintura = st.number_input("Cintura (cm)", 50.0, 200.0, 80.0, step=0.5)
            with c4: m_pasos = st.number_input("Pasos/día", 0, 50000, 8000)
            
            st.subheader("Sensores de Salud Interna")
            c5, c6, c7 = st.columns(3)
            with c5: m_fc = st.number_input("FC Reposo (Corazón)", 30, 120, 60)
            with c6: m_dig = st.selectbox("Digestión Hoy", ["Perfecta (Plano)", "Regular", "Pesada / Inflamado"])
            with c7: m_snc = st.slider("Energía SNC (1=Muerto, 10=Dios)", 1, 10, 7)
            
            if st.form_submit_button("💾 Guardar y Analizar"):
                fila = pd.DataFrame([{"Fecha": time.strftime("%d/%m/%Y"), "Peso (kg)": m_peso, "Grasa (%)": m_grasa, "Cintura (cm)": m_cintura, "Pasos": m_pasos, "FC Reposo": m_fc, "Digestión": m_dig, "Fatiga SNC": m_snc}])
                st.session_state.historial_biometrico = pd.concat([st.session_state.historial_biometrico, fila], ignore_index=True)
                st.success("¡Datos guardados!")
                
        if not st.session_state.historial_biometrico.empty:
            st.line_chart(st.session_state.historial_biometrico.set_index("Fecha")[["Peso (kg)", "Grasa (%)", "Cintura (cm)"]])
            
            if st.button("🧠 IA: Evaluación de Fatiga y Digestión", type="primary") and IA_ACTIVA:
                with st.spinner("Analizando tu sistema nervioso y digestivo..."):
                    df_str = st.session_state.historial_biometrico.tail(3).to_string()
                    prompt_med = f"Analiza los últimos 3 días: {df_str}. Fíjate en la Digestión y Fatiga SNC. Si la fatiga está baja (<5), ordénale una 'Semana de Descarga'. Si la digestión está inflamada, sugiérele cambios en la dieta."
                    res_a = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_med)
                    st.info(res_a.text)

    with t_espejo:
        st.subheader("📸 Tu Evolución Visual")
        st.write("Sube tu foto de progreso mensual para comparar.")
        foto_progreso = st.file_uploader("Sube tu foto", type=['jpg', 'png', 'jpeg'])
        if st.button("💾 Guardar en Galería") and foto_progreso:
            st.session_state.galeria_espejo.append({"fecha": time.strftime("%d/%m/%Y"), "foto": Image.open(foto_progreso)})
            st.success("¡Foto guardada en tu galería!")
            
        if st.session_state.galeria_espejo:
            st.divider()
            cols_galeria = st.columns(3)
            for idx, item in enumerate(st.session_state.galeria_espejo):
                with cols_galeria[idx % 3]:
                    st.image(item["foto"], caption=f"📅 {item['fecha']}", use_container_width=True)

    with t_sangre:
        st.subheader("🧪 Análisis de Sangre y Biomarcadores")
        st.warning("🩺 Aviso Médico: Análisis orientativo. Consulta a tu médico.")
        foto_sangre = st.file_uploader("Sube foto de tus análisis", type=['png', 'jpg', 'jpeg'], key="up_sangre")
        if foto_sangre and IA_ACTIVA:
            if st.button("🔬 Analizar Analítica", type="primary"):
                with st.spinner("Procesando analítica..."):
                    res_sangre = client.models.generate_content(model='gemini-2.5-flash', contents=["Analiza estos biomarcadores cruzándolos con los objetivos del usuario.", Image.open(foto_sangre)])
                    st.markdown(res_sangre.text)
