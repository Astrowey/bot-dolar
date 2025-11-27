import yfinance as yf
import requests
import os
import json
from datetime import datetime
import pytz 
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ARCHIVO_ESTADO = 'estado.json'

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except:
        pass

def obtener_precio_callejero():
    """Intenta obtener precio de cuantoestaeldolar.pe"""
    url = "https://cuantoestaeldolar.pe/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        precios = soup.find_all('p', class_=lambda x: x and 'ValueCurrency_item_cost' in x)
        if len(precios) >= 4:
            return float(precios[3].text.strip()) # Venta Paralelo
        return None
    except:
        return None

def leer_ultimo_precio():
    if not os.path.exists(ARCHIVO_ESTADO): return 0.0
    try:
        with open(ARCHIVO_ESTADO, 'r') as f:
            datos = json.load(f)
            return datos.get('precio', 0.0)
    except: return 0.0

def guardar_nuevo_precio(precio):
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump({'precio': precio}, f)

def analizar_mercado():
    print("Iniciando análisis inteligente...")
    
    # 1. PREPARAR HORARIOS (PERÚ)
    zona_peru = pytz.timezone('America/Lima')
    ahora = datetime.now(zona_peru)
    hora = ahora.hour      # Formato 24h (9, 10... 18)
    minuto = ahora.minute
    hora_texto = ahora.strftime("%I:%M %p")

    # 2. OBTENER DATOS
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    if data.empty: return

    precio_oficial = data['Close'].iloc[-1].item()
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    precio_paralelo = obtener_precio_callejero()
    precio_actual = precio_paralelo if precio_paralelo else precio_oficial
    
    # 3. LÓGICA DE MENSAJES DE APERTURA Y CIERRE
    # GitHub a veces se demora unos minutos en arrancar, damos margen de 15 min.
    
    tipo_reporte = "NORMAL" # Por defecto
    mensaje_intro = ""
    icono_titulo = "🔔"
    
    # CASO A: APERTURA (Entre 9:00 AM y 9:15 AM)
    if hora == 9 and minuto < 60:
        tipo_reporte = "FORZAR_ENVIO"
        icono_titulo = "☕ BUENOS DÍAS"
        mensaje_intro = "☀️ *APERTURA DE MERCADO*\nHoy comenzamos con estos valores:"

    # CASO B: CIERRE (Entre 6:00 PM y 6:15 PM)
    elif hora == 18 and minuto < 60:
        tipo_reporte = "FORZAR_ENVIO"
        icono_titulo = "🌙 BUENAS NOCHES"
        mensaje_intro = "🌚 *CIERRE DE MERCADO*\nHoy el mercado cerró con los siguientes valores:"

    # 4. LÓGICA DE ALERTA (Anti-Spam)
    ultimo_precio = leer_ultimo_precio()
    diferencia = abs(precio_actual - ultimo_precio)
    
    enviar = False

    if tipo_reporte == "FORZAR_ENVIO":
        # Si es hora de apertura o cierre, enviamos SÍ O SÍ
        enviar = True
    else:
        # Si es horario normal, solo enviamos si hay cambios importantes
        if diferencia >= 0.003: enviar = True
        if precio_actual <= min_mes and diferencia > 0: enviar = True
        if precio_actual >= max_mes and diferencia > 0: enviar = True

    # 5. ENVIAR MENSAJE
    if enviar:
        print(f"Enviando reporte tipo: {icono_titulo}")
        
        # Icono de alerta extrema
        icono_precio = ""
        if precio_actual <= min_mes: icono_precio = "🚨 MIN"
        elif precio_actual >= max_mes: icono_precio = "💰 MAX"

        txt_paralelo = f"S/ {precio_paralelo:.3f}" if precio_paralelo else "⚠️ N/D"

        # Si no hay intro especial (es una alerta normal), ponemos título estándar
        if not mensaje_intro:
            mensaje_intro = f"🔔 *CAMBIO DETECTADO*"

        mensaje = (
            f"{icono_titulo}\n"
            f"{mensaje_intro}\n"
            f"🕒 _{hora_texto}_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Calle:* {txt_paralelo} {icono_precio}\n"
            f"🏦 *Oficial:* S/ {precio_oficial:.3f}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📉 Min Mes: {min_mes:.3f}\n"
            f"📈 Max Mes: {max_mes:.3f}"
        )

        enviar_telegram(mensaje)
        guardar_nuevo_precio(precio_actual)
    else:
        print("Sin cambios importantes. Modo silencio.")

if __name__ == "__main__":
    analizar_mercado()
