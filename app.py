import streamlit as st
import pandas as pd
import time
import os
import json
import datetime
from dotenv import load_dotenv
from google import genai
from PIL import Image

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA Y UI
# ==========================================
load_dotenv()
st.set_page_config(page_title="FitChef AI Pro | Nivel God-Tier", layout="wide", page_icon="🚀")
# --- PARCHE DE VISIBILIDAD (Añadir al principio del script) ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; color: #00FFA3 !important; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    [data-testid="stExpander"] { border: 1px solid #333; background: #0e1117; }
    /* Fix para tarjetas blancas en modo oscuro */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN AL MOTOR IA (GEMINI 2.5 PRO)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

try:
    # Usamos la API de pago para desatar todo el potencial
    client = genai.Client(api_key=api_key)
    IA_ACTIVA = True
    MODELO_IA = 'gemini-2.5-pro' 
except Exception as e:
    st.error("⚠️ Error crítico: API Key no detectada. La IA está apagada.")
    IA_ACTIVA = False

# ==========================================
# 3. MEMORIA RAM DE LA APP (SESSION STATE)
# ==========================================
# Aquí definimos la estructura del usuario para que NUNCA se borre al recargar

# --- BUSCA ESTO AL PRINCIPIO DE TU CÓDIGO ---
if 'perfil' not in st.session_state:
    st.session_state.perfil = {
        "nombre": "", "sexo": "Hombre", "edad": 25, "peso": 70.0, "altura": 170, "actividad": "Moderada",
        "hora_despertar": datetime.time(7, 0), "hora_dormir": datetime.time(23, 0),
        "digestion": "Normal", "cafeina": "Normal", "lesiones_historial": "",
        "objetivo": "Estética Funcional", "experiencia": "Intermedio",
        "lugar_entreno": "Gimnasio Comercial", "horario_entreno": "Tarde", "dias_entreno": 4,
        "estres_base": "Moderado", "sueno_base": "Normal (6-8h)",
        "dieta_base": "Omnívora", "n_comidas": 4, "ayuno": False,
        "presupuesto": "Moderado", "estilo_cocina": "Rápido (15-20 min)",
        "utensilios": ["Sartén", "Microondas"], "suplementos": "", 
        "restricciones": "",  # <--- ¡ESTA ES LA QUE TE FALTA!
        "gustos_positivos": "", "gustos_negativos": "", "alergias": "",
        "bio_hacker_mode": False, "protocolo_metabolico": "Balanceado",
        "salud_intestinal": [], "semana_mesociclo": 1, "perfil_hormonal": "Ninguno"
    }

# B) Arrays y Contadores de Nutrición y Progreso
for key, default in {
    'despensa': [], 
    'plan_estructurado': None, 
    'comidas_completadas': [],
    'gustos_positivos': [], 
    'gustos_negativos': [], 
    'agua_bebida': 0.0, 
    'meta_agua': 2.5,
    'rutina_estructurada': None, 
    'historial_cargas': {},
    'racha_nutricion': 0, 
    'racha_entreno': 0, 
    'menu_val': "🏠 Inicio",
    'modo_bestia': False # Magia extra: Interruptor para días de alta energía
}.items():
    if key not in st.session_state: 
        st.session_state[key] = default

# C) El Analista Biométrico (DataFrames y Mapas Complejos)
if 'historial_biometrico' not in st.session_state: 
    st.session_state.historial_biometrico = pd.DataFrame(columns=["Fecha", "Peso (kg)"])

# D) MAPA DE FATIGA MUSCULAR (La idea del siglo)
# 100% = Totalmente recuperado | 0% = Frito/Destruido
if 'mapa_muscular' not in st.session_state:
    st.session_state.mapa_muscular = {
        "Pecho": 100, "Espalda": 100, "Cuádriceps": 100, "Isquios_Glúteo": 100, 
        "Hombros": 100, "Bíceps": 100, "Tríceps": 100, "Core": 100, "SNC": 100
    }

# E) Readiness Score (Check-in Diario Dinámico)
if 'checkin_hoy' not in st.session_state:
    st.session_state.checkin_hoy = {
        'horas_sueno_anoche': 7, 
        'nivel_agujetas': 3, 
        'estres_hoy': "Normal",
        'realizado': False
    }

if 'historial_medico' not in st.session_state:
    st.session_state.historial_medico = {"analiticas": "Sin datos.", "lesiones": "Sin lesiones."}

# ==========================================
# 4. FUNCIONES DEL SISTEMA (Motor Interno)
# ==========================================
def cambiar_pestana(nombre):
    """Función maestra para navegar con botones en lugar de clics en el menú"""
    st.session_state.menu_val = nombre
    st.rerun()

def generar_ics(plan_json):
    """Convierte el JSON de la dieta en un archivo de Calendario (Apple/Google)"""
    lineas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FitChef AI//ES"]
    dias_map = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6}
    hoy = datetime.date.today()
    for dia_nombre, comidas in plan_json.items():
        if dia_nombre not in dias_map: continue
        delta_dias = (dias_map[dia_nombre] - hoy.weekday()) % 7
        fecha_evento = hoy + datetime.timedelta(days=delta_dias)
        hora_comida = 9 # Empezamos a las 9:00am
        for comida in comidas:
            dt_start = fecha_evento.strftime("%Y%m%d") + f"T{hora_comida:02d}0000"
            dt_end = fecha_evento.strftime("%Y%m%d") + f"T{hora_comida+1:02d}0000"
            lineas.extend([
                "BEGIN:VEVENT", 
                f"SUMMARY:🍽️ {comida['tipo']} - {comida['plato']}", 
                f"DESCRIPTION:Ingredientes: {', '.join(comida['ingredientes'])}", 
                f"DTSTART:{dt_start}", 
                f"DTEND:{dt_end}", 
                "END:VEVENT"
            ])
            hora_comida += 3 # Espaciamos 3 horas por comida
    lineas.append("END:VCALENDAR")
    return "\n".join(lineas)
# ==========================================
# 5. BARRA LATERAL (El HUD Permanente)
# ==========================================
with st.sidebar:
    st.title("🛡️ FitChef AI")
    st.caption("Modo Dios: ACTIVADO" if IA_ACTIVA else "Modo IA: OFFLINE")
    
    st.subheader("🔥 Tus Rachas")
    col_r1, col_r2 = st.columns(2)
    with col_r1: st.metric(label="🥗 Dieta", value=f"{st.session_state.racha_nutricion} pts")
    with col_r2: st.metric(label="🏋️ Entreno", value=f"{st.session_state.racha_entreno} d")
    
    st.subheader("💧 Hidratación Hoy")
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1: st.metric(label=f"Meta: {st.session_state.meta_agua}L", value=f"{st.session_state.agua_bebida:.2f} L")
    with col_w2: 
        if st.button("🥤 +0.25L", use_container_width=True): 
            st.session_state.agua_bebida += 0.25
            st.rerun()
    
    if st.session_state.agua_bebida >= st.session_state.meta_agua:
        st.success("¡Meta de hidratación alcanzada! 🌊")
        
    st.divider()
    # Interruptor del Modo Bestia
    st.session_state.modo_bestia = st.toggle("🔥 Modo Bestia", value=st.session_state.modo_bestia, help="Actívalo los días que te sientas con energía infinita. La IA subirá la intensidad.")

# ==========================================
    # 💾 SISTEMA DE GUARDADO Y CARGA (BÓVEDA)
    # ==========================================
    st.sidebar.divider()
    st.sidebar.subheader("💾 Tu Bóveda Biológica")
    
    # 1. PREPARAR LOS DATOS PARA DESCARGAR
    # Recopilamos solo lo importante (evitamos basura temporal de la sesión)
    datos_exportar = {
        "perfil": st.session_state.perfil,
        "despensa": st.session_state.despensa,
        "mapa_muscular": st.session_state.mapa_muscular,
        "historial_medico": st.session_state.get('historial_medico', {"analiticas": "Sin datos.", "lesiones": "Sin lesiones."}),
        "maximos_rm": st.session_state.get('maximos_rm', {}),
        "racha_entreno": st.session_state.racha_entreno
    }
    
    # Convertimos el diccionario a un texto JSON formateado
    json_guardado = json.dumps(datos_exportar, indent=4)
    
    # Botón de Descarga
    st.sidebar.download_button(
        label="⬇️ Descargar mi Perfil Biológico",
        data=json_guardado,
        file_name="mi_human_os_backup.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.sidebar.write("---")
    
    # 2. CARGAR UNA COPIA DE SEGURIDAD ANTERIOR
    archivo_carga = st.sidebar.file_uploader("📂 Restaurar Copia de Seguridad", type=["json"], key="carga_boveda")
    
    if archivo_carga is not None:
        try:
            datos_cargados = json.load(archivo_carga)
            
            # Inyectamos los datos cargados directamente en las venas de la app
            for clave, valor in datos_cargados.items():
                st.session_state[clave] = valor
                
            st.sidebar.success("¡Perfil Restaurado con Éxito!")
            time.sleep(1)
            st.rerun() # Recargamos la app para que aplique los cambios visualmente
        except Exception as e:
            st.sidebar.error("Error al leer el archivo. ¿Es un backup válido?")

# ==========================================
# 6. NAVEGACIÓN PRINCIPAL
# ==========================================
opciones_menu = ["🏠 Inicio", "👤 Perfil", "🏥 Clínica Bio-Hacking", "🥗 Nutrición Pro", "🏋️‍♂️ Entrenador IA", "🍷 Vida Social", "🩸 Progreso"]
menu = st.radio(
    "Navegación:", 
    opciones_menu, 
    index=opciones_menu.index(st.session_state.menu_val), 
    horizontal=True,
    key="nav_principal"
)
st.divider()

# ==========================================
# 🏠 PANTALLA: INICIO (HUB DE ALTO RENDIMIENTO)
# ==========================================
if menu == "🏠 Inicio":
    st.title("🚀 FitChef AI")
    st.subheader(f"Ecosistema de Bio-Hacking activo. ¿Qué destruimos hoy?")
    
    # --- CHECK-IN DIARIO (READINESS SCORE) ---
    if not st.session_state.checkin_hoy.get('realizado', False):
        with st.container(border=True):
            st.markdown("### 📊 Check-in Diario (Readiness Score)")
            st.write("Dime cómo estás hoy. La IA ajustará tus macros y tu entreno al instante.")
            
            c_ck1, c_ck2, c_ck3 = st.columns(3)
            with c_ck1:
                horas_sueno = st.number_input("Horas de sueño anoche", 1.0, 14.0, float(st.session_state.checkin_hoy['horas_sueno_anoche']), step=0.5)
            with c_ck2:
                agujetas = st.slider("Nivel de Agujetas/Fatiga (1=Fresco, 10=Destruido)", 1, 10, st.session_state.checkin_hoy['nivel_agujetas'])
            with c_ck3:
                estres = st.selectbox("Nivel de Estrés Mental", ["Bajo", "Normal", "Alto (Cortisol por las nubes)"], index=["Bajo", "Normal", "Alto (Cortisol por las nubes)"].index(st.session_state.checkin_hoy['estres_hoy']) if st.session_state.checkin_hoy['estres_hoy'] in ["Bajo", "Normal", "Alto (Cortisol por las nubes)"] else 1)
            
            if st.button("💾 Calibrar mi día", type="primary"):
                st.session_state.checkin_hoy = {
                    'horas_sueno_anoche': horas_sueno,
                    'nivel_agujetas': agujetas,
                    'estres_hoy': estres,
                    'realizado': True
                }
                st.success("¡Sistema calibrado! La IA ha tomado nota.")
                st.rerun()
    else:
        st.success("✅ Check-in diario completado. Sistema calibrado a tu estado actual.")
        if st.button("🔄 Resetear Check-in"):
            st.session_state.checkin_hoy['realizado'] = False
            st.rerun()

    # --- FITCHEF VOICE (COMANDOS POR AUDIO) ---
    st.markdown("### 🎙️ FitChef Voice (Beta)")
    audio_grabado = st.audio_input("Cuéntame qué has comido, cómo te sientes o pide un cambio rápido:")
    if audio_grabado and IA_ACTIVA:
        with st.spinner("Escuchando y transcribiendo..."):
            try:
                # Aquí enviamos el audio directamente a Gemini 2.5 Pro
                res_audio = client.models.generate_content(
                    model=MODELO_IA,
                    contents=["Eres el asistente personal de fitness. Transcribe y resume brevemente qué acción debe tomar el sistema según este audio.", audio_grabado]
                )
                st.info(f"🤖 **Jarvis dice:** {res_audio.text}")
            except Exception as e:
                st.error("Error al procesar el audio. Asegúrate de hablar claro.")

    st.divider()

    # --- ACCESOS DIRECTOS (BOTONES) ---
    st.write("### ⚡ Accesos Rápidos")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("⚙️ CONFIGURAR PERFIL", use_container_width=True): cambiar_pestana("👤 Perfil")
        st.caption("Ajusta tu biometría, hormonas y logística.")
    with c_btn2:
        if st.button("🥗 IR A NUTRICIÓN", use_container_width=True, type="primary"): cambiar_pestana("🥗 Nutrición Pro")
        st.caption("Genera menús y gestiona tu despensa.")
    with c_btn3:
        if st.button("🏋️‍♂️ IR A ENTRENAMIENTO", use_container_width=True, type="primary"): cambiar_pestana("🏋️‍♂️ Entrenador IA")
        st.caption("Tu rutina con análisis de fatiga y técnica.")
        
    st.image("https://images.unsplash.com/photo-1594882645126-14020914d58d?q=80&w=2085", use_container_width=True)

# ==========================================
# 👤 PANTALLA: PERFIL GOD-TIER
# ==========================================
elif menu == "👤 Perfil":
    st.header("👤 Perfil Biológico y Logístico")
    p = st.session_state.perfil

    # --- BLOQUE 1: BIOMETRÍA Y OBJETIVOS ---
    with st.container(border=True):
        st.subheader("🧬 Biometría y Objetivo")
        col1, col2, col3 = st.columns(3)
        with col1:
            p['sexo'] = st.selectbox("Sexo Biológico", ["Hombre", "Mujer"], index=0 if p['sexo']=="Hombre" else 1)
            p['edad'] = st.number_input("Edad", 14, 100, p['edad'])
        with col2:
            p['peso'] = st.number_input("Peso (kg)", 30.0, 250.0, float(p['peso']))
            p['altura'] = st.number_input("Altura (cm)", 100, 250, p['altura'])
        with col3:
            p['objetivo'] = st.selectbox("Objetivo Principal", ["Perder Grasa", "Ganar Músculo", "Rendimiento Atlético", "Longevidad"])
            p['actividad'] = st.selectbox("Nivel de Actividad Diaria", ["Sedentario", "Moderada", "Activa", "Muy Activa"])

    # --- BLOQUE 2: ENTRENAMIENTO ---
    with st.container(border=True):
        st.subheader("🏋️‍♂️ Configuración de Entrenamiento")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            p['experiencia'] = st.selectbox("Experiencia", ["Principiante", "Intermedio", "Avanzado"])
            p['lugar_entreno'] = st.selectbox("Lugar", ["Gimnasio Comercial", "En Casa (Mínimo material)", "Calistenia / Parque"])
        with col_e2:
            p['dias_entreno'] = st.slider("Días por semana", 1, 7, p.get('dias_entreno', 4))
            p['horario_entreno'] = st.selectbox("Horario", ["Mañana", "Mediodía", "Tarde", "Noche"])
        with col_e3:
            p['estres_base'] = st.select_slider("Nivel de Estrés", options=["Bajo", "Moderado", "Alto", "Crítico"])
            p['sueno_base'] = st.selectbox("Calidad de Sueño", ["Mala (<6h)", "Normal (6-8h)", "Reparadora (>8h)"])

    # --- BLOQUE 3: LOGÍSTICA Y COCINA ---
    with st.container(border=True):
        st.subheader("🍳 Logística y Nutrición Base")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            p['dieta_base'] = st.selectbox("Identidad Alimentaria", ["Omnívoro", "Flexitariano", "Pescetariano", "Vegetariano", "Vegano (WFPB)"])
            p['estilo_cocina'] = st.selectbox("Tiempo para Cocinar", ["Rápido (15-20 min)", "Gourmet", "Batch-Cooking (Domingo)"])
            p['presupuesto'] = st.selectbox("Presupuesto Semanal", ["Económico", "Moderado", "Premium"])
        with col_c2:
            p['utensilios'] = st.multiselect("Utensilios disponibles", 
                ["Sartén", "Olla", "Horno", "Airfryer", "Thermomix", "Vaporera", "Microondas", "Batidora de vaso"],
                default=p.get('utensilios', ["Sartén", "Microondas"]))
            p['realidad_diaria'] = st.selectbox("Contexto de comidas", ["Como en casa", "Llevo Tupper", "Restaurante / Menú del día"])

    # --- BLOQUE 4: SEGURIDAD Y SUPLEMENTOS ---
    with st.container(border=True):
        st.subheader("💊 Seguridad y Arsenal")
        p['restricciones'] = st.text_area("Alergias, intolerancias o alimentos que ODIAS", value=p['restricciones'], placeholder="Ej: Celíaco, odio el pepino...")
        p['suplementos_disponibles'] = st.text_area("Suplementos que ya tienes", value=p['suplementos_disponibles'], placeholder="Ej: Creatina, Proteína Whey, Omega 3, Magnesio...")

    # --- BLOQUE 5: EL INTERRUPTOR BIO-HACKER ---
    st.divider()
    p['bio_hacker_mode'] = st.toggle("🚀 ACTIVAR MODO BIO-HACKER & CLÍNICO", value=p['bio_hacker_mode'])

    if p['bio_hacker_mode']:
        with st.container(border=True):
            st.warning("⚠️ Modo Bio-Hacker: Ajustando protocolos metabólicos y periodización celular.")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                p['protocolo_metabolico'] = st.selectbox("Protocolo de Energía", 
                    ["Balanceado", "Keto Cíclica", "Carb Cycling", "Paleo", "Carnívora (Lion Diet)", "Dieta Vertical"])
            with col_b2:
                p['salud_intestinal'] = st.multiselect("Salud Intestinal", ["Low FODMAP", "AIP (Autoinmune)", "Baja en Histamina"])

            st.write("---")
            if p['sexo'] == "Mujer":
                st.subheader("🩸 Bio-Reloj Hormonal")
                semana = st.slider("Semana del Ciclo", 1, 4, p['semana_mesociclo'])
                p['semana_mesociclo'] = semana
                fases = {
                    1: ("Fase Menstrual", "🩸 Descarga del SNC. Hierro alto. RIR 3-4."),
                    2: ("Fase Folicular", "🟢 Pico de fuerza. Carga de CH permitida. RIR 0-1."),
                    3: ("Fase Ovulatoria", "🟡 Testosterona alta. Cuidado ligamentos. RIR 1."),
                    4: ("Fase Lútea", "🟠 Metabolismo +10% kcal. Grasas altas. RIR 2-3.")
                }
                p['perfil_hormonal'], desc = fases[semana]
                st.info(f"**{p['perfil_hormonal']}:** {desc}")
            else:
                st.subheader("📅 Periodización del Mesociclo")
                semana = st.slider("Semana de carga", 1, 4, p['semana_mesociclo'])
                p['semana_mesociclo'] = semana
                p['perfil_hormonal'] = "Ninguno"
                desc_h = {1:"Adaptación (VME)", 2:"Sobrecarga Progresiva", 3:"Pico de Intensidad (MRV)", 4:"Descarga (Deload)"}
                st.info(f"**Fase actual:** {desc_h[semana]}")

    if st.button("💾 SINCRONIZAR ADN BIOLÓGICO", type="primary", use_container_width=True):
        st.success("¡Perfil Human OS actualizado!")
        st.balloons()
# ==========================================
# 🥗 PANTALLA: NUTRICIÓN PRO (El Arsenal del Chef)
# ==========================================
elif menu == "🥗 Nutrición Pro":
    st.header("🥗 Central Nutricional y Chef IA")
    
    # --- 1. LÓGICA DE DESPENSA VACÍA (LISTA DE COMPRA INICIAL) ---
    if not st.session_state.despensa:
        st.warning("🚨 Tu despensa está vacía. Para empezar con el pie derecho, necesitas un arsenal básico.")
        if st.button("🛒 GENERAR MI LISTA DE COMPRA INICIAL (BIO-HACKED)", type="primary", use_container_width=True):
            if IA_ACTIVA:
                with st.spinner("El Chef está analizando tu biometría para tu primera compra..."):
                    p = st.session_state.perfil
                    prompt_compra = f"""
                    Eres un experto en nutrición y logística. Genera una lista de compra inicial para un {p['sexo']} de {p['peso']}kg con objetivo {p['objetivo']}.
                    REGLAS:
                    - Incluye fuentes de grasas insaturadas (aguacate, AOVE, nueces).
                    - Incluye hidratos complejos para el glucógeno.
                    - Ten en cuenta su presupuesto {p['presupuesto']} y dieta {p['dieta_tipo']}.
                    - Formato: Devuelve una lista categorizada (Proteínas, Grasas, Hidratos, Vegetales).
                    """
                    res = client.models.generate_content(model=MODELO_IA, contents=prompt_compra)
                    st.session_state.lista_compra_sugerida = res.text
        
        if 'lista_compra_sugerida' in st.session_state:
            with st.container(border=True):
                st.markdown("### 📋 Tu Lista de Compra Estratégica")
                st.write(st.session_state.lista_compra_sugerida)
                if st.button("✅ Ya he comprado todo (Llenar despensa automáticamente)"):
                    # Extraemos los nombres de alimentos de la lista sugerida (simulado)
                    st.session_state.despensa = ["huevos", "pollo", "arroz", "aguacate", "avena", "nueces", "espinacas", "aceite de oliva"]
                    st.success("¡Despensa cargada con los básicos! Ahora ya podemos cocinar.")
                    st.rerun()
        st.divider()

    # --- 2. GESTIÓN DE DESPENSA (LOS 5 ESCÁNERES MULTIMODALES) ---
    with st.expander("🛒 Gestionar mi Despensa e Ingredientes", expanded=not bool(st.session_state.despensa)):
        t_nev, t_ticket, t_barras, t_voz, t_man = st.tabs([
            "📸 Nevera/Despensa", "🧾 Ticket", "🔍 Código de Barras", "🎙️ Dictado", "⌨️ Manual"
        ])
        
        # 1. ESCÁNER DE NEVERA
        with t_nev:
            col_n1, col_n2 = st.columns(2)
            with col_n1: foto_n = st.camera_input("Hacer foto a la nevera", key="cam_nev")
            with col_n2: archivo_n = st.file_uploader("O subir desde galería", type=['jpg', 'png', 'jpeg'], key="up_nev")
            
            input_nevera = foto_n if foto_n else archivo_n
            if input_nevera and IA_ACTIVA:
                with st.spinner("Chef IA escaneando..."):
                    res = client.models.generate_content(model=MODELO_IA, contents=["Lista alimentos saludables separados por comas.", Image.open(input_nevera)])
                    nuevos = [i.strip().lower() for i in res.text.split(",") if i.strip()]
                    st.session_state.despensa = list(set(st.session_state.despensa + nuevos))
                    st.success(f"Detectados: {', '.join(nuevos)}")
                    time.sleep(1); st.rerun()

        # 2. ESCÁNER DE TICKETS
        with t_ticket:
            st.info("🧾 Haz una foto al ticket en directo o súbela de tu galería.")
            col_t1, col_t2 = st.columns(2)
            with col_t1: foto_t = st.camera_input("Hacer foto al ticket", key="cam_tick")
            with col_t2: archivo_t = st.file_uploader("O subir ticket", type=['jpg', 'png', 'jpeg'], key="up_tick")
            
            input_ticket = foto_t if foto_t else archivo_t
            if input_ticket and IA_ACTIVA:
                with st.spinner("Leyendo ticket y descartando ultraprocesados..."):
                    res = client.models.generate_content(model=MODELO_IA, contents=["Extrae nombres de alimentos saludables del ticket separados por comas. Ignora precios y basura.", Image.open(input_ticket)])
                    nuevos = [i.strip().lower() for i in res.text.split(",") if i.strip()]
                    st.session_state.despensa = list(set(st.session_state.despensa + nuevos))
                    st.success("Ticket hackeado. Despensa actualizada.")
                    time.sleep(1); st.rerun()

        # 3. ESCÁNER DE CÓDIGO DE BARRAS / PRODUCTOS
        with t_barras:
            st.info("🔍 Haz una foto nítida al código de barras o al envase del producto.")
            col_b1, col_b2 = st.columns(2)
            with col_b1: foto_b = st.camera_input("Escanear código", key="cam_bar")
            with col_b2: archivo_b = st.file_uploader("O subir foto del código", type=['jpg', 'png', 'jpeg'], key="up_bar")
            
            input_barras = foto_b if foto_b else archivo_b
            if input_barras and IA_ACTIVA:
                with st.spinner("Buscando base de datos nutricional..."):
                    res = client.models.generate_content(model=MODELO_IA, contents=["¿Qué alimento es este código de barras o envase? Solo devuelve el nombre genérico del alimento en español.", Image.open(input_barras)])
                    nuevo_prod = res.text.strip().lower()
                    st.session_state.despensa.append(nuevo_prod)
                    st.success(f"Producto identificado y añadido: {nuevo_prod.title()}")
                    time.sleep(1); st.rerun()

        # 4. DICTADO POR VOZ
        with t_voz:
            audio = st.audio_input("Dicta tus ingredientes:")
            if audio and IA_ACTIVA:
                with st.spinner("Transcribiendo ingredientes..."):
                    res = client.models.generate_content(model=MODELO_IA, contents=["Extrae los alimentos de este audio separados por comas.", audio])
                    nuevos = [i.strip().lower() for i in res.text.split(",") if i.strip()]
                    st.session_state.despensa = list(set(st.session_state.despensa + nuevos))
                    st.success(f"Añadidos por voz: {', '.join(nuevos)}")
                    time.sleep(1); st.rerun()

        # 5. AÑADIDO MANUAL
        with t_man:
            manual = st.text_input("Añadir manual (ej: atún, pasta, huevos):")
            if st.button("➕ Añadir a Despensa", use_container_width=True):
                st.session_state.despensa = list(set(st.session_state.despensa + [i.strip().lower() for i in manual.split(",") if i.strip()]))
                st.rerun()

        st.divider()
        if st.session_state.despensa:
            st.write(f"🍏 **Tu Arsenal Actual:** {', '.join(st.session_state.despensa).title()}")
            if st.button("🗑️ VACIAR DESPENSA A 0", type="secondary"):
                st.session_state.despensa = []
                st.session_state.pop('lista_compra_sugerida', None)
                st.rerun()

    # --- 3. EL CHEF IA (GENERADOR CON RECETAS DETALLADAS Y MACROS) ---
    if st.button("👨‍🍳 GENERAR PLAN SEMANAL Y RECETAS (GOD-TIER)", type="primary", use_container_width=True):
        if IA_ACTIVA:
            with st.spinner("El Chef está cuadrando tus macros y diseñando la semana..."):
                p = st.session_state.perfil
                prompt = f"""
                Eres un Chef Michelin y Nutricionista Clínico. Genera una dieta semanal de Lunes a Domingo.
                
                🩺 [HISTORIAL MÉDICO Y ANALÍTICAS]: {st.session_state.historial_medico.get('analiticas', 'Sin datos')}
                
                REGLAS: 
                1. Grasas min 1g/kg. Post-entreno ({p.get('horario_entreno', 'Tarde')}) alto en CH. 
                2. Fase Hormonal: {p.get('perfil_hormonal', 'Ninguno')}. 
                3. Usa esta despensa si es posible: {st.session_state.despensa}.
                4. OBLIGATORIO: Adapta los ingredientes y macros para corregir los problemas del [HISTORIAL MÉDICO] (ej: si falta hierro pon alimentos ricos en él + Vitamina C, si el azúcar es alto baja el índice glucémico).
                🩺 [FASE DEL MESOCICLO]: Semana {p.get('semana_mesociclo', 1)} de 4. 
                - Si es Semana 4 (Descarga/Deload): Aumenta ligeramente los carbohidratos (Refeed/Diet Break) para dar un respiro a la adaptación metabólica.
                
                DEVUELVE ÚNICA Y EXCLUSIVAMENTE UN JSON VÁLIDO. NI UNA SOLA PALABRA MÁS. SIN SALUDOS.
                Estructura EXACTA obligatoria:
                {{
                  "Lunes": [
                    {{
                      "tipo": "Desayuno",
                      "plato": "Nombre del plato",
                      "ingredientes": ["ingrediente 1", "ingrediente 2"],
                      "instrucciones": "Paso a paso breve",
                      "nota_ciencia": "Bio-hack de este plato y cómo ayuda a tu Historial Médico",
                      "kcal": 400,
                      "prot": 30,
                      "cho": 40,
                      "fat": 15
                    }}
                  ],
                  "Martes": [ ... ]
                }}
                """
                try:
                    res = client.models.generate_content(model=MODELO_IA, contents=prompt)
                    
                    # Limpieza extrema: buscamos solo lo que hay entre la primera { y la última }
                    texto = res.text.replace("```json", "").replace("```", "").strip()
                    inicio = texto.find('{')
                    fin = texto.rfind('}') + 1
                    
                    if inicio != -1 and fin != 0:
                        texto_limpio = texto[inicio:fin]
                        st.session_state.plan_estructurado = json.loads(texto_limpio)
                        st.success("¡Dieta lista y emplatada!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        raise ValueError("La IA no devolvió corchetes de JSON.")
                        
                except Exception as e: 
                    st.error(f"Error en la cocina. Detalle técnico: {e}")
                    st.info("💡 Sugerencia: Dale al botón de nuevo. A veces la IA tiene un pequeño lapsus de formato.")

  # --- 4. VISUALIZACIÓN, MACROS, FALTANTES Y AUDITORÍA DE DESVÍOS ---
    if st.session_state.plan_estructurado: # <--- Corregido de 'structured' a 'estructurado'
        dia_sel = st.selectbox("📅 Selecciona Día:", list(st.session_state.plan_estructurado.keys()))
        
        # A) RESUMEN DE MACROS DEL DÍA
        macros_dia = {"kcal": 0, "prot": 0, "cho": 0, "fat": 0}
        for c in st.session_state.plan_estructurado.get(dia_sel, []):
            macros_dia["kcal"] += c.get("kcal", 0)
            macros_dia["prot"] += c.get("prot", 0)
            macros_dia["cho"] += c.get("cho", 0)
            macros_dia["fat"] += c.get("fat", 0)
            
        st.subheader(f"📊 Resumen Nutricional: {dia_sel}")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("🔥 Kcal", f"{macros_dia['kcal']}")
        m_col2.metric("🥩 Prot", f"{macros_dia['prot']}g")
        m_col3.metric("🍞 Hidratos", f"{macros_dia['cho']}g")
        m_col4.metric("🥑 Grasas", f"{macros_dia['fat']}g")

        # B) ESCÁNER DE FALTANTES CRÍTICOS
        ingredientes_dia = []
        for c in st.session_state.plan_estructurado.get(dia_sel, []):
            ingredientes_dia.extend([i.lower() for i in c.get('ingredientes', [])])
        
        faltantes = [i for i in ingredientes_dia if not any(d in i or i in d for d in st.session_state.despensa)]
        
        if faltantes:
            with st.status("⚠️ Alerta de Suministros: Faltan ingredientes para hoy", state="error"):
                st.write("Para cumplir el plan al 100%, necesitas comprar:")
                for f in set(faltantes): st.write(f"❌ {f.title()}")
        else:
            st.success("✅ Tienes todo para cumplir el plan de hoy.")

        st.divider()

        # C) DETALLE DE LAS COMIDAS CON AUDITORÍA
        for i, c in enumerate(st.session_state.plan_estructurado.get(dia_sel, [])):
            with st.expander(f"🍽️ {c['tipo']}: {c['plato']} ({c.get('kcal', 0)} kcal)", expanded=True):
                st.info(f"🧬 **Bio-Hack:** {c.get('nota_ciencia', 'Optimización metabólica activa.')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**🛒 Ingredientes:**")
                    for ing in c.get('ingredientes', []): # <--- Corregido de 'ingredients' a 'ingredientes'
                        tienes = any(d in ing.lower() or ing.lower() in d for d in st.session_state.despensa)
                        st.write(f"{'✅' if tienes else '❌'} {ing}")
                with col2:
                    st.write("**👨‍🍳 Instrucciones:**")
                    st.write(c.get('instrucciones', 'Cocinar a fuego lento y disfrutar.')) # <--- Corregido de 'instructions'
                
                # BOTONERA DE ACCIÓN DOBLE
                c_act1, c_act2 = st.columns(2)
                
                with c_act1:
                    if st.button(f"✅ Hecho (Restar Plan)", key=f"ok_{dia_sel}_{i}"):
                        for ing in c.get('ingredientes', []):
                            for item in st.session_state.despensa:
                                if item in ing.lower() or ing.lower() in item:
                                    try: st.session_state.despensa.remove(item); break
                                    except: pass
                        st.session_state.racha_nutricion += 10
                        st.balloons()
                        st.rerun()

                with c_act2:
                    if st.button(f"📸 He comido otra cosa", key=f"fail_{dia_sel}_{i}"):
                        st.session_state[f"rebelde_{i}"] = True

                # ZONA DE AUDITORÍA REBELDE
                if st.session_state.get(f"rebelde_{i}", False):
                    with st.container(border=True):
                        st.write("🕵️‍♂️ **Auditoría IA:** Sube foto de lo que has comido realmente.")
                        foto_rebelde = st.file_uploader("Captura del plato real", type=['jpg', 'png'], key=f"foto_reb_{i}")
                        if foto_rebelde and IA_ACTIVA:
                            with st.spinner("Analizando plato improvisado..."):
                                res = client.models.generate_content(
                                    model=MODELO_IA,
                                    contents=["Analiza este plato. Dime qué ingredientes lleva que suelan estar en una despensa. Sepáralos por comas.", Image.open(foto_rebelde)]
                                )
                                ingredientes_f = [x.strip().lower() for x in res.text.split(",") if x.strip()]
                                for ing_f in ingredientes_f:
                                    for item in st.session_state.despensa:
                                        if item in ing_f or ing_f in item:
                                            try: st.session_state.despensa.remove(item); break
                                            except: pass
                                st.warning(f"Detectado y restado de despensa: {', '.join(ingredientes_f)}")
                                if st.button("Cerrar Auditoría", key=f"close_{i}"):
                                    st.session_state[f"rebelde_{i}"] = False
                                    st.rerun()
# ==========================================
# 🏋️‍♂️ PANTALLA: ENTRENADOR IA (Biomecánica y Fatiga)
# ==========================================
elif menu == "🏋️‍♂️ Entrenador IA":
    st.header("🏋️‍♂️ Entrenador Personal y Biomecánica")
    
    t_rutina, t_coach = st.tabs(["📋 Tu Microciclo Semanal", "📹 Coach Técnico (Vídeo)"])
        
    with t_rutina:
        # --- INICIALIZAR BÓVEDA DE RÉCORDS (Por si es la primera vez) ---
        if "maximos_rm" not in st.session_state:
            st.session_state.maximos_rm = {}

        st.subheader("🔥 Mapa de Recuperación Muscular (Auto-Regulación)")
        
        # --- MAPA DE FATIGA ---
        cols_mapa = st.columns(4)
        musculos = list(st.session_state.mapa_muscular.keys())
        for i, m in enumerate(musculos):
            valor = st.session_state.mapa_muscular[m]
            color = "🟢" if valor > 70 else "🟡" if valor > 40 else "🔴"
            with cols_mapa[i % 4]:
                st.metric(label=f"{color} {m}", value=f"{valor}%")
        st.divider()

        # --- GENERADOR SEMANAL CON APROXIMACIÓN (CALENTAMIENTO) ---
        if st.button("💪 GENERAR MICROCICLO SEMANAL", type="primary", use_container_width=True):
            if IA_ACTIVA:
                with st.spinner("Programando la semana con telemetría avanzada y aproximaciones..."):
                    p = st.session_state.perfil
                    ck = st.session_state.checkin_hoy
                    
                    prompt_entreno = f"""
                    Diseña un Microciclo de {p.get('dias_entreno', 4)} días para {p['objetivo']}. 
                    Material: {p['lugar_entreno']}. 
                    
                    🚨 [INFORME DE LESIONES Y FISIOTERAPIA]: {st.session_state.historial_medico.get('lesiones', 'Sin lesiones')}
                    
                    Devuelve un JSON estricto:
                    {{
                      "diagnostico_semanal": "Estrategia adaptada a tus lesiones...",
                      "dias": {{
                        "Día 1": [
                          {{
                            "nombre": "Press Banca", 
                            "calentamiento": "2x15 (barra vacía), 1x5 (50%), 1x2 (70%)", 
                            "series": 3, 
                            "reps": "8-10", 
                            "rir": "1-2", 
                            "tut": "3-1-X-1", 
                            "descanso": "90s", 
                            "video": "https://www.youtube.com/watch?v=tu_url", 
                            "series_completadas": []
                          }}
                        ]
                      }}
                    }}
                    REGLAS VITALES:
                    1. ADAPTA EL ENTRENO AL INFORME MÉDICO: Prohíbe totalmente ejercicios incompatibles con las lesiones y añade ejercicios específicos de rehabilitación o seguros.
                    2. El "video" debe ser una URL válida y directa de Youtube.
                    3. Incluye SIEMPRE la clave "calentamiento" para prescribir las series de aproximación.
                    🚨 [FASE DEL MESOCICLO]: Semana {p.get('semana_mesociclo', 1)} de 4. 
                    - Si es Semana 1: RIR 2-3, volumen moderado.
                    - Si es Semana 2 o 3: RIR 0-1 (Fallo), alta intensidad.
                    - Si es Semana 4 (DESCARGA): OBLIGATORIO bajar las series a la mitad y subir el RIR a 3-4 para recuperar el Sistema Nervioso.
                    """
                    try:
                        res = client.models.generate_content(model=MODELO_IA, contents=prompt_entreno)
                        texto = res.text.replace("```json", "").replace("```", "").strip()
                        inicio = texto.find('{')
                        fin = texto.rfind('}') + 1
                        st.session_state.rutina_estructurada = json.loads(texto[inicio:fin])
                        st.success("¡Microciclo generado con fases de calentamiento!")
                    except Exception as e: 
                        st.error(f"Error de la IA: {e}")

        # --- CUADRO DE MANDOS DEL DÍA ---
        if st.session_state.rutina_estructurada and "dias" in st.session_state.rutina_estructurada:
            dia_entreno = st.selectbox("📅 Selecciona tu sesión:", list(st.session_state.rutina_estructurada["dias"].keys()))
            
            ejercicios = st.session_state.rutina_estructurada["dias"].get(dia_entreno, [])
            todos_terminados = True
            
            for i, ej in enumerate(ejercicios):
                id_ej = f"ej_{dia_entreno}_{i}"
                
                if "series_completadas" not in ej: ej["series_completadas"] = []
                    
                series_totales = int(ej.get('series', 3))
                series_hechas = len(ej["series_completadas"])
                rm_historico = st.session_state.maximos_rm.get(ej['nombre'], 0)
                
                if series_hechas < series_totales: todos_terminados = False

                with st.container(border=True):
                    # Cabecera con nombre e indicador de RM histórico
                    st.subheader(f"🎯 {ej['nombre']} ({series_hechas}/{series_totales})")
                    if rm_historico > 0:
                        st.caption(f"🏆 Tu 1RM Histórico: **{rm_historico} kg**")
                    
                    # Detalles e incrustación de vídeo
                    c_info1, c_info2 = st.columns([2, 1])
                    with c_info1:
                        st.write(f"**Reps:** {ej['reps']} | **Descanso:** {ej['descanso']}")
                        st.markdown(f"⏱️ **TUT:** `{ej.get('tut', 'Controlado')}` | 🎯 **RIR Objetivo:** `{ej.get('rir', '1-2')}`")
                    with c_info2:
                        if "youtube.com/watch" in ej.get('video', '') or "youtu.be" in ej.get('video', ''):
                            st.video(ej['video'])
                        else:
                            st.markdown(f"[📺 Ver Ejecución]({ej.get('video', '#')})")
                    
                    st.divider()

                    # Mostrar Calentamiento SOLO si estamos en la Serie 0 (Aproximación inicial)
                    if series_hechas == 0 and ej.get("calentamiento"):
                        st.info(f"🔥 **Fase de Aproximación:** {ej['calentamiento']}")

                    # LÓGICA DE SERIES Y CAJETINES
                    if series_hechas >= series_totales:
                        st.success("✅ EJERCICIO TERMINADO")
                        st.write("Registro:", ej["series_completadas"])
                    else:
                        st.write(f"▶️ **Registrando Serie Efectiva {series_hechas + 1} de {series_totales}**")
                        
                        c_e1, c_e2, c_e3 = st.columns([1,1,1])
                        with c_e1: carga = st.number_input("Peso (kg)", 0.0, 500.0, step=2.5, key=f"w_{id_ej}")
                        with c_e2: rir_real = st.slider("RIR Real", 0, 5, 2, key=f"rir_{id_ej}")
                        with c_e3:
                            if st.button("🔄 SUSTITUIR", key=f"occ_{id_ej}", use_container_width=True):
                                with st.spinner("Generando variante..."):
                                    prompt_sust = f"Dame 1 sustituto para {ej['nombre']}. JSON exacto: nombre, calentamiento, series (int), reps, rir, tut, descanso, video, series_completadas (vacio)."
                                    res_alt = client.models.generate_content(model=MODELO_IA, contents=prompt_sust)
                                    texto_alt = res_alt.text.replace("```json", "").replace("```", "").strip()
                                    inicio, fin = texto_alt.find('{'), texto_alt.rfind('}') + 1
                                    nuevo_ej = json.loads(texto_alt[inicio:fin])
                                    nuevo_ej["series_completadas"] = []
                                    st.session_state.rutina_estructurada["dias"][dia_entreno][i] = nuevo_ej
                                    st.rerun()

                        # Botonera de Acción dividida (Serie normal vs RM)
                        fatiga_actual = st.session_state.mapa_muscular["SNC"]
                        if fatiga_actual < 40:
                            st.error("🚨 SNC CRÍTICO. Detén el entreno para evitar lesiones.")
                        else:
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✅ REGISTRAR SERIE", key=f"reg_{id_ej}", type="primary", use_container_width=True):
                                    ej["series_completadas"].append({"peso": carga, "rir": rir_real})
                                    st.session_state.mapa_muscular["SNC"] = max(0, fatiga_actual - 3)
                                    st.toast(f"⏱️ Descansa {ej['descanso']} para la siguiente serie.", icon="⏳")
                                    st.rerun()
                            with b2:
                                if st.button("🏆 GUARDAR COMO NUEVO 1RM", key=f"rm_{id_ej}", use_container_width=True):
                                    ej["series_completadas"].append({"peso": carga, "rir": rir_real, "es_rm": True})
                                    st.session_state.maximos_rm[ej['nombre']] = carga
                                    st.session_state.mapa_muscular["SNC"] = max(0, fatiga_actual - 6) # El RM fatiga el doble
                                    st.toast(f"🎉 ¡NUEVO RÉCORD! {carga}kg anotados en tu bóveda.", icon="🏆")
                                    st.balloons()
                                    st.rerun()

            # --- CIERRE DEL DÍA Y RESUMEN DEL COACH ---
            if todos_terminados and len(ejercicios) > 0:
                st.success("🏆 ¡HAS COMPLETADO TODAS LAS SERIES DEL DÍA!")
                if st.button("🧠 Pedir Análisis de la Sesión al Coach", type="primary", use_container_width=True):
                    with st.spinner("El Coach está evaluando tus RIRs y pesos..."):
                        datos_sesion = str([{"ejercicio": e["nombre"], "registro": e["series_completadas"]} for e in ejercicios])
                        res_coach = client.models.generate_content(
                            model=MODELO_IA, 
                            contents=f"El usuario ha terminado su entreno. Datos: {datos_sesion}. Haz una valoración técnica breve (¿se ha quedado muy lejos del fallo?, ¿ha hecho RMs?) y da 1 consejo de recuperación."
                        )
                        st.info(f"🗣️ **Coach Biomecánico:** {res_coach.text}")

    with t_coach:
        st.subheader("📹 Coach Técnico Biomecánico")
        st.write("Grábate en directo haciendo tu serie o sube un vídeo de tu galería (máximo 10-15 segundos). La IA analizará tu postura, tempo y posibles fallos técnicos.")
        
        # Este es el componente que en móviles abre la cámara o la galería
        video_file = st.file_uploader("🎥 Toca aquí para Grabarte o Subir tu Vídeo", type=["mp4", "mov", "avi"], key="video_coach")
        
        if video_file and IA_ACTIVA:
            st.video(video_file) # Te muestra el vídeo en pantalla para confirmar
            
            if st.button("🔍 Analizar Biomecánica", type="primary", use_container_width=True):
                with st.spinner("La visión artificial está procesando tus ángulos articulares y fotogramas..."):
                    try:
                        prompt_video = """
                        Eres un experto en biomecánica deportiva y fisioterapia. 
                        Analiza este levantamiento y devuelve un diagnóstico estructurado en 3 puntos:
                        1. ✅ Puntos Fuertes (¿Qué estoy haciendo bien?).
                        2. 🚨 Correcciones Urgentes (Riesgo de lesión o pérdida de fuerza).
                        3. ⏱️ Valoración del Tempo/TUT (¿Bajo muy rápido? ¿Hay rebote?).
                        """
                        res_vid = client.models.generate_content(
                            model=MODELO_IA,
                            contents=[prompt_video, video_file]
                        )
                        st.success("Análisis Biomecánico completado:")
                        st.markdown(res_vid.text)
                    except Exception as e:
                        st.error("Error al procesar el vídeo. Intenta grabar una toma más corta (menos de 15 segundos).")    

            # --- MOSTRAR EL PLAN SEMANAL (CUADRO DE MANDOS) ---
        if st.session_state.rutina_estructurada and "dias" in st.session_state.rutina_estructurada:
            st.info(f"🧠 **Estrategia del Coach:** {st.session_state.rutina_estructurada.get('diagnostico_semanal', '')}")
            
            # Selector de días como en nutrición
            dia_entreno = st.selectbox("📅 Selecciona tu sesión:", list(st.session_state.rutina_estructurada["dias"].keys()))
            
            st.write(f"### 🏋️‍♂️ Rutina: {dia_entreno}")
            
            for i, ej in enumerate(st.session_state.rutina_estructurada["dias"].get(dia_entreno, [])):
                id_ej = f"ej_{dia_entreno}_{i}"
                with st.container(border=True):
                    st.subheader(f"🎯 {ej['nombre']}")
                    
                    # Variables de hipertrofia
                    st.write(f"**Series:** {ej['series']} | **Reps:** {ej['reps']} | **Descanso:** {ej['descanso']}")
                    st.markdown(f"⏱️ **TUT (Tempo):** `{ej.get('tut', 'Controlado')}` | 🎯 **RIR Objetivo:** `{ej.get('rir', '1-2')}`")
                    st.markdown(f"📺 [Ver Técnica en Vídeo]({ej.get('video', '#')})")
                    
                    st.divider()
                    
                    c_e1, c_e2, c_e3 = st.columns([1,1,1])
                    
                    with c_e1: 
                        carga = st.number_input("Peso (kg)", 0.0, 300.0, step=2.5, key=f"w_{id_ej}")
                    
                    with c_e2:
                        rir_real = st.slider("RIR Real logrado", 0, 5, 2, help="0 = Fallo. 3 = Podías 3 más.", key=f"rir_{id_ej}")
                    
                    with c_e3:
                        if st.button("🔄 SUSTITUIR", key=f"occ_{id_ej}", use_container_width=True):
                            with st.spinner("Buscando alternativa..."):
                                res_alt = client.models.generate_content(model=MODELO_IA, contents=f"Dame 1 sustituto para {ej['nombre']}. Solo el nombre.")
                                st.warning(f"Alternativa: {res_alt.text}")
                        
                        if st.button("✅ REGISTRAR SERIE", key=f"reg_{id_ej}", type="primary", use_container_width=True):
                            st.session_state.historial_cargas[ej['nombre']] = {"peso": carga, "rir": rir_real}
                            st.session_state.racha_entreno += 1
                            st.session_state.mapa_muscular["SNC"] = max(0, st.session_state.mapa_muscular["SNC"] - 5)
                            st.success(f"¡Registrado! RIR {rir_real} anotado. SNC fatigado.")
                            time.sleep(1)
                            st.rerun()

        # --- GENERADOR DE ENTRENAMIENTO INTELIGENTE (CON RIR Y TUT) ---
        if st.button("💪 GENERAR SESIÓN ADAPTATIVA", type="primary", use_container_width=True):
            if IA_ACTIVA:
                with st.spinner("Calculando volumen, RIR y Tempo (TUT) óptimos para hoy..."):
                    p = st.session_state.perfil
                    ck = st.session_state.checkin_hoy
                    mapa = st.session_state.mapa_muscular
                    bestia = "¡MODO BESTIA ACTIVADO! Sube la intensidad, RIR al 0 (Fallo) y volumen un 15%." if st.session_state.modo_bestia else ""
                    
                    prompt_entreno = f"""
                    Eres un entrenador de fuerza de élite. Cliente: {p['objetivo']}, Nivel: {p['experiencia']}, Lugar: {p['lugar_entreno']}. Lesiones: {p['lesiones']}.
                    {bestia}
                    
                    [ESTADO FÍSICO HOY]: Sueño: {ck['horas_sueno_anoche']}h. Agujetas: {ck['nivel_agujetas']}. Estrés: {ck['estres_hoy']}.
                    Mapa Fatiga: {mapa}.
                    
                    REGLAS OBLIGATORIAS:
                    1. NO uses músculos por debajo del 50%.
                    2. Prescribe TUT (Tempo, ej: 3-1-1-1 o 4-0-X-0) y RIR (Reps en Reserva, ej: 1-2).
                    3. Si durmió poco o hay estrés, sube el RIR (ej. RIR 3) para proteger el Sistema Nervioso Central.
                    
                    Devuelve un JSON estricto:
                    {{
                      "diagnostico": "Explicación de la carga elegida hoy...",
                      "rutina": [
                        {{"nombre": "Sentadilla Búlgara", "series": 3, "reps": "8-10", "rir": "1-2", "tut": "3-1-X-1", "descanso": "90s", "video": "https://www.youtube.com/results?search_query=ejecucion+correcta+sentadilla+bulgara"}}
                      ]
                    }}
                    """
                    try:
                        res = client.models.generate_content(model=MODELO_IA, contents=prompt_entreno)
                        texto = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.rutina_estructurada = json.loads(texto)
                        st.success("¡Sesión generada con telemetría avanzada (RIR/TUT)!")
                    except Exception as e:
                        st.error("Error al generar la rutina. La IA devolvió un formato incorrecto.")

        # --- MOSTRAR LA RUTINA (CUADRO DE MANDOS AVANZADO) ---
        if st.session_state.rutina_estructurada:
            st.info(f"🧠 **Diagnóstico de tu Coach:** {st.session_state.rutina_estructurada.get('diagnostico', '')}")
            
            for i, ej in enumerate(st.session_state.rutina_estructurada.get('rutina', [])):
                id_ej = f"ej_{i}"
                with st.container(border=True):
                    st.subheader(f"🎯 {ej['nombre']}")
                    
                    # Mostrar las variables de programación arriba
                    st.write(f"**Series:** {ej['series']} | **Reps:** {ej['reps']} | **Descanso:** {ej['descanso']}")
                    st.markdown(f"⏱️ **TUT (Tempo):** `{ej.get('tut', 'Controlado')}` | 🎯 **RIR Objetivo:** `{ej.get('rir', '1-2')}`")
                    st.markdown(f"📺 [Ver Técnica en Vídeo]({ej['video']})")
                    
                    st.divider()
                    
                    c_e1, c_e2, c_e3 = st.columns([1,1,1])
                    
                    with c_e1: 
                        carga = st.number_input("Peso (kg)", 0.0, 300.0, step=2.5, key=f"w_{id_ej}")
                    
                    with c_e2:
                        # Cambiamos el viejo RPE por el RIR Real
                        rir_real = st.slider("RIR Real logrado", 0, 5, int(ej.get('rir', '2')[0]) if ej.get('rir', '2')[0].isdigit() else 2, help="0 = Llegaste al fallo. 3 = Podías hacer 3 más.", key=f"rir_{id_ej}")
                    
                    with c_e3:
                        if st.button("🔄 MÁQUINA OCUPADA", key=f"occ_{id_ej}", use_container_width=True):
                            with st.spinner("Buscando alternativa..."):
                                res_alt = client.models.generate_content(model=MODELO_IA, contents=f"Dame 1 sustituto directo para {ej['nombre']} usando material de {st.session_state.perfil['lugar_entreno']}. Solo di el nombre.")
                                st.warning(f"Alternativa IA: {res_alt.text}")
                        
                        if st.button("✅ REGISTRAR SERIE", key=f"reg_{id_ej}", type="primary", use_container_width=True):
                            st.session_state.historial_cargas[ej['nombre']] = {"peso": carga, "rir": rir_real}
                            st.session_state.racha_entreno += 1
                            # Castigo muscular al SNC
                            st.session_state.mapa_muscular["SNC"] = max(0, st.session_state.mapa_muscular["SNC"] - 5)
                            st.success(f"¡Carga guardada! RIR anotado: {rir_real}")
                            time.sleep(1)
                            st.rerun()
# ==========================================
# 🍷 PANTALLA: VIDA SOCIAL (Supervivencia)
# ==========================================
elif menu == "🍷 Vida Social":
    st.header("🍷 Vida Social y Supervivencia")
    t_carta, t_plato, t_resaca = st.tabs(["📜 Hackear Menú", "📸 Analizar Plato", "🤕 Protocolo Resaca"])
    
    with t_carta:
        usar_cam = st.toggle("Cámara frontal", key="tc")
        f_carta = st.camera_input("Enfoca el menú del restaurante") if usar_cam else st.file_uploader("📷 Subir Foto de la Carta", type=['jpg', 'png'])
        if f_carta and IA_ACTIVA:
            with st.spinner("Buscando las mejores opciones proteicas..."):
                res = client.models.generate_content(model=MODELO_IA, contents=[f"Dime los 2 platos que mejor encajan para un objetivo de {st.session_state.perfil['objetivo']}. Ignora fritos.", Image.open(f_carta)])
                st.info(res.text)

    with t_plato:
        usar_camp = st.toggle("Cámara frontal", key="tp")
        f_plato = st.camera_input("Enfoca tu plato servido") if usar_camp else st.file_uploader("📷 Subir Foto del Plato", type=['jpg', 'png'])
        if f_plato and IA_ACTIVA:
            with st.spinner("Calculando macros visuales..."):
                res = client.models.generate_content(model=MODELO_IA, contents=["Desglosa calorías y macros estimados de esto. ¿Hay buena cantidad de proteína?", Image.open(f_plato)])
                st.success(res.text)

    with t_resaca:
        st.subheader("🤕 S.O.S Rescate (El día después)")
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            intensidad = st.select_slider("🔥 Nivel de destrucción anoche", options=range(1, 11), value=5)
            comida_basura = st.toggle("🍔 Hubo comida ultraprocesada/alcohol")
        with c_res2:
            estado = st.selectbox("💀 Estado vital hoy", ["Supervivencia (Muerte)", "Zombie (Funcional)", "Resacoso pero Guerrero"])
            hid = st.slider("💧 Nivel de agua ayer (1-10)", 1, 10, 3)
        
        if st.button("🚑 ACTIVAR PROTOCOLO DE PURGA", type="primary"):
            st.session_state.racha_nutricion = 0 # Castigo divino
            st.session_state.meta_agua = 4.0 if intensidad > 6 else 3.5
            with st.spinner("Generando suero de recuperación..."):
                prompt = f"Protocolo rescate. Daño: {intensidad}/10. Basura: {comida_basura}. Estado: {estado}. Genera: 1 bebida de reposición de electrolitos (Sodio/Potasio), 1 comida sólida para asentar el estómago y ajusta el entreno de hoy."
                res = client.models.generate_content(model=MODELO_IA, contents=prompt)
                st.error(f"🚨 PROTOCOLO ACTIVADO. Tu racha se ha reseteado. Nueva meta de agua hoy: {st.session_state.meta_agua}L.")
                st.markdown(res.text)

# ==========================================
# 🩸 PANTALLA: PROGRESO Y BIO-CENTRO (El Santo Grial)
# ==========================================
elif menu == "🩸 Progreso":
    st.header("📈 Centro de Biometría y Salud")
    
    t_peso, t_reloj, t_sangre, t_espejo = st.tabs(["⚖️ Peso", "⌚ Sincronizar Reloj", "🩸 Analíticas", "📸 Espejo IA"])
    
    with t_peso:
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            st.subheader("Registrar Hoy")
            nuevo_peso = st.number_input("Peso actual (kg)", value=float(st.session_state.perfil['peso']), step=0.1)
            if st.button("Guardar Registro", type="primary"):
                hoy = datetime.date.today().strftime("%Y-%m-%d")
                nuevo_dato = pd.DataFrame({"Fecha": [hoy], "Peso (kg)": [nuevo_peso]})
                st.session_state.historial_biometrico = pd.concat([st.session_state.historial_biometrico, nuevo_dato], ignore_index=True)
                st.session_state.perfil['peso'] = nuevo_peso
                st.success("¡Peso guardado! La tendencia es tu amiga.")
        with col_p2:
            st.subheader("Tu Evolución")
            if len(st.session_state.historial_biometrico) > 0:
                df = st.session_state.historial_biometrico.set_index("Fecha")
                st.line_chart(df)
            else:
                st.info("Registra tu peso para ver la gráfica.")
                
    with t_reloj:
        st.subheader("⌚ Sincronización Visual (Garmin/Apple Watch/Oura)")
        st.write("Sube una captura de pantalla del resumen diario de tu reloj inteligente.")
        f_reloj = st.file_uploader("Subir captura del reloj", type=['jpg', 'png', 'jpeg'])
        if f_reloj and IA_ACTIVA:
            if st.button("Extraer Datos del Reloj"):
                with st.spinner("Leyendo métricas..."):
                    res_reloj = client.models.generate_content(
                        model=MODELO_IA, 
                        contents=["Extrae de esta imagen: Pasos totales, Calorías activas, Horas de sueño y Frecuencia Cardíaca (si las hay). Haz un resumen corto.", Image.open(f_reloj)]
                    )
                    st.success("Datos sincronizados en el sistema:")
                    st.write(res_reloj.text)
                    
    with t_sangre:
        st.subheader("🩸 Analista Clínico (Análisis de Sangre)")
        st.write("Sube una foto o PDF (captura) de tu último análisis de sangre. La IA buscará deficiencias para adaptar tu dieta.")
        f_sangre = st.file_uploader("Subir Analítica", type=['jpg', 'png'])
        if f_sangre and IA_ACTIVA:
            if st.button("Analizar Biomarcadores"):
                with st.spinner("Revisando colesterol, hierro, glucosa..."):
                    res_sangre = client.models.generate_content(
                        model=MODELO_IA,
                        contents=["Eres un endocrino. Lee estos análisis de sangre. Resume los 3 valores que están fuera de rango (si los hay) y dime qué 3 alimentos exactos debo añadir a mi dieta para corregirlos.", Image.open(f_sangre)]
                    )
                    st.warning("Diagnóstico Nutricional completado:")
                    st.write(res_sangre.text)
                    
    with t_espejo:
        st.subheader("📸 Espejo Inteligente (Body Comp)")
        st.write("Sube tu foto de progreso mensual frente al espejo. La IA analizará la hipertrofia y tu postura.")
        f_espejo = st.file_uploader("Subir foto de progreso", type=['jpg', 'png'])
        if f_espejo and IA_ACTIVA:
            if st.button("Evaluar Físico"):
                with st.spinner("Analizando recomposición corporal..."):
                    res_espejo = client.models.generate_content(
                        model=MODELO_IA,
                        contents=[f"Evalúa esta foto de progreso fitness de una persona que busca {st.session_state.perfil['objetivo']}. Comenta amablemente sobre su desarrollo muscular visible y su postura.", Image.open(f_espejo)]
                    )
                    st.success("Evaluación de tu Coach:")
                    st.write(res_espejo.text)                        
