def analizar_mercado():
    print("Iniciando análisis con estilo...")
    
    zona_peru = pytz.timezone('America/Lima')
    ahora = datetime.now(zona_peru)
    hora = ahora.hour
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_texto = ahora.strftime("%I:%M %p")

    estado = leer_estado()
    # AHORA EL RADAR ES EL GRINGO (Yahoo)
    ultimo_precio_yahoo = estado.get('precio_yahoo', 0.0) 
    ultima_apertura = estado.get('fecha_apertura', "")
    ultimo_cierre = estado.get('fecha_cierre', "")

    try:
        data = yf.download(TICKER, period="1mo", interval="1d", progress=False, multi_level_index=False)
    except: return
    if data.empty: return

    # ESTE ES EL QUE SE MUEVE EN VIVO
    precio_oficial = data['Close'].iloc[-1].item() 
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    # Este es fijo por día, solo lo mostramos como información
    precio_local = obtener_precio_local_api() 
    
    tipo_reporte = "NORMAL"
    mensaje_intro = ""
    intro_random_apertura = random.choice(FRASES_APERTURA)
    intro_random_cierre = random.choice(FRASES_CIERRE)
    guardar_cambios = False

    if hora == 9 and ultima_apertura != fecha_hoy:
        tipo_reporte = "FORZAR_ENVIO"
        mensaje_intro = intro_random_apertura
        estado['fecha_apertura'] = fecha_hoy
        guardar_cambios = True

    elif hora == 18 and ultimo_cierre != fecha_hoy:
        tipo_reporte = "FORZAR_ENVIO"
        mensaje_intro = intro_random_cierre
        estado['fecha_cierre'] = fecha_hoy
        guardar_cambios = True

    # LA LÓGICA DE ALERTA AHORA VIGILA AL MERCADO EN VIVO (Yahoo)
    diferencia = abs(precio_oficial - ultimo_precio_yahoo)
    enviar = False

    if tipo_reporte == "FORZAR_ENVIO":
        enviar = True
    else:
        # Si Yahoo Finance se mueve más de 0.003, disparamos la alerta
        if diferencia >= 0.003: enviar = True
        if precio_oficial <= min_mes and diferencia > 0: enviar = True
        if precio_oficial >= max_mes and diferencia > 0: enviar = True

    frase_accion = ""
    
    # Los consejos ahora se basan en la volatilidad en vivo
    if precio_oficial <= min_mes:
        frase_accion = random.choice(FRASES_COMPRA)
    elif precio_oficial >= max_mes:
        frase_accion = random.choice(FRASES_VENTA)
    elif diferencia >= 0.003:
        if precio_oficial > ultimo_precio_yahoo:
            frase_accion = random.choice(FRASES_SUBIDA)
        else:
            frase_accion = random.choice(FRASES_BAJADA)

    if enviar:
        icono_precio = ""
        if precio_oficial <= min_mes: icono_precio = "🚨 BAJÓ"
        elif precio_oficial >= max_mes: icono_precio = "🔥 SUBIÓ"

        txt_local = f"S/ {precio_local:.3f}" if precio_local else "⚠️ N/D"

        if not mensaje_intro:
            mensaje_intro = f"🔔 *¡ALERTA CAUSA!* Se movió el dólar internacional"

        mensaje = (
            f"{mensaje_intro}\n"
            f"🕒 _{hora_texto}_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏦 *Mercado Vivo (Yahoo):* S/ {precio_oficial:.3f} {icono_precio}\n"
            f"🇵🇪 *Referencia SUNAT:* {txt_local}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📉 Min Mes: {min_mes:.3f}\n"
            f"📈 Max Mes: {max_mes:.3f}\n"
            f"{frase_accion}"
        )

        enviar_telegram(mensaje)
        # Guardamos el precio de Yahoo para compararlo en los próximos 10 min
        estado['precio_yahoo'] = precio_oficial 
        guardar_cambios = True
    else:
        print(f"Sin novedades. Diferencia en vivo: {diferencia:.4f}.")
        
    if guardar_cambios:
        guardar_estado(estado)
    print("✅ Ejecución finalizada.")
