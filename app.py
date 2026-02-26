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
                    Material: {p['lugar_entreno']}. Lesiones: {p['lesiones']}.
                    Devuelve un JSON estricto:
                    {{
                      "diagnostico_semanal": "Estrategia...",
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
                    1. El "video" debe ser una URL válida y directa de Youtube.
                    2. Incluye SIEMPRE la clave "calentamiento" para prescribir las series de aproximación lógicas antes de las series efectivas.
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
