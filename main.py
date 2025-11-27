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
    url = "https://cuantoestaeldolar.pe/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        precios = soup.find_all('p', class_=lambda x: x and 'ValueCurrency_item_cost' in x)
        if len(precios) >= 4:
            return float(precios[3].text.strip())
        return None
    except:
        return None

# --- NUEVAS FUNCIONES DE MEMORIA (JSON) ---
def leer_estado():
    """Lee todo el diccionario del JSON"""
    if not os.path.exists(ARCHIVO_ESTADO):
        return {}
    try:
        with open(ARCHIVO_ESTADO, 'r') as f:
            return json.load(f)
    except:
        return {}

def guardar_estado(datos):
    """Guarda el diccionario completo"""
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump(datos, f)

def analizar_mercado():
    print("Iniciando análisis inteligente...")
    
    # 1. PREPARAR FECHAS Y HORAS
    zona_peru = pytz.timezone('America/Lima')
    ahora = datetime.now(zona_peru)
    hora = ahora.hour
    minuto = ahora.minute
    hora_texto = ahora.strftime("%I:%M %p")
    fecha_hoy = ahora.strftime("%Y-%m-%d") # Ej: 2025-11-27

    # 2. LEER MEMORIA
    estado = leer_estado()
    ultimo_precio = estado.get('precio', 0.0)
    ultima_apertura = estado.get('fecha_apertura', "")
    ultimo_cierre = estado.get('fecha_cierre', "")

    # 3. OBTENER DATOS DEL MERCADO
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    if data.empty: return

    precio_oficial = data['Close'].iloc[-1].item()
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    precio_paralelo = obtener_precio_callejero()
    precio_actual = precio_paralelo if precio_paralelo else precio_oficial
    
    # 4. LÓGICA DE DECISIÓN
    tipo_reporte = "NORMAL"
    mensaje_intro = ""
    icono_titulo = "🔔"
    guardar_cambios = False

    # CASO A: APERTURA (9 AM)
    # Solo entramos si NO hemos saludado HOY todavía
    if hora == 9 and ultima_apertura != fecha_hoy:
        tipo_reporte = "FORZAR_ENVIO"
        icono_titulo = "☕ BUENOS DÍAS"
        mensaje_intro = "☀️ *APERTURA DE MERCADO*\nHoy comenzamos con estos valores:"
        estado['fecha_apertura'] = fecha_hoy # Marcamos que ya saludamos hoy
        guardar_cambios = True

    # CASO B: CIERRE (6 PM)
    # Solo entramos si NO hemos despedido HOY todavía
    elif hora == 18 and ultimo_cierre != fecha_hoy:
        tipo_reporte = "FORZAR_ENVIO"
        icono_titulo = "🌙 BUENAS NOCHES"
        mensaje_intro = "🌚 *CIERRE DE MERCADO*\nHoy el mercado cerró con los siguientes valores:"
        estado['fecha_cierre'] = fecha_hoy # Marcamos que ya despedimos hoy
        guardar_cambios = True

    # CASO C: VIGILANCIA NORMAL (10 AM - 5 PM)
    diferencia = abs(precio_actual - ultimo_precio)
    enviar = False

    if tipo_reporte == "FORZAR_ENVIO":
        enviar = True
    else:
        # Lógica de silencio: Solo avisa si cambia 0.003 o toca extremos
        if diferencia >= 0.003: enviar = True
        if precio_actual <= min_mes and diferencia > 0: enviar = True
        if precio_actual >= max_mes and diferencia > 0: enviar = True

    # 5. ENVIAR Y GUARDAR
    if enviar:
        print(f"Enviando reporte: {icono_titulo}")
        
        icono_precio = ""
        if precio_actual <= min_mes: icono_precio = "🚨 MIN"
        elif precio_actual >= max_mes: icono_precio = "💰 MAX"

        txt_paralelo = f"S/ {precio_paralelo:.3f}" if precio_paralelo else "⚠️ N/D"

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
        
        # Actualizamos el precio en memoria
        estado['precio'] = precio_actual
        guardar_cambios = True
    
    # 6. GUARDADO FINAL (Si hubo saludo o cambio de precio)
    if guardar_cambios:
        guardar_estado(estado)

if __name__ == "__main__":
    analizar_mercado()
