import yfinance as yf
import requests
import os
import json
import random
from datetime import datetime
import pytz 

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ARCHIVO_ESTADO = 'estado.json'

# --- FRASES CON CALLE (PACK EXTENDIDO) ---
FRASES_APERTURA = [
    "☀️ *¡Habla causa!* Arranca el mercado. Agarra tu café que aquí vamos:",
    "🐓 *¡Quiquiriquí!* Despierta oye, que el dinero no duerme.",
    "🚀 *¡Arriba Perú!* Vamos a ver cómo se porta el gringo hoy:",
    "😎 *¡Buenos días alegría!* A chambear que la plata no cae del cielo.",
    "🔋 *¡Habla batería seria!* Carga pilas que hoy se factura:",
    "☕ *¡Despierta!* Ni el gallo se levantó tan temprano. Checa:",
    "🧢 *¡Alao!* ¿Todo chill? Vamos a ver si hoy nos hacemos millonarios:",
    "🔔 *¡Ding dong!* Abrió el mercado, mano. Mira esto:"
]

FRASES_CIERRE = [
    "🌙 *¡Ya cerró el kiosko!* Mañana seguimos haciendo plata:",
    "😴 *¡A mimir!* El mercado se fue a dormir y tú también deberías.",
    "🍻 *¡Nos fuimos!* Cierra la laptop y descansa. Así quedó la cosa:",
    "🌚 *¡Chau chau!* Se acabó la jarana por hoy. Datos finales:",
    "🛑 *¡Baja la cortina!* Ya no hay atención hasta mañana.",
    "🍜 *¡Chaufa!* Se terminó la jornada. Anda pide tu delivery.",
    "🔚 *¡Game Over!* Se acabó el día bursátil. Aquí la foto final:"
]

FRASES_COMPRA = [
    "\n🐷 *¡ROMPE EL CHANCHITO!* El dólar está en el suelo.\n✅ Compra barato, vende caro.",
    "\n🤑 *¡OFERTA DE INFARTO!* Está más barato que menú de mercado.\n✅ Aprovecha y compra.",
    "\n📉 *¡ESTÁ REGALADO!* Si tienes soles, vuélvelos dólares AL TOQUE.",
    "\n🥚 *¡PRECIO DE HUEVO!* Está baratito casero.\n✅ Llévatelo antes que se acabe.",
    "\n🛏️ *¡SACA LO DEL COLCHÓN!* Es momento de stockearse de verdes.",
    "\n🏃 *¡CORRE AL BANCO!* Está bajando rico.\n✅ Asegura tu chivilín."
]

FRASES_VENTA = [
    "\n🚀 *¡SE FUE A LAS NUBES!* Asu mare, qué tal subida.\n✅ Vende tus dólares.",
    "\n💰 *¡ESTÁ CAROLINE!* El dólar está por los techos.\n✅ Cobra rico.",
    "\n🔥 *¡VENDE TODO!* Sácale el jugo a esta subida.\n✅ Gánate el extra.",
    "\n😱 *¡ASU QUÉ PALTA!* Qué tal subidón.\n✅ Si tienes dólares, hoy te consagras.",
    "\n🤑 *¡HAZTE UNA!* El gringo está power.\n✅ Vende y date ese gustito.",
    "\n📈 *¡ESTÁ PICANTE!* Aprovecha el pánico y vende caro."
]

FRASES_SUBIDA = [
    "\n📈 *Ojo al piojo:* Está subiendo rápido. Piensa en vender.",
    "\n🚀 *Despegando:* El gringo se está poniendo fuerte.",
    "\n👀 *¡Yara!* Se está disparando. Checa bien tu billetera.",
    "\n🍺 *¡Sube como espuma!* Hoy podrías salir ganadazo.",
    "\n😨 *¡Aguanta tu coche!* Está trepando. Preocúpate un poquito.",
    "\n🧗 *¡Se fue pa' arriba!* Está escalando. Asegura la papa.",
    "\n🔥 *¡Calentando motores!* Quiere romper el techo."
]

FRASES_BAJADA = [
    "\n📉 *Se cae, se cae:* Está bajando. Prepárate.",
    "\n🥶 *Se congeló:* Está bajando el precio. Compra ya.",
    "\n📉 *De bajada:* Parece tobogán. Atento para pagar deudas.",
    "\n⛷️ *¡Bajada de reyes!* Está cayendo rico.",
    "\n🎈 *¡Se desinfló!* Perdiendo fuerza. Acumula verdes.",
    "\n😎 *¡Tranqui!* Bajando la marea. Va llegando tu hora.",
    "\n📉 *¡Suelo, suelo!* Yendo para abajo. Aprovecha."
]

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except: pass

def obtener_precio_local_api():
    """Obtiene el precio de venta desde la API de la SUNAT (100% estable)"""
    url = "https://api.apis.net.pe/v1/tipo-cambio-sunat"
    try:
        print("🕵️ Consultando API Oficial (SUNAT)...")
        # Ya no necesitamos hacernos pasar por un navegador, es una API oficial
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            datos = response.json()
            precio_venta = float(datos['venta'])
            print(f"✅ Precio local encontrado: S/ {precio_venta}")
            return precio_venta
        else:
            print(f"❌ Error de API: {response.status_code}")
            return None
    except Exception as e:
        print(f"💥 Error técnico API: {e}")
        return None

def leer_estado():
    if not os.path.exists(ARCHIVO_ESTADO): return {}
    try:
        with open(ARCHIVO_ESTADO, 'r') as f: return json.load(f)
    except: return {}

def guardar_estado(datos):
    with open(ARCHIVO_ESTADO, 'w') as f: json.dump(datos, f)

def analizar_mercado():
    print("Iniciando análisis con estilo...")
    
    zona_peru = pytz.timezone('America/Lima')
    ahora = datetime.now(zona_peru)
    hora = ahora.hour
    fecha_hoy = ahora.strftime("%Y-%m-%d")
    hora_texto = ahora.strftime("%I:%M %p")

    estado = leer_estado()
    ultimo_precio = estado.get('precio', 0.0)
    ultima_apertura = estado.get('fecha_apertura', "")
    ultimo_cierre = estado.get('fecha_cierre', "")

    try:
        data = yf.download(TICKER, period="1mo", interval="1d", progress=False, multi_level_index=False)
    except: return
    if data.empty: return

    precio_oficial = data['Close'].iloc[-1].item()
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    # NUEVO: Usamos la API estable
    precio_local = obtener_precio_local_api()
    precio_actual = precio_local if precio_local else precio_oficial
    
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

    diferencia = abs(precio_actual - ultimo_precio)
    enviar = False

    if tipo_reporte == "FORZAR_ENVIO":
        enviar = True
    else:
        if diferencia >= 0.003: enviar = True
        if precio_actual <= min_mes and diferencia > 0: enviar = True
        if precio_actual >= max_mes and diferencia > 0: enviar = True

    frase_accion = ""
    
    if precio_actual <= min_mes:
        frase_accion = random.choice(FRASES_COMPRA)
    elif precio_actual >= max_mes:
        frase_accion = random.choice(FRASES_VENTA)
    elif diferencia >= 0.003:
        if precio_actual > ultimo_precio:
            frase_accion = random.choice(FRASES_SUBIDA)
        else:
            frase_accion = random.choice(FRASES_BAJADA)

    if enviar:
        icono_precio = ""
        if precio_actual <= min_mes: icono_precio = "🚨 BAJÓ"
        elif precio_actual >= max_mes: icono_precio = "🔥 SUBIÓ"

        # Actualizamos la etiqueta para que sepas que viene de SUNAT
        txt_local = f"S/ {precio_local:.3f}" if precio_local else "⚠️ N/D"

        if not mensaje_intro:
            mensaje_intro = f"🔔 *¡ALERTA CAUSA!* Se movió el dólar"

        mensaje = (
            f"{mensaje_intro}\n"
            f"🕒 _{hora_texto}_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🇵🇪 *Perú (SUNAT):* {txt_local} {icono_precio}\n"
            f"🏦 *Gringo (Yahoo):* S/ {precio_oficial:.3f}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📉 Min Mes: {min_mes:.3f}\n"
            f"📈 Max Mes: {max_mes:.3f}\n"
            f"{frase_accion}"
        )

        enviar_telegram(mensaje)
        estado['precio'] = precio_actual
        guardar_cambios = True
    else:
        print(f"Sin novedades. Diferencia: {diferencia:.4f}. No molestamos.")
        
    if guardar_cambios:
        guardar_estado(estado)
    print("✅ Ejecución finalizada.")

if __name__ == "__main__":
    analizar_mercado()
