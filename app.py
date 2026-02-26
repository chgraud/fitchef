# ==========================================
# 🏥 PANTALLA: CLÍNICA BIO-HACKING
# ==========================================
elif menu == "🏥 Clínica Bio-Hacking":
    st.header("🏥 Centro Médico y Longevidad")
    st.write("Haz una foto a tus analíticas de sangre o al informe del fisio. La IA extraerá los biomarcadores para hackear tu dieta y entrenamiento.")
    
    # Dividimos la pantalla en dos columnas
    c_med1, c_med2 = st.columns(2)
    
    # --- COLUMNA 1: SANGRE Y METABOLISMO ---
    with c_med1:
        st.subheader("🩸 Analíticas de Sangre")
        archivo_sangre = st.file_uploader("Foto de la Analítica", type=['jpg', 'png', 'jpeg'], key="up_sangre")
        
        if archivo_sangre and IA_ACTIVA:
            if st.button("🔬 Analizar Biomarcadores", use_container_width=True):
                with st.spinner("Leyendo niveles de vitaminas, hierro, hormonas..."):
                    try:
                        prompt_sangre = """
                        Eres un médico endocrino. Analiza este documento. 
                        Extrae SOLO las deficiencias, excesos o valores anómalos que impacten en la dieta o el rendimiento 
                        (ej: falta de Vitamina D, hierro bajo, glucosa alta, colesterol). 
                        Sé muy breve, directo y usa bullet points.
                        """
                        res_sangre = client.models.generate_content(
                            model=MODELO_IA, 
                            contents=[prompt_sangre, Image.open(archivo_sangre)]
                        )
                        st.session_state.historial_medico["analiticas"] = res_sangre.text
                        st.success("¡Analítica procesada!")
                    except Exception as e:
                        st.error("Error al leer la imagen. Asegúrate de que se vea nítida.")
        
        # Mostramos lo que la app ha memorizado
        with st.container(border=True):
            st.markdown(f"**🧬 Diagnóstico Metabólico Actual:**\n\n{st.session_state.historial_medico['analiticas']}")

    # --- COLUMNA 2: FISIOTERAPIA Y LESIONES ---
    with c_med2:
        st.subheader("🦴 Informes de Fisioterapia")
        archivo_fisio = st.file_uploader("Foto del Diagnóstico/Resonancia", type=['jpg', 'png', 'jpeg'], key="up_fisio")
        
        if archivo_fisio and IA_ACTIVA:
            if st.button("🔍 Analizar Lesión", use_container_width=True):
                with st.spinner("Evaluando limitaciones biomecánicas..."):
                    try:
                        prompt_fisio = """
                        Eres un fisioterapeuta deportivo. Analiza este informe médico. 
                        Dime EXACTAMENTE qué movimientos, músculos o ejercicios están PROHIBIDOS o limitados, 
                        y cuáles están recomendados para rehabilitación. Sé breve y usa bullet points.
                        """
                        res_fisio = client.models.generate_content(
                            model=MODELO_IA, 
                            contents=[prompt_fisio, Image.open(archivo_fisio)]
                        )
                        st.session_state.historial_medico["lesiones"] = res_fisio.text
                        st.success("¡Lesión registrada en el expediente!")
                    except Exception as e:
                        st.error("Error al leer la imagen. Inténtalo de nuevo.")
        
        # Mostramos lo que la app ha memorizado
        with st.container(border=True):
            st.markdown(f"**🚨 Limitaciones Físicas Actuales:**\n\n{st.session_state.historial_medico['lesiones']}")
