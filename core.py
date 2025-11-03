
import time
from exchange import *
from winsound import Beep
from basics import *
import datetime
from statistics import mean, stdev
from files import *
from analysis_candles import *
import webbrowser


DIRECTORY_DATA = "analysis"
DIRECTORY_DATETIME_PREFIX = "report"


class Core(Basics):

    def __init__(self, config:Dict):
        self.config = config
        self.exchange = Exchange(self.config["exchangeId"], "", "")
        self.milliseconds = self.exchange.exchange.milliseconds()
        self.datetimeLocal = datetime.datetime.now()
        self.datetimeIso8601 = self.exchange.exchange.iso8601(self.milliseconds)
        self.datetimeUTC = datetime.datetime.strptime(self.datetimeIso8601, "%Y-%m-%dT%H:%M:%S.%fz")
        fileNameCommon = '{}_{}_{}'.format(
            self.config["exchangeId"], 
            self.config["currencyBase"],
            self.config["currencyQuote"]
        ) 
        #self.fileNameLastRanking = '{}/{}_last_ranking.json'.format(self.script_path(), fileNameCommon) 
        #self.fileNamePreviousTickers = '{}/{}_previous_tickers1.json'.format(self.script_path(), fileNameCommon)
        self.pricesToCompare = {}
        
        if self.config["sound"]:
            Beep(440, 300)
        self.print_head()
        log.info(f'\nBotId: {self.config["botId"]}')
        log.info(f'ExchangeId: {self.config["exchangeId"]}')
        log.info(f'CurrencyBase: {self.config["currencyBase"]}')
        log.info(f'CurrencyQuote: {self.config["currencyQuote"]}')
        log.info(f'DatetimeLocal: {self.datetimeLocal}')
        log.info(f'DatetimeUTC: {self.datetimeUTC}')
        


    def get_data_of_market(self) -> bool:
        markets = self.exchange.get_markets()
        currencies = self.exchange.get_currencies()
        if markets is not None and currencies is not None:
            baseId = self.config["currencyBase"]
            quoteId = self.config["currencyQuote"]
            marketId = f'{baseId}/{quoteId}'
            marketData = {}
            marketData["exchangeId"] = self.config["exchangeId"]
            marketData["marketId"] = marketId
            marketData["baseId"] = baseId
            marketData["quoteId"] = quoteId
            marketData["ticker"] = self.exchange.get_ticker(marketId)
            marketData["market"] = markets.get(marketId)
            marketData["base"] = currencies.get(baseId)
            marketData["quote"] = currencies.get(quoteId)
            marketData["reportTimestamp"] = self.milliseconds
            marketData["reportDatetimeUTC"] = self.datetimeIso8601
            ticker = marketData["ticker"]
            if ticker["bid"] is not None and ticker["ask"] is not None:
                if ticker["open"] is not None and ticker["high"] is not None \
                    and ticker["low"] is not None and ticker["close"] is not None \
                    and ticker["quoteVolume"] is not None:
                    marketData["ticker"]['bestSpreadOnLast24h'] = self.delta(ticker["bid"], ticker["ask"])
                    marketData["ticker"]['amplitude'] = float(ticker["high"] - ticker["low"])
                    marketData["ticker"]['amplitudeAsPercent'] = self.delta(ticker["low"], ticker["high"])
                    marketData["ticker"]['percentagePerMinute'] = ticker["percentage"] / (24 * 60)
                    marketData["ticker"]['volumePerMinute'] = float(ticker["quoteVolume"] / 24 / 60)
                    log.info('OBTENIDO: ticker')

            marketData["minimunAmountAsBase"] = marketData["market"]['limits']['amount']["min"]
            marketData["maximunAmountAsBase"] = marketData["market"]['limits']['amount']["min"]

            #orderBook = self.exchange.get_order_book(marketId, 100)
            #if orderBook is not None:
            #    if len(orderBook.get("bids", [])) > 0 and len(orderBook.get("asks", [])) > 0:
            #        marketData['spread'] = self.delta(orderBook["bids"][0][0], orderBook["asks"][0][0])
            #        marketData['deltaAsks'] = self.delta_of_order_book(orderBook, 1000, "asks") 
            #        marketData['deltaBids'] = self.delta_of_order_book(orderBook, 1000, "bids") 
            #        log.info('OBTENIDO: orderBook')

            #marketData['candles'] = []
            #for candles in CONFIGURATION["candles"]:
            #    candles["marketId"] = marketId
            #    candles["data"] = self.exchange.get_last_candles(marketId, candles["count"], candles["temporality"])
            #    candles["datetimes"] = [self.exchange.exchange.iso8601(x[0]) for x in candles["data"]]
            #    candles['metrics'] = self.metrics(candles, marketData)
            #    candles["closeConditions"] = self.close_conditions(candles, marketData)
            #    marketData['candles'].append(candles)
            #    log.info(f'OBTENIDAS: {candles["count"]} velas de temporalidad {candles["temporality"]}')
                
                
            #takerFeeAsPercent = float(marketData["market"]["taker"]) * 100
            #minProfitAsPercent = takerFeeAsPercent * 3
            #metricData['minutesToMinimunProfit'] = 1000000000
            #if marketData["ticker"]['percentagePerMinute'] > 0:
            #    metricData['minutesToMinimunProfit'] = minProfitAsPercent / marketData["ticker"]['percentagePerMinute']
                
                
            marketData["isValidSpotMarket"] = self.is_valid_spot_market(marketData)
            log.info(f'MERCADO ACTIVO: {"SI" if marketData["isValidSpotMarket"] else "NO"}')

            return marketData
        return None


    
    def analyze_market(self, marketData:Dict, openInBrowser:bool=True, dataToJson:bool=True) -> bool:
        # Crea los directorios para guardar los datos.
        self.uniqueDateTimeLabel = self.create_unique_id()
        self.directoryData = f'{self.script_path()}/{DIRECTORY_DATA}'
        if not self.prepare_directory(self.directoryData):
            log.info(f'ERROR: No se pudo crear el directorio "{self.directoryData}"')
            return False
        self.directoryDateTime = f'{self.directoryData}/{DIRECTORY_DATETIME_PREFIX}_{self.uniqueDateTimeLabel}'
        if not self.prepare_directory(self.directoryDateTime):
            log.info(f'ERROR: No se pudo crear el directorio "{self.directoryDateTime}"')
            return False
        
        fileNameWeb = f'{self.directoryDateTime}/reporte.html'
        with open(fileNameWeb, 'a') as file:
            file.write(f'<html><head><title>{marketData["marketId"]}</title></head><body>\n')
            file.write(f'<b>Fecha y hora UTC: {self.datetimeUTC.strftime("%Y-%m-%d   %H:%M")}</b><br>\n')
            file.write(f'<b>Fecha y hora local: {self.datetimeLocal.strftime("%Y-%m-%d   %H:%M")}</b>\n')
            
            text = f'<b>REPORTE {marketData["marketId"]}</b>'
            text += f'\nUTC: {self.datetimeUTC.strftime("%Y-%m-%d   %H:%M")}'
            #text += f'\nFecha y hora local: {marketData["reportDatetimeLocal"]}'
            for chatId in self.config["telegramChatsId"]:
                send("text", self.config["telegramBotToken"], chatId, text)
            
            # Crea un analisis de las ultimas 24 horas mostrando la tendencia y desviacion.
            analysisCandles = AnalysisCandles(
                exchangeId= self.config["exchangeId"],
                marketId= f'{self.config["currencyBase"]}/{self.config["currencyQuote"]}',
                temporality= "5m", 
                count= 24 * 12, 
                temporalityLabel= "Ultimas 24 horas",
                telegramBotToken= self.config["telegramBotToken"], 
                telegramChatsId= self.config["telegramChatsId"], 
                directory= self.directoryDateTime,
                analysisLinear= False,
                analysisSMA= True,
                analysisVolumeProfile= False,
                styleDark= False,
                showLegend= True,
                showVolume= False,
                showVolumeProfile= False,
                showTrendCenter= True,
                showTrendDeviationsMeans= False,
                showTrendDeviationsExtremes= True,
                showVolumeProfilePeacks= False,
                showTakeProfit= True,
                showStopLoss= True,
                sound= self.config["sound"]
            )
            marketData = analysisCandles.do(marketData)
            file.write(marketData["analysisCandles"]["html"])            
            
            # Crea un analisis de los ultimos 7 dias mostrando la tendencia y desviacion.
            analysisCandles = AnalysisCandles(
                exchangeId= self.config["exchangeId"],
                marketId= f'{self.config["currencyBase"]}/{self.config["currencyQuote"]}',
                temporality= "1h", 
                count= 24 * 7, 
                temporalityLabel= "Ultimos 7 dias",
                telegramBotToken= self.config["telegramBotToken"], 
                telegramChatsId= self.config["telegramChatsId"], 
                directory= self.directoryDateTime,
                analysisLinear= True,
                analysisSMA= False,
                analysisVolumeProfile= True,
                styleDark= False,
                showLegend= True,
                showVolume= False,
                showVolumeProfile= True,
                showTrendCenter= True,
                showTrendDeviationsMeans= False,
                showTrendDeviationsExtremes= True,
                showVolumeProfilePeacks= False,
                showTakeProfit= True,
                showStopLoss= True,
                sound= self.config["sound"]
            )
            marketData = analysisCandles.do(marketData)
            file.write(marketData["analysisCandles"]["html"])            
            
            # Crea un analisis de los ultimos 90 dias mostrando las acumulaciones de volumen.
            analysisCandles = AnalysisCandles(
                exchangeId= self.config["exchangeId"],
                marketId= f'{self.config["currencyBase"]}/{self.config["currencyQuote"]}',
                temporality= "1h", 
                count= 24 * 30, 
                temporalityLabel= "Ultimos 90 dias",
                telegramBotToken= self.config["telegramBotToken"], 
                telegramChatsId= self.config["telegramChatsId"], 
                directory= self.directoryDateTime,
                analysisLinear= False,
                analysisSMA= False,
                analysisVolumeProfile= True,
                styleDark= False,
                showLegend= True,
                showVolume= False,
                showVolumeProfile= True,
                showTrendCenter= False,
                showTrendDeviationsMeans= False,
                showTrendDeviationsExtremes= False,
                showVolumeProfilePeacks= True,
                showTakeProfit= False,
                showStopLoss= False,
                sound= self.config["sound"]
            )
            marketData = analysisCandles.do(marketData)
            html = marketData["analysisCandles"]["html"]
            if html is not None:
                file.write(html)         
            
            file.write("</body></html>\n")
            if openInBrowser:
                webbrowser.open(os.path.abspath(fileNameWeb))
        
        # Guarda los datos de analisis en fichero JSON.
        if dataToJson:
            fileNameJson = f'{self.directoryDateTime}/datos_{self.uniqueDateTimeLabel}.json'
            Files.data_to_file_json(marketData, fileNameJson)        
        
        return True
        
    
    
    def is_valid_spot_market(self, marketData: MarketData) -> bool:
        '''
        Comprueba si el mercado está activo en el exchange y si es tipo spot.\n
        param marketData: Datos descriptivos del mercado obtenidos con CCXT.
        return: True si el mercado es válido. De lo contrario devuelve False.
        '''
        return marketData["market"]['active'] == True \
            and marketData["market"]['spot'] == True \
            and marketData["market"]['type'] == 'spot' \
            and marketData["market"]['active'] == True \
            and marketData["market"]['active'] == True


    
    """
    def delta_of_order_book(self, orderBook:Any, amountAsQuote:float, key:Literal["bids", "asks"]) -> float:
        sumVolumeAsQuote = 0
        for orderIndex in range(len(orderBook.get(key, []))):
            sumVolumeAsQuote += orderBook[key][orderIndex][0] * orderBook[key][orderIndex][1]
            if sumVolumeAsQuote >= amountAsQuote:
                return self.delta(orderBook[key][0][0], orderBook[key][orderIndex][0])
        return 100





    def _is_valid_market(
            self, 
            dataMarket: Optional[Market], 
            dataCurrencyBase: Optional[Currency], 
            dataCurrencyQuote: Optional[Currency]
        ) -> bool:
        '''
        Comprueba si el mercado está activo en el exchange y si es tipo spot.\n
        param marketData: Datos descriptivos del mercado obtenidos con CCXT.
        return: True si el mercado es válido. De lo contrario devuelve False.
        '''
        if dataMarket is not None and dataCurrencyBase is not None and dataCurrencyQuote is not None:
            return dataMarket['active'] != False and dataMarket['spot'] != False and dataMarket['type'] == 'spot' \
                and dataCurrencyBase['active'] != False and dataCurrencyQuote['active'] != False
        return False





    def check_market_limits(self, dataMarket:Market, amountAsBase:float, lastPrice:float) -> bool:
        '''
        Verifica si un valor esta dentro de los limites permitidos para el mercado especificado.\n
        param dataMarket: Datos del mercado obtenidos mediante la libreria CCXT.
        param amountAsBase: Valor expresado e currecy ase, que se debe verificar si esta dentro de los limites.
        return: Cadena vacia si el valor "amountAsBase" esta dentro de los limites permitidos. Mensaje de error si esta fuera de los limites.
        '''
        symbolId = dataMarket['symbol']
        base = Basics.base_of_symbol(symbolId)
        quote = Basics.quote_of_symbol(symbolId)
        decimals = 2 if quote.upper() == "USDT" else 12
        amountMin = self.get_market_limit("min", dataMarket)
        amountMax = self.get_market_limit("max", dataMarket)
        amountMinAsQuote = float(amountMin * lastPrice)
        amountMaxAsQuote = float(amountMax * lastPrice)
        if amountAsBase < amountMin:
            return f'Monto insuficiente. El minimo es {amountMin} ({round(amountMinAsQuote, decimals)} {quote})'
        elif amountAsBase > amountMax:
            return f'Monto excedido. El maximo es {amountMax} ({round(amountMaxAsQuote, decimals)} {quote})'
        else:
            return ""





    def sma(self, values, length:int=10):
        result = {
            "lineMean": []
        }
        result = []
        for indexEnd in range(len(values)):
            indexBegin = 0 if indexEnd < length else indexEnd - length
            result["lineMean"].append(mean(values[indexBegin:indexEnd]) if indexEnd >= 1 else values[0])
        return result





    def bolinger_bands(self, values, lengthSMA:int=10, lengthDev:int=10):
        result = {
            "lineMean": [],
            "deviationStandard": [],
            "lineDeviationUpAverage": [],
            "lineDeviationDownAverage": []
        }
        for indexEnd in range(len(values)):
            indexBeginSMA = 0 if indexEnd < lengthSMA else indexEnd - lengthSMA
            indexBeginDev = 0 if indexEnd < lengthDev else indexEnd - lengthDev
            result["lineMean"].append(mean(values[indexBeginSMA:indexEnd]) if indexEnd >= 1 else values[0])
            result["deviationStandard"].append(stdev(values[indexBeginDev:indexEnd]) if indexEnd >= 2 else 0)
            result["lineDeviationUpAverage"].append(result["lineMean"][-1] + (result["deviationStandard"][-1]) * 2)
            result["lineDeviationDownAverage"].append(result["lineMean"][-1] - (result["deviationStandard"][-1]) * 2)            
        return result
                




    def linear_bands(self, values:List[float]):
        result = {
            "lineMean": [],
            "lineDeviationUpMax": [],
            "lineDeviationUpAverage": [],
            "lineDeviationDownAverage": [],
            "lineDeviationDownMin": []
        }
        result['lineMean'] = self._create_trend_line(values[0], values[-1], len(values))
        deviations = [(values[index] - result["lineMean"][index]) for index in range(len(values))] 
        upperDeviations = list(filter(lambda value: value > 0, deviations))
        lowerDeviations = list(filter(lambda value: value < 0, deviations))
        
        deltaUpperMax = max(upperDeviations) if len(upperDeviations) >= 1 else 0
        deltaUpperAverage = mean(upperDeviations) if len(upperDeviations) >= 1 else 0
        deltaLowerAverage = mean(lowerDeviations) if len(lowerDeviations) >= 1 else 0
        deltaLowerMin = min(lowerDeviations) if len(lowerDeviations) >= 1 else 0
        
        result['lineDeviationUpMax'] = self._create_trend_line(values[0] + deltaUpperMax, values[-1] + deltaUpperMax, len(values))
        result['lineDeviationUpAverage'] = self._create_trend_line(values[0] + deltaUpperAverage, values[-1] + deltaUpperAverage, len(values))
        result['lineDeviationDownAverage'] = self._create_trend_line(values[0] + deltaLowerAverage, values[-1] + deltaLowerAverage, len(values))
        result['lineDeviationDownMin'] = self._create_trend_line(values[0] + deltaLowerMin, values[-1] + deltaLowerMin, len(values))
        return result

            



    def asimetric_bands(
            self, 
            values:List[float], 
            typeBand:Literal["mean", "extreme"], 
            percentOfLength:float=33,
            percentOfDeviation:int=100
        ):
        result = {
            "sma": [],
            "dev": [],
            "devUp": [],
            "devDown": [],
            "bandUp": [],
            "bandDown": []
        }
        lengthDev = round(len(values) * (percentOfLength / 100))
        result['sma'] = self._create_trend_line(values[0], values[-1], len(values))
        for indexEnd in range(len(values)):
            indexBeginDev = 0 if indexEnd < lengthDev else indexEnd - lengthDev
            result["dev"].append(values[indexEnd] - result["sma"][indexEnd])  
            fragmentDev = result["dev"][indexBeginDev:indexEnd]
            upperDeviations = list(filter(lambda value: value > 0, fragmentDev))
            lowerDeviations = list(filter(lambda value: value < 0, fragmentDev))
            if typeBand == "mean":
                result["devUp"].append(mean(upperDeviations) if len(upperDeviations) >= 1 else 0)
                result["devDown"].append(mean(lowerDeviations) if len(lowerDeviations) >= 1 else 0)
            elif typeBand == "extreme":
                result["devUp"].append(max(upperDeviations) if len(upperDeviations) >= 1 else 0)
                result["devDown"].append(min(lowerDeviations) if len(lowerDeviations) >= 1 else 0)
            deltaFactor = 2 * (percentOfDeviation / 100)
            result["bandUp"].append(result["sma"][indexEnd] + (result["devUp"][indexEnd]) * deltaFactor)  
            result["bandDown"].append(result["sma"][indexEnd] + (result["devDown"][indexEnd]) * deltaFactor) 
        return result

    """
        