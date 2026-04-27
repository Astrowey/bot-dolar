import yfinance as yf
import requests
import os
import json
import random
import re  # <--- NUEVO IMPORT NECESARIO PARA KAMBISTA
from datetime import datetime
import pytz 
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ARCHIVO_ESTADO = 'estado.json'

# --- FRASES CON CALLE ---
FRASES_APERTURA = [
    "☀️ *¡Habla causa!* Arranca el mercado. Agarra tu café que aquí vamos:",
    "🐓 *¡Quiquiriquí!* Despierta oye, que el dinero no duerme (y la inflación tampoco).",
    "🚀 *¡Arriba Perú!* Vamos a ver cómo se porta el gringo hoy. Atento a la jugada:",
    "😎 *¡Buenos días alegría!* A chambear que la plata no cae del cielo.",
    "🔋 *¡Habla batería seria!* Carga pilas que hoy se factura. Así amanecemos:",
    "☕ *¡Despierta!* Ni el gallo se levantó tan temprano, pero el dólar sí. Checa:",
    "🧢 *¡Alao!* ¿Todo chill? Vamos a ver si hoy nos hacemos millonarios o seguimos misios:",
    "🔔 *¡Ding dong!* Abrió el mercado, mano. Deja de procrastinar y mira esto:"
]

FRASES_CIERRE = [
    "🌙 *¡Ya cerró el kiosko!* Mañana seguimos haciendo plata. Así terminamos:",
    "😴 *¡A mimir!* El mercado se fue a dormir y tú también deberías. Resumen:",
    "🍻 *¡Nos fuimos!* Cierra la laptop y descansa. Así quedó la cosa:",
    "🌚 *¡Chau chau!* Se acabó la jarana por hoy. Nos vidrios mañana con estos datos:",
    "🛑 *¡Baja la cortina!* Ya no hay atención hasta mañana. Anda descansa, tigre.",
    "🍜 *¡Chaufa!* Se terminó la jornada. Anda pide tu delivery y relájate.",
    "🔚 *¡Game Over!* Se acabó el día bursátil. Aquí la foto final:"
]

FRASES_COMPRA = [
    "\n🐷 *¡ROMPE EL CHANCHITO!* El dólar está en el suelo.\n✅ Compra barato, vende caro (ley de vida).",
    "\n🤑 *¡OFERTA DE INFARTO!* Está más barato que menú de mercado.\n✅ Aprovecha y compra unos cocos.",
    "\n📉 *¡ESTÁ REGALADO!* Si tienes soles, vuélvelos dólares AL TOQUE.\n✅ Oportunidad de compra detectada.",
    "\n🥚 *¡PRECIO DE HUEVO!* Está baratito casero.\n✅ Llévatelo antes que se acabe.",
    "\n🛏️ *¡SACA LO DEL COLCHÓN!* Es momento de stockearse de verdes.\n✅ No lo pienses mucho o te ganan.",
    "\n🏃 *¡CORRE AL BANCO!* Está bajando rico.\n✅ Aprovecha la oferta y asegura tu chivilín."
]

FRASES_VENTA = [
    "\n🚀 *¡SE FUE A LAS NUBES!* Asu mare, qué tal subida.\n✅ Vende tus dólares y hazte millonario.",
    "\n💰 *¡ESTÁ CAROLINE!* El dólar está por los techos.\n✅ Momento perfecto para vender y cobrar rico.",
    "\n🔥 *¡VENDE TODO!* Sácale el jugo a esta subida.\n✅ Cambia esos dólares a soles y gánate el extra.",
    "\n😱 *¡ASU QUÉ PALTA!* Qué tal subidón.\n✅ Si tienes dólares, hoy te consagras. ¡Vende!",
    "\n🤑 *¡HAZTE UNA!* El gringo está power.\n✅ Vende y date ese gustito que querías.",
    "\n📈 *¡ESTÁ PICANTE!* Aprovecha el pánico y vende caro.\n✅ Hoy se factura en grande."
]

FRASES_SUBIDA = [
    "\n📈 *Ojo al piojo:* Está subiendo rápido. Si necesitas soles, anda pensando en vender.",
    "\n🚀 *Despegando:* El gringo se está poniendo fuerte. Atento a la jugada.",
    "\n👀 *¡Yara!* Se está disparando el precio. Checa bien tu billetera.",
    "\n⛰️ *¡Como espuma!* Sube y sube. Si debes en dólares, empieza a preocuparte.",
    "\n✈️ *¡Se va, se va!* El dólar agarra vuelo. Si querías comprar, ya fuiste (por ahora).",
    "\n🌶️ *¡Está picante!* La cosa se pone caliente. No te duermas."
]

FRASES_BAJADA = [
    "\n📉 *Se cae, se cae:* Está bajando. Si querías comprar, prepárate.",
    "\n🥶 *Se congeló:* Está bajando el precio. Aguanta un poco más o compra ya.",
    "\n📉 *De bajada:* Parece tobogán. Si tienes deudas en dólares, atento para pagar.",
    "\n🎢 *¡Tobogán!* Se está chorreando el precio. A río revuelto, ganancia de pescadores.",
    "\n📉 *¡Suelo, suelo!* Está perdiendo fuerza. Atento para pescar la oferta.",
    "\n😌 *¡Respira!* Está bajando. Al fin un respiro para tu bolsillo."
]

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except: pass

def obtener_precio_callejero():
    # Consultamos Kambista, la primera casa de cambio online en Perú
    url = "https://kambista.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print("🕵️ Buscando precio en Kambista...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200: 
            print(f"❌ Error HTTP: La página bloqueó la conexión (Código {response.status_code})")
            return None
            
        # Kambista siempre incluye su tasa con el formato "Venta: 3.XXX" en su texto
        match = re.search(r'Venta:\s*(\d+\.\d+)', response.text)
        
        if match:
            precio = float(match.group(1))
            print(f"✅ Precio callejero encontrado: {precio}")
            return precio
        else:
            print("⚠️ Alerta: La web cambió su diseño de texto.")
            return None
            
    except Exception as e:
        print(f"💥 Error técnico al leer la web: {e}")
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

    precio_paralelo = obtener_precio_callejero()
    precio_actual = precio_paralelo if precio_paralelo else precio_oficial
    
    tipo_reporte = "NORMAL"
    mensaje_intro = ""
    # Seleccionamos frases aleatorias para que no aburra
    intro_random_apertura = random.choice(FRASES_APERTURA)
    intro_random_cierre = random.choice(FRASES_CIERRE)
    
    guardar_cambios = False

    # Apertura
    if hora == 9 and ultima_apertura != fecha_hoy:
        tipo_reporte = "FORZAR_ENVIO"
        mensaje_intro = intro_random_apertura
        estado['fecha_apertura'] = fecha_hoy
        guardar_cambios = True

    # Cierre
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

    # --- ESCOGER LA FRASE PICARESCA ---
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

        txt_paralelo = f"S/ {precio_paralelo:.3f}" if precio_paralelo else "⚠️ N/D"

        if not mensaje_intro:
            mensaje_intro = f"🔔 *¡ALERTA CAUSA!* Se movió el dólar"

        mensaje = (
            f"{mensaje_intro}\n"
            f"🕒 _{hora_texto}_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Calle:* {txt_paralelo} {icono_precio}\n"
            f"🏦 *Oficial:* S/ {precio_oficial:.3f}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📉 Min Mes: {min_mes:.3f}\n"
            f"📈 Max Mes: {max_mes:.3f}\n"
            f"{frase_accion}"
        )

        enviar_telegram(mensaje)
        estado['precio'] = precio_actual
        guardar_cambios = True
    
    if guardar_cambios:
        guardar_estado(estado)
    print("✅ Ejecución finalizada.")

if __name__ == "__main__":
    analizar_mercado()
