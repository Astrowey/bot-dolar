import yfinance as yf
import requests
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
TICKER = "PEN=X"  # Dólar vs Sol
TOKEN = os.getenv('TELEGRAM_TOKEN') # La clave secreta de tu bot
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') # Tu ID de usuario en Telegram

def enviar_telegram(mensaje):
    print(f"--> Intentando enviar mensaje a ID: {CHAT_ID}...") # Para verificar que leyó el ID
    
    if not TOKEN or not CHAT_ID:
        print("Error: Faltan las credenciales (Token o ID) en los Secrets.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    
    # Aquí capturamos la respuesta de Telegram
    response = requests.post(url, data=data)
    
    # Imprimimos el resultado (Éxito o Error)
    print(f"Respuesta de Telegram: {response.status_code}")
    print(f"Detalle: {response.text}")

def analizar_mercado():
    print(f"Analizando {TICKER}...")
    
    # 1. Descargar datos del último mes (intervalo diario)
    data = yf.download(TICKER, period="1mo", interval="1d", progress=False)
    
    if data.empty:
        print("No se pudieron obtener datos.")
        return

    # 2. Obtener precios (El último dato disponible es el precio actual/cierre de hoy)
    precio_actual = data['Close'].iloc[-1].item() # .item() convierte de numpy a float nativo
    
    # Calculamos min y max EXCLUYENDO el día de hoy para comparar
    historial_pasado = data['Close'].iloc[:-1] 
    min_mes = historial_pasado.min().item()
    max_mes = historial_pasado.max().item()

    print(f"Precio Actual: {precio_actual:.4f}")
    print(f"Mínimo (30 días): {min_mes:.4f} | Máximo (30 días): {max_mes:.4f}")

    # 3. Lógica de Alertas
    if precio_actual <= min_mes:
        msg = f"🚨 BAJO HISTÓRICO (Mes): El dólar bajó a S/ {precio_actual:.3f}. Es buen momento para COMPRAR."
        enviar_telegram(msg)
        print("Alerta de compra enviada.")
        
    elif precio_actual >= max_mes:
        msg = f"📈 ALTO HISTÓRICO (Mes): El dólar subió a S/ {precio_actual:.3f}. Es buen momento para VENDER."
        enviar_telegram(msg)
        print("Alerta de venta enviada.")
    else:
        print("El precio está estable dentro del rango mensual. No se envía alerta.")

if __name__ == "__main__":
    # La prueba ya funcionó, ahora solo analizamos
    analizar_mercado()
