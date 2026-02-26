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

# A) Perfil Biométrico y Logístico
if 'perfil' not in st.session_state:
    st.session_state.perfil = {
        'sexo': 'Hombre', 'perfil_hormonal': 'Ninguno', 'edad': 30, 'peso': 75.0, 'altura': 175, 
        'actividad': 'Moderada', 'objetivo': 'Estética Funcional', 'experiencia': 'Intermedio', 
        'lugar_entreno': 'Gimnasio Comercial', 'horario_entreno': 'Tarde', 'dias_entreno': 4,
        'dieta_tipo': 'Omnívora', 'alergias': '', 'n_comidas': 4, 'ayuno': False, 'suplementos': '',
        'lesiones': 'Ninguna', 'sueno_base': 'Normal (6-8h)', 'estres_base': 'Moderado',
        'presupuesto': 'Moderado', 'utensilios': ['Sartén', 'Microondas'], 'tiempo_cocina': 30
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
# 6. NAVEGACIÓN PRINCIPAL
# ==========================================
opciones_menu = ["🏠 Inicio", "👤 Perfil", "🥗 Nutrición Pro", "🏋️‍♂️ Entrenador IA", "🍷 Vida Social", "🩸 Progreso"]
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
    st.header("👤 Perfil God-Tier (Centro de Mando)")
    st.write("Rellena tus datos. La IA cruzará tu biometría, hormonas y logística para crear tu plan perfecto.")
    
# --- 1. BIOMETRÍA Y SALUD FEMENINA ---
    with st.expander("1. Biometría y Salud", expanded=True):
        # Usamos columnas con un ratio 1:1 para asegurar el espacio
        c1, c2 = st.columns([1, 1])
        
        with c1:
            sexo = st.selectbox(
                "Sexo", 
                ["Hombre", "Mujer"], 
                index=0 if st.session_state.perfil.get('sexo', 'Hombre') == 'Hombre' else 1,
                key="perfil_sexo"
            )
        
        with c2:
            perfil_hormonal = "Ninguno"
            if sexo == "Mujer":
                opciones_hormonas = ["Ninguno", "Fase Folicular (Post-regla)", "Fase Lútea (Pre-regla)", "SOP", "Endometriosis", "Embarazo", "⚠️ RED-S (Falta de regla)"]
                # Buscamos el índice actual para que no se resetee al guardar
                try:
                    idx_horm = opciones_hormonas.index(st.session_state.perfil.get('perfil_hormonal', 'Ninguno'))
                except ValueError:
                    idx_horm = 0
                
                perfil_hormonal = st.selectbox("Fase / Estado Hormonal", opciones_hormonas, index=idx_horm, key="perfil_fase")
            else:
                st.info("Perfil optimizado para testosterona y salud masculina.")
        
        st.write("---") # Una línea sutil de separación
        
        c3, c4, c5 = st.columns(3)
        with c3: edad = st.number_input("Edad", 14, 90, st.session_state.perfil.get('edad', 30))
        with c4: altura = st.number_input("Altura (cm)", 100, 250, st.session_state.perfil.get('altura', 175))
        with c5: peso = st.number_input("Peso (kg)", 30.0, 200.0, float(st.session_state.perfil.get('peso', 75.0)))
        
        actividad = st.selectbox("NEAT Diario (Actividad fuera del gym)", ["Sedentaria", "Ligera", "Moderada", "Muy Activa"], index=2, key="perfil_neat")
    # --- 2. CRONOBIOLOGÍA Y CLÍNICA ---
    with st.expander("2. Cronobiología, Microbiota y Clínica"):
        st.markdown("**⏰ Tus Ritmos Circadianos**")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            hora_despertar = st.time_input("Hora habitual de despertar", value=datetime.time(7, 0))
        with col_c2:
            hora_dormir = st.time_input("Hora habitual de dormir", value=datetime.time(23, 0))
            
        st.markdown("**🧬 Digestión y Sistema Nervioso**")
        col_c3, col_c4 = st.columns(2)
        with col_c3:
            digestion = st.selectbox("Sensibilidad Digestiva (Microbiota)", ["Fuerte (Digiero piedras)", "Normal", "Pesada / Gases", "Intestino Irritable (FODMAP)"])
        with col_c4:
            cafeina = st.selectbox("Tolerancia a la Cafeína", ["Alta (Me duermo con un RedBull)", "Normal", "Baja (Me da taquicardia)"])
            
        lesiones = st.text_area("Lesiones o patologías a tener en cuenta:", value=st.session_state.perfil.get('lesiones', ''))

    # --- 3. OBJETIVOS Y LOGÍSTICA DE ENTRENO ---
    with st.expander("3. Objetivos y Logística de Entreno"):
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            obj = st.selectbox("Programa (Objetivo)", ["Estética Funcional", "Powerbuilding (Fuerza+Masa)", "Shredding (Definición)", "Recomposición Femenina (Glúteo)", "Atleta Híbrido", "Longevidad"], index=0)
        with col_o2:
            experiencia = st.selectbox("Nivel", ["Principiante", "Intermedio", "Avanzado"], index=1)
            
        col_o3, col_o4, col_o5 = st.columns(3)
        with col_o3: lugar_entreno = st.selectbox("Lugar", ["Gimnasio Comercial", "Home Gym", "Parque/Calistenia"])
        with col_o4: horario_entreno = st.selectbox("Horario de entreno", ["Mañana (Ayunas)", "Mañana (Post-desayuno)", "Tarde", "Noche"])
        with col_o5: dias_gym = st.slider("Días/Semana", 1, 7, st.session_state.perfil.get('dias_entreno', 4))

    # --- 4. NUTRICIÓN, COCINA Y SUPLEMENTOS ---
    with st.expander("4. 🍳 Cocina, Nutrición, Suplementos y Utensilios"):
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            dieta_tipo = st.selectbox("Tipo de Dieta", ["Omnívora", "Vegetariana", "Vegana", "Keto", "Pescetariana"])
        with col_n2:
            n_comidas = st.number_input("Comidas/día", 1, 8, st.session_state.perfil.get('n_comidas', 4))
        with col_n3:
            ayuno = st.toggle("¿Ayuno Intermitente?", value=st.session_state.perfil.get('ayuno', False))
        
        st.markdown("**🛠️ Tu Arsenal**")
        opciones_utensilios = ["Sartén", "Olla", "Horno", "Microondas", "Airfryer", "Batidora", "Vaporera", "Robot de Cocina"]
        utensilios = st.multiselect("Electrodomésticos:", opciones_utensilios, default=st.session_state.perfil.get('utensilios', ['Sartén', 'Microondas']))
        
        col_n4, col_n5 = st.columns(2)
        with col_n4: alergias = st.text_input("Alergias:", value=st.session_state.perfil.get('alergias', ''))
        with col_n5: suplementos = st.text_input("Suplementos:", value=st.session_state.perfil.get('suplementos', ''))
        
        presupuesto = st.select_slider("Presupuesto:", options=["Económico", "Moderado", "Premium"])

    # --- 5. MEMORIA GASTRONÓMICA ---
    with st.expander("5. 🧠 Memoria Gastronómica IA"):
        g_pos = st.text_area("AMAS (Ingredientes):", value=", ".join(st.session_state.gustos_positivos))
        g_neg = st.text_area("ODIAS (Ingredientes):", value=", ".join(st.session_state.gustos_negativos))
    
    if st.button("💾 BLINDAR PERFIL Y CALIBRAR IA", type="primary", use_container_width=True):
        st.session_state.perfil.update({
            'sexo': sexo, 'perfil_hormonal': perfil_hormonal, 'edad': edad, 'peso': peso, 'altura': altura, 
            'actividad': actividad, 'objetivo': obj, 'experiencia': experiencia, 'lugar_entreno': lugar_entreno, 
            'horario_entreno': horario_entreno, 'dias_entreno': dias_gym, 'dieta_tipo': dieta_tipo, 
            'n_comidas': n_comidas, 'ayuno': ayuno, 'alergias': alergias, 'suplementos': suplementos,
            'presupuesto': presupuesto, 'utensilios': utensilios, 'hora_despertar': hora_despertar.strftime("%H:%M"),
            'hora_dormir': hora_dormir.strftime("%H:%M"), 'sensibilidad_digestiva': digestion, 'tolerancia_cafeina': cafeina
        })
        st.session_state.gustos_positivos = [g.strip() for g in g_pos.split(",") if g.strip()]
        st.session_state.gustos_negativos = [g.strip() for g in g_neg.split(",") if g.strip()]
        st.success("¡Perfil guardado!")
        st.rerun()

# ==========================================
# 🥗 PANTALLA: NUTRICIÓN PRO
# ==========================================
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

    # --- 2. GESTIÓN DE DESPENSA (LOS 5 ESCÁNERES) ---
    with st.expander("🛒 Gestionar mi Despensa e Ingredientes", expanded=not bool(st.session_state.despensa)):
        t_nev, t_ticket, t_barras, t_voz, t_man = st.tabs([
            "📸 Nevera/Despensa", "🧾 Ticket", "🔍 Código de Barras", "🎙️ Dictado", "⌨️ Manual"
        ])
        
        with t_nev:
            col_n1, col_n2 = st.columns(2)
            with col_n1: foto_n = st.camera_input("Hacer foto a la nevera")
            with col_n2: archivo_n = st.file_uploader("O subir foto desde archivo", type=['jpg', 'png', 'jpeg'], key="up_nev")
            if (foto_n or archivo_n) and IA_ACTIVA:
                img = Image.open(foto_n if foto_n else archivo_n)
                with st.spinner("Chef IA escaneando..."):
                    res = client.models.generate_content(model=MODELO_IA, contents=["Lista alimentos saludables separados por comas.", img])
                    nuevos = [i.strip().lower() for i in res.text.split(",") if i.strip()]
                    st.session_state.despensa = list(set(st.session_state.despensa + nuevos))
                    st.success(f"Detectados: {', '.join(nuevos)}")

        with t_ticket:
            archivo_t = st.file_uploader("Sube foto del ticket", type=['jpg', 'png', 'jpeg'], key="up_tick")
            if archivo_t and IA_ACTIVA:
                res = client.models.generate_content(model=MODELO_IA, contents=["Extrae nombres de alimentos saludables del ticket.", Image.open(archivo_t)])
                nuevos = [i.strip().lower() for i in res.text.split(",") if i.strip()]
                st.session_state.despensa = list(set(st.session_state.despensa + nuevos))

        with t_barras:
            archivo_b = st.file_uploader("Foto Código de Barras", type=['jpg', 'png', 'jpeg'], key="up_bar")
            if archivo_b and IA_ACTIVA:
                res = client.models.generate_content(model=MODELO_IA, contents=["¿Qué alimento es este código de barras?", Image.open(archivo_b)])
                st.session_state.despensa.append(res.text.strip().lower())

        with t_voz:
            audio = st.audio_input("Dicta tus ingredientes:")
            if audio and IA_ACTIVA:
                res = client.models.generate_content(model=MODELO_IA, contents=["Extrae alimentos de este audio.", audio])
                st.session_state.despensa = list(set(st.session_state.despensa + [i.strip().lower() for i in res.text.split(",") if i.strip()]))
                st.rerun()

        with t_man:
            manual = st.text_input("Añadir manual (ej: atún, pasta):")
            if st.button("➕ Añadir"):
                st.session_state.despensa = list(set(st.session_state.despensa + [i.strip().lower() for i in manual.split(",") if i.strip()]))
                st.rerun()

        st.divider()
        if st.session_state.despensa:
            st.write(f"🍏 **Tu Despensa:** {', '.join(st.session_state.despensa).title()}")
            if st.button("🗑️ VACIAR DESPENSA A 0", type="secondary"):
                st.session_state.despensa = []
                st.session_state.pop('lista_compra_sugerida', None)
                st.rerun()

    # --- 3. EL CHEF IA (RECETAS Y CIENCIA) ---
    if st.button("👨‍🍳 GENERAR PLAN SEMANAL Y RECETAS (GOD-TIER)", type="primary", use_container_width=True):
        if IA_ACTIVA:
            with st.spinner("El Chef está diseñando tu semana..."):
                p = st.session_state.perfil
                prompt = f"""
                Eres un Chef Michelin y Nutricionista. Genera dieta semanal.
                REGLAS: Grasas min 1g/kg. Post-entreno ({p['horario_entreno']}) alto en CH. 
                Fase Hormonal: {p['perfil_hormonal']}. Despensa: {st.session_state.despensa}.
                Devuelve JSON con: "plato", "ingredientes", "instrucciones", "nota_ciencia".
                """
                try:
                    res = client.models.generate_content(model=MODELO_IA, contents=prompt)
                    texto = res.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.plan_estructurado = json.loads(texto)
                except: st.error("Error en la cocina. Reintenta.")

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
    
    t_rutina, t_coach = st.tabs(["📋 Tu Rutina de Hoy", "📹 Coach Técnico (Vídeo)"])
    
    with t_rutina:
        # --- MAPA DE FATIGA MUSCULAR ---
        st.subheader("🔥 Mapa de Recuperación Muscular")
        st.write("Estado de tu Sistema Nervioso (SNC) y grupos musculares. La IA evitará lo que esté en rojo.")
        
        cols_mapa = st.columns(4)
        musculos = list(st.session_state.mapa_muscular.keys())
        for i, m in enumerate(musculos):
            valor = st.session_state.mapa_muscular[m]
            color = "🟢" if valor > 70 else "🟡" if valor > 40 else "🔴"
            with cols_mapa[i % 4]:
                st.metric(label=f"{color} {m}", value=f"{valor}%")
        
        st.divider()

        # --- GENERADOR DE ENTRENAMIENTO INTELIGENTE ---
        if st.button("💪 GENERAR SESIÓN ADAPTATIVA", type="primary", use_container_width=True):
            if IA_ACTIVA:
                with st.spinner("Analizando tu fatiga, horas de sueño y estrés para crear el entreno perfecto..."):
                    p = st.session_state.perfil
                    ck = st.session_state.checkin_hoy
                    mapa = st.session_state.mapa_muscular
                    bestia = "¡MODO BESTIA ACTIVADO! Sube la intensidad y el volumen un 15%." if st.session_state.modo_bestia else ""
                    
                    prompt_entreno = f"""
                    Eres un entrenador de fuerza de élite y fisioterapeuta.
                    Cliente: {p['objetivo']}, Nivel: {p['experiencia']}, Lugar: {p['lugar_entreno']}. Lesiones: {p['lesiones']}.
                    {bestia}
                    
                    [ESTADO FÍSICO HOY]:
                    - Sueño anoche: {ck['horas_sueno_anoche']}h. Agujetas (1-10): {ck['nivel_agujetas']}. Estrés: {ck['estres_hoy']}.
                    - Mapa de Fatiga (100% es fresco, 0% es destruido): {mapa}.
                    
                    REGLAS OBLIGATORIAS:
                    1. PROHIBIDO prescribir ejercicios para músculos que estén por debajo del 50%.
                    2. Si ha dormido menos de 6 horas o el estrés es 'Alto', reduce el volumen total (menos series) para no freír el Sistema Nervioso.
                    3. Genera una frase de diagnóstico inicial explicando por qué has elegido esta rutina basándote en su fatiga y sueño.
                    
                    Devuelve un JSON estricto con este formato:
                    {{
                      "diagnostico": "Tu texto explicando la elección...",
                      "rutina": [
                        {{"nombre": "Sentadilla Búlgara", "series": 3, "reps": "8-10", "descanso": "90s", "video": "https://www.youtube.com/results?search_query=ejecucion+correcta+sentadilla+bulgara"}}
                      ]
                    }}
                    """
                    try:
                        res = client.models.generate_content(model=MODELO_IA, contents=prompt_entreno)
                        texto = res.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.rutina_estructurada = json.loads(texto)
                        st.success("¡Sesión generada y adaptada a tu fisiología de hoy!")
                    except Exception as e:
                        st.error("Error al generar la rutina. La IA devolvió un formato incorrecto.")

        # --- MOSTRAR LA RUTINA ---
        if st.session_state.rutina_estructurada:
            st.info(f"🧠 **Diagnóstico de tu Coach:** {st.session_state.rutina_estructurada.get('diagnostico', '')}")
            
            for i, ej in enumerate(st.session_state.rutina_estructurada.get('rutina', [])):
                id_ej = f"ej_{i}"
                with st.container(border=True):
                    st.subheader(f"🎯 {ej['nombre']}")
                    c_e1, c_e2, c_e3 = st.columns([1,1,1])
                    
                    with c_e1: 
                        st.write(f"**Series:** {ej['series']} | **Reps:** {ej['reps']} | **Descanso:** {ej['descanso']}")
                        st.markdown(f"📺 [Ver Técnica en Vídeo]({ej['video']})")
                    
                    with c_e2:
                        carga = st.number_input("Peso levantado (kg)", 0.0, 300.0, step=2.5, key=f"w_{id_ej}")
                        rpe = st.slider("Esfuerzo RPE (1=Paseo, 10=Fallo)", 1, 10, 8, key=f"r_{id_ej}")
                    
                    with c_e3:
                        if st.button("🔄 MÁQUINA OCUPADA", key=f"occ_{id_ej}", use_container_width=True):
                            with st.spinner("Buscando alternativa..."):
                                res_alt = client.models.generate_content(model=MODELO_IA, contents=f"Dame 1 sustituto directo para {ej['nombre']} usando material de {st.session_state.perfil['lugar_entreno']}. Solo di el nombre del ejercicio.")
                                st.warning(f"Alternativa IA: {res_alt.text}")
                        
                        if st.button("✅ REGISTRAR Y FATIGAR MÚSCULO", key=f"reg_{id_ej}", type="primary", use_container_width=True):
                            st.session_state.historial_cargas[ej['nombre']] = {"peso": carga, "rpe": rpe}
                            st.session_state.racha_entreno += 1
                            # Simulamos fatiga bajando un 10% un músculo al azar para el MVP (En producción se mapearía exacto)
                            st.session_state.mapa_muscular["SNC"] = max(0, st.session_state.mapa_muscular["SNC"] - 5)
                            st.success("¡Guardado en el historial!")
                            st.rerun()

    with t_coach:
        st.subheader("📹 Coach Técnico Biomecánico")
        st.write("Sube un vídeo corto de tu levantamiento y la IA analizará tu postura, tempo y fallos técnicos.")
        video_file = st.file_uploader("Sube tu vídeo (mp4, mov)", type=["mp4", "mov"])
        if video_file and IA_ACTIVA:
            if st.button("🔍 Analizar Biomecánica"):
                with st.spinner("La IA está procesando los fotogramas y tu postura..."):
                    # Gemini 2.5 Pro procesa vídeo nativo.
                    res_vid = client.models.generate_content(
                        model=MODELO_IA,
                        contents=["Eres un experto en biomecánica. Analiza este levantamiento. Dime 3 puntos fuertes y 3 correcciones urgentes para evitar lesiones y maximizar la hipertrofia.", video_file]
                    )
                    st.success("Análisis completado:")
                    st.markdown(res_vid.text)

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
