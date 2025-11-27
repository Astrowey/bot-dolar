import yfinance as yf
import requests
import os
from datetime import datetime
import pytz 
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        print("Error: Credenciales no encontradas.")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, data=data)
        print("Mensaje enviado a Telegram.")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def obtener_precio_callejero():
    """Obtiene el precio paralelo de venta"""
    url = "https://cuantoestaeldolar.pe/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200: return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos etiquetas <p> con la clase parcial correcta
        precios = soup.find_all('p', class_=lambda x: x and 'ValueCurrency_item_cost' in x)

        if len(precios) >= 4:
            # Índice 3 suele ser Venta Paralelo
            return float(precios[3].text.strip())
        return None

    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def analizar_mercado():
    print("Iniciando análisis dual...")
    
    # 1. DATOS OFICIALES (Yahoo)
    # Usamos esto para el precio oficial y para el historial (Máximos/Mínimos)
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    
    if data.empty:
        print("Error crítico: Yahoo no responde.")
        return

    precio_oficial = data['Close'].iloc[-1].item()
    historial = data['Close'].iloc[:-1]
    min_mes = historial.min().item()
    max_mes = historial.max().item()

    # 2. DATOS PARALELOS (Scraping)
    precio_paralelo = obtener_precio_callejero()

    # 3. LÓGICA DE ALERTA (Usamos el Paralelo para decidir, si existe)
    # Si no hay paralelo, usamos el oficial para la alerta
    precio_referencia = precio_paralelo if precio_paralelo else precio_oficial
    
    icono_alerta = ""
    aviso_especial = ""

    if precio_referencia <= min_mes:
        icono_alerta = "🚨"
        aviso_especial = "\n🔥 *¡OPORTUNIDAD DE COMPRA!* (Precio bajo histórico)"
    elif precio_referencia >= max_mes:
        icono_alerta = "💰"
        aviso_especial = "\n🚀 *¡OPORTUNIDAD DE VENTA!* (Precio alto histórico)"

    # 4. CONSTRUCCIÓN DEL MENSAJE DUAL
    zona_peru = pytz.timezone('America/Lima')
    hora_peru = datetime.now(zona_peru).strftime("%d/%m/%Y %I:%M %p")

    # Formateamos el texto del paralelo (por si falla la web, que diga "No disp.")
    txt_paralelo = f"S/ {precio_paralelo:.3f}" if precio_paralelo else "⚠️ No disponible"

    mensaje = (
        f"📊 *REPORTE DUAL DÓLAR* 🇵🇪\n"
        f"🕒 _{hora_peru}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 *PARALELO (Calle):* {txt_paralelo} {icono_alerta}\n"
        f"🏦 *OFICIAL (Bancos):* S/ {precio_oficial:.3f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📉 *Mínimo Mes:* S/ {min_mes:.3f}\n"
        f"📈 *Máximo Mes:* S/ {max_mes:.3f}\n"
        f"{aviso_especial}"
    )

    enviar_telegram(mensaje)

if __name__ == "__main__":
    analizar_mercado()
