'''
Realiza análisis automáticos de criptomonedas

Para realizar un análisis de una criptomoneda es necesario cambiar la configuración 
antes de ejecutar este fichero estableciendo el valor de "currencyBase" con el
identificador de la criptomoneda en mayusculas.
'''

CONFIGURATION = {
    "botId": "MarketView1",
    "exchangeId": "coinex",
    "currencies": ["BTC", "ETH", "SOL"],    # El analisis se realiza a estas criptomoneda.
    "currencyQuote": "USDT",                # Esta es la criptomoneda con la que se contabiliza el precio.
    "sound": False,
    "telegramBotToken": "TOKEN_DEL_BOT_QUE_ENVIA_EL_CONTENIDO",     # Bot que envía informes al canal Telegram.
    "telegramChatsId": ["@IDENTIFICADOR_DEL_CANAL"]                 # Canales de Telegram donde se informa.
}


import time
from market_view import analyze_market
if __name__ == "__main__":
    analyze_market(CONFIGURATION)
    time.sleep(60)
