import yfinance as yf
import requests
import os
import json # Necesario para la memoria
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
    # Tu misma lógica de Scraping de antes...
    url = "https://cuantoestaeldolar.pe/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
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
    """Lee el archivo JSON para saber qué precio enviamos la última vez"""
    if not os.path.exists(ARCHIVO_ESTADO):
        return 0.0
    try:
        with open(ARCHIVO_ESTADO, 'r') as f:
            datos = json.load(f)
            return datos.get('precio', 0.0)
    except:
        return 0.0

def guardar_nuevo_precio(precio):
    """Guarda el precio actual en el JSON"""
    with open(ARCHIVO_ESTADO, 'w') as f:
        json.dump({'precio': precio}, f)

def analizar_mercado():
    print("Iniciando escaneo...")
    
    # 1. OBTENER DATOS
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    if data.empty: return

    precio_oficial = data['Close'].iloc[-1].item()
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    precio_paralelo = obtener_precio_callejero()
    
    # Precio real para la alerta
    precio_actual = precio_paralelo if precio_paralelo else precio_oficial
    fuente = "Paralelo" if precio_paralelo else "Oficial"

    # 2. VERIFICAR MEMORIA (ANTI-SPAM)
    ultimo_precio_avisado = leer_ultimo_precio()
    
    # Calculamos la diferencia
    diferencia = abs(precio_actual - ultimo_precio_avisado)
    
    # REGLA DE ORO: ¿Vale la pena molestar al usuario?
    # Avisar SOLO SI:
    # A. El precio cambió significativamente (más de 0.002 céntimos)
    # B. O llegamos a un extremo histórico (Min/Max) y el precio cambió un poco
    
    es_importante = False
    
    if diferencia >= 0.003: # Si subió/bajó al menos 0.003, avisar siempre
        es_importante = True
    elif precio_actual <= min_mes and diferencia > 0: # Si es mínimo histórico y cambió algo
        es_importante = True
    elif precio_actual >= max_mes and diferencia > 0: # Si es máximo histórico y cambió algo
        es_importante = True

    if not es_importante:
        print(f"El precio {precio_actual} es similar al anterior ({ultimo_precio_avisado}). No molestamos.")
        return # TERMINA AQUÍ, NO ENVÍA NADA

    # 3. SI ES IMPORTANTE, ENVIAMOS Y GUARDAMOS
    print("¡Cambio detectado! Enviando alerta...")
    
    zona_peru = pytz.timezone('America/Lima')
    hora_peru = datetime.now(zona_peru).strftime("%I:%M %p")
    
    icono = "🔔"
    if precio_actual <= min_mes: icono = "🚨 COMPRA"
    elif precio_actual >= max_mes: icono = "💰 VENTA"

    txt_paralelo = f"S/ {precio_paralelo:.3f}" if precio_paralelo else "⚠️ N/D"

    mensaje = (
        f"{icono} *CAMBIO EN EL DÓLAR*\n"
        f"🕒 {hora_peru}\n"
        f"💵 *Calle:* {txt_paralelo}\n"
        f"🏦 *Oficial:* S/ {precio_oficial:.3f}\n"
        f"📉 Min: {min_mes:.3f} | 📈 Max: {max_mes:.3f}"
    )

    enviar_telegram(mensaje)
    
    # ACTUALIZAMOS LA MEMORIA
    guardar_nuevo_precio(precio_actual)

if __name__ == "__main__":
    analizar_mercado()
