import yfinance as yf
import requests
import os
from datetime import datetime
import pytz # Para manejar la hora de Perú

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def enviar_telegram(mensaje):
    if not TOKEN or not CHAT_ID:
        print("Error: Credenciales no encontradas.")
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # parse_mode="Markdown" permite usar negritas y formato
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, data=data)
        print("Mensaje enviado a Telegram.")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

def analizar_mercado():
    print(f"Analizando {TICKER}...")
    
    # Descargar datos
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    if data.empty:
        return

    # Obtener valores
    precio_actual = data['Close'].iloc[-1].item()
    historial_pasado = data['Close'].iloc[:-1]
    min_mes = historial_pasado.min().item()
    max_mes = historial_pasado.max().item()
    
    # Definir el "Estado" del mercado para el reporte
    aviso_especial = ""
    icono_estado = "🟢" # Verde por defecto (Estable)
    
    if precio_actual <= min_mes:
        icono_estado = "🚨"
        aviso_especial = "\n🔥 *¡ATENCIÓN!* Estamos en un *MINIMO MENSUAL*. Buen momento para comprar."
    elif precio_actual >= max_mes:
        icono_estado = "💰"
        aviso_especial = "\n🚀 *¡ATENCIÓN!* Estamos en un *MAXIMO MENSUAL*. Buen momento para vender."

    # Obtener hora de Perú para el mensaje
    zona_peru = pytz.timezone('America/Lima')
    hora_peru = datetime.now(zona_peru).strftime("%d/%m/%Y %I:%M %p")

    # --- CREANDO EL MENSAJE BONITO ---
    mensaje = (
        f"📊 *REPORTE DEL DÓLAR* 🇵🇪\n"
        f"🕒 _{hora_peru}_\n\n"
        f"💵 *Precio Actual:* S/ {precio_actual:.3f} {icono_estado}\n\n"
        f"📉 *Mínimo (30d):* S/ {min_mes:.3f}\n"
        f"📈 *Máximo (30d):* S/ {max_mes:.3f}\n"
        f"{aviso_especial}"
    )

    # Enviamos el reporte SIEMPRE (Reporte Diario)
    enviar_telegram(mensaje)

if __name__ == "__main__":
    analizar_mercado()
