"""
Este script se encarga de realizar el analisis de las velas del mercado y su 
volumen, detectando niveles, soportes, resistencias, tendencias, desviaciones. 
Es el primer script de analisis que se implemento para el sistema de reportes.

Paleta de colores de la web: https://colorswall.com/es/palette/268193
"""


from basics import *
from exchange import *
import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots  # type: ignore
import google.generativeai as ai
import pyttsx3
from telegram_sender import *

Formats = Literal["png", "jpg", "jpeg", "webp", "svg", "pdf"]


class AnalysisCandles(Basics):
    
    def __init__(self, exchangeId:str, marketId:MarketId, temporality:str, count:int, temporalityLabel:str, 
                 telegramBotToken:str, telegramChatsId:List[str], directory:str, 
                 analysisLinear:bool=True,
                 analysisSMA:bool=True,
                 analysisVolumeProfile:bool=True,
                 styleDark:bool=True,
                 showLegend:bool=True,
                 showVolume:bool=True,
                 showVolumeProfile:bool=True,
                 showTrendCenter:bool=True,
                 showTrendDeviationsExtremes:bool=True,
                 showTrendDeviationsMeans:bool=True,
                 showVolumeProfilePeacks:bool=True,
                 showTrendSMA:bool=True,
                 showPriceSMA:bool=True,
                 showTakeProfit:bool=True,
                 showStopLoss:bool=True,
                 sound:bool=True
                 ):
        self.exchangeId = exchangeId
        self.marketId = marketId
        self.temporality = temporality
        self.count = count
        self.temporalityLabel = temporalityLabel
        self.telegramBotToken = telegramBotToken
        self.telegramChatsId = telegramChatsId
        self.directory = directory
        self.analysisLinear = analysisLinear
        self.analysisSMA = analysisSMA
        self.analysisVolumeProfile = analysisVolumeProfile
        self.styleDark = styleDark
        self.showLegend = showLegend
        self.showVolume = showVolume
        self.showVolumeProfile = showVolumeProfile
        self.showTrendCenter = showTrendCenter
        self.showTrendDeviationsExtremes = showTrendDeviationsExtremes
        self.showTrendDeviationsMeans = showTrendDeviationsMeans
        self.showVolumeProfilePeacks = showVolumeProfilePeacks
        self.showTrendSMA = showTrendSMA
        self.showPriceSMA = showPriceSMA
        self.showTakeProfit = showTakeProfit
        self.showStopLoss = showStopLoss        
        self.sound = sound
        
        self.baseId = self.base_of_symbol(self.marketId)
        self.quoteId = self.quote_of_symbol(self.marketId)
        self.marketData = None



    def do(self, marketData:MarketData=None, toTelegram:bool=True):
        self.marketData = marketData
        self.uniqueDateTimeLabel = self.create_unique_id()
        if self.marketData is not None:
            self.marketData["analysisCandles"] = {}
            self.marketData["analysisCandles"]["data"] = self._get_data()
            self.marketData["analysisCandles"]["analyse"] = self._analyse()
            self.marketData["analysisCandles"]["graph"] = self._create_graph()
            self.marketData["analysisCandles"]["text"] = self._create_text()
            self.marketData["analysisCandles"]["audio"] = self._create_audio()
            self.marketData["analysisCandles"]["html"] = self._create_for_html()
            self.marketData["analysisCandles"]["chat"] = self._create_for_chat()
            if toTelegram:
                self.send_to_telegram(self.telegramBotToken, self.telegramChatsId)
        else:
            log.info("ERROR: Faltan los datos de mercado para iniciar el analisis de las velas.")
        return self.marketData



    def send_to_telegram(self, botToken:str, chatsId:List[str]):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["text"] is not None:
                if self.marketData["analysisCandles"]["graph"] is not None:
                    for chatId in self.telegramChatsId:
                        filenameGraph = self.marketData["analysisCandles"]["graph"]["pathFileName"]
                        send("photo", botToken, chatId, f"Analisis de {self.marketId}  {self.temporalityLabel}", filenameGraph)
                    for chatId in self.telegramChatsId:
                        filenameAudio = self.marketData["analysisCandles"]["audio"]["pathFileName"]
                        send("audio", botToken, chatId, "", filenameAudio)
                    for chatId in self.telegramChatsId:
                        send("text", botToken, chatId, self.marketData["analysisCandles"]["text"]["text"])
                    #for chatId in self.telegramChatsId[0]:
                    #    send("text", botToken, chatId, "samtiago")
                    return True 
        return False



    ###############################################################################################
    ####   Optener los datos   ####################################################################
    ###############################################################################################

    def _get_data(self):
        if self.marketData is not None:
            exchange = Exchange(self.exchangeId, "", "")
            data = {
                "exchangeId": self.exchangeId,
                "marketId": self.marketId,
                "temporality": self.temporality,
                "count": self.count,
                "candles": exchange.get_last_candles(self.marketId, self.count, self.temporality)
            }
            if data["candles"] is not None:
                for i in range(len(data["candles"])):
                    data["candles"][i].append(exchange.exchange.iso8601(data["candles"][i][0]))
                #candles["datetimes"] = [exchange.exchange.iso8601(x[0]) for x in candles["data"]]
                log.info(f'OBTENIDAS: {self.count} velas de temporalidad {self.temporality}')
                return data 
        return None



    ###############################################################################################
    ####   Aalisis de los datos  ##################################################################
    ###############################################################################################
    
    def _analyse(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["data"] is not None:
                analyse = {}
                analyse['metrics'] = self.metrics(self.marketData)
                analyse["closeConditions"] = self.close_conditions(self.marketData)
                return analyse 
        return None



    def metrics(self, marketData:MarketData) -> Metrics:
        candles = marketData["analysisCandles"]["data"]["candles"]
        metricData: Metrics = {}
        metricData["count"] = len(candles)
        metricData["open"] = candles[0][CANDLE_OPEN]
        metricData["low"] = min([candle[CANDLE_LOW] for candle in candles])
        metricData["higt"] = max([candle[CANDLE_HIGT] for candle in candles])
        metricData["close"] = candles[-1][CANDLE_CLOSE]
        metricData['deltaPercent'] = self.delta(candles[0][CANDLE_OPEN], candles[-1][CANDLE_CLOSE])                     
        metricData['trendLine'] = self._create_trend_line(candles[0][CANDLE_OPEN], candles[-1][CANDLE_CLOSE], len(candles))
        if self.analysisLinear:
            metricData["linearBands"] = self.linear_bands(
                [self.candle_resume(x, "mean") for x in candles],
                round(len(candles) * 0.25), round(len(candles) * 0.25)
            )
        if self.analysisSMA:
            metricData["analysisSma"] = self.analysis_sma([x[CANDLE_CLOSE] for x in candles], 25, 200)
        if self.analysisVolumeProfile:
            metricData["volumeProfile"] = self.volume_profile(marketData)
        hours = (self.temporality_as_minutes(self.temporality) * self.count) / 60
        metricData["profitPercentPerHours"] = metricData['deltaPercent'] / hours
        metricData["hoursToProfit1Percent"] = 1 / metricData["profitPercentPerHours"]
        return metricData    



    def linear_bands(self, values:List[float], beginMeanLength:int=1, endMeanLength:int=1):
        result = {
            "lineMean": [],
            "lineDeviationUpMax": [],
            "lineDeviationUpAverage": [],
            "lineDeviationDownAverage": [],
            "lineDeviationDownMin": []
        }
        priceBegin = mean(values[0:beginMeanLength])
        priceEnd = mean(values[len(values) - endMeanLength:])
        result['lineMean'] = self._create_trend_line(priceBegin, priceEnd, len(values))
        deviations = [(values[index] - result["lineMean"][index]) for index in range(len(values))] 
        deviationsAbsolutes = [abs(value) for value in deviations]
        upperDeviations = list(filter(lambda value: value > 0, deviations))
        lowerDeviations = list(filter(lambda value: value < 0, deviations))
        
        result["deltaUpperMax"] = max(upperDeviations) if len(upperDeviations) >= 1 else 0
        result["deltaAverage"] = mean(deviationsAbsolutes) if len(deviationsAbsolutes) >= 1 else 0
        result["deltaUpperAverage"] = mean(upperDeviations) if len(upperDeviations) >= 1 else 0
        result["deltaLowerAverage"] = mean(lowerDeviations) if len(lowerDeviations) >= 1 else 0
        result["deltaLowerMin"] = min(lowerDeviations) if len(lowerDeviations) >= 1 else 0
        
        result['lineDeviationUpMax'] = self._create_trend_line(
            priceBegin + result["deltaUpperMax"], priceEnd + result["deltaUpperMax"], len(values))
        result['lineDeviationUpAverage'] = self._create_trend_line(
            priceBegin + result["deltaUpperAverage"], priceEnd + result["deltaUpperAverage"], len(values))
        result['lineDeviationDownAverage'] = self._create_trend_line(
            priceBegin + result["deltaLowerAverage"], priceEnd + result["deltaLowerAverage"], len(values))
        result['lineDeviationDownMin'] = self._create_trend_line(
            priceBegin + result["deltaLowerMin"], priceEnd + result["deltaLowerMin"], len(values))
        return result

            

    def analysis_sma(self, values:List[float], priceSmaLength, trendSmaLength):
        result = {
            "priceSma": [],
            "trendSma": []
        }
        for indexEnd in range(len(values)):
            dataSmaPrice = values[0:indexEnd] if indexEnd < priceSmaLength else values[indexEnd - priceSmaLength:indexEnd]
            result["priceSma"].append(mean(dataSmaPrice) if len(dataSmaPrice) > 0 else values[indexEnd])
            dataSmaTrend = values[0:indexEnd] if indexEnd < trendSmaLength else values[indexEnd - trendSmaLength:indexEnd]
            result["trendSma"].append(mean(dataSmaTrend) if len(dataSmaTrend) > 0 else values[indexEnd])
        return result



    def volume_profile(self, marketData:Dict, resolution:int=50, peaksMinSizePercent:float=75, peaksMinSeparationSizePercent:float=7):
        candles = marketData["analysisCandles"]["data"]["candles"]
        result = {}
        
        def detect_peaks(i, j):
            if i >= 0 and j <= len(result["volumes"]) and i < j:
                maximun = max(result["volumes"][i:j])
                peakPosition = result["volumes"].index(maximun)
                if (maximun - result["volumeMin"]) / result["volumeRange"] * 100 > peaksMinSizePercent:
                    result["peaks"].append(result["prices"][peakPosition])
                    separation = round(resolution * (peaksMinSeparationSizePercent / 100)) + 1
                    detect_peaks(i, peakPosition - separation)
                    detect_peaks(peakPosition + separation, j)
        
        priceMax = max([self.candle_resume(x, "mean") for x in candles])
        priceMin = min([self.candle_resume(x, "mean") for x in candles])
        result["priceRange"] = priceMax - priceMin
        result["priceStep"] = result["priceRange"] / resolution
        result["prices"] = [priceMin + (result["priceStep"] * x) + (result["priceStep"] / 2) for x in range(resolution)]
        result["volumes"] = [0 for x in range(resolution)] 
        for candle in candles:
            index = round(((self.candle_resume(candle, "mean") - priceMin) / result["priceRange"]) * (resolution - 1))
            result["volumes"][index] += candle[CANDLE_VOLUME]
            
        result["volumeMax"] = max(result["volumes"])
        result["volumeMin"] = min(result["volumes"])
        result["volumeRange"] = result["volumeMax"] - result["volumeMin"]
        result["peaks"] = []
        detect_peaks(0, len(result["volumes"]))
        return result



    def _linear_interpolation(self, X: int, X0: int, Y0: float, X1: int, Y1: float) -> float:
        '''
        Devuelve la interpolacion lineal de Y para un valor de X dado.
        param X: Valor del eje X para el que se debe calcular la Y mediante interpolacion lineal.
        param X0: Valor en el eje X del punto 0 donde inicia el segmento.
        param Y0: Valor en el eje Y del punto 0 donde inicia el segmento.
        param X1: Valor en el eje X del punto 1 donde termina el segmento.
        param Y1: Valor en el eje Y del punto 1 donde termina el segmento.
        return: Interpolacion lineal de Y para un valor de X dado.
        '''
        return float(((Y1 - Y0) / (X1 - X0)) * (X - X0) + Y0)



    def _create_trend_line(self, priceBegin: float, priceEnd: float, count: int) -> List[float]:
        '''
        Devuelve una linea de precios que van desde el precio inicial hasta el final.
        param priceBegin: Precio inicial desde donde se calcula la interpolacion.
        param priceEnd: Precio final hasta donde se calcula la interpolacion.
        param count: Cantidad de valores Y que deben componer a la linea de precios.
        return: Lista de precios que representa una linea que va desde el precio inicial hasta el final. 
                Si ocurre un error, devuelve lista vacia.
        '''
        try:
            if count == 0:
                return []
            elif count == 1:
                return [priceBegin]
            elif count == 2:
                return [priceBegin, priceEnd]
            return [self._linear_interpolation(index, 0, priceBegin, count-1, priceEnd) for index in range(count)]
        except Exception as e:
            return []



    def candles_trend_deviation(self, candles:ListOfCandles, trendLine:List[float]) -> Optional[Dict]:
        '''
        Devuelve los datos de la desviacion de las velas con respecto a una linea.
        param candles: Lista de velas obtenidas del exchange, mediante la librería ccxt.
        param trendLine: Lista de precios que representa una linea que va desde el precio inicial hasta el final.
        return: Devuelve un objeto con los datos de la desviacion de las velas con respecto a "trendLine".
                Una parte del resultado contiene los valores absolutos de desviacion.
                La otra parte contiene los valores de desviacion expresados en porciento con respecto a la tendencia.
                Si hay menos de 5 velas, devuelve None por unsuficiencia de datos.
                Si ocurre un error, devuelve None.
        '''
        if len(candles) < 5:
            return None
        
        # Valores absolutos de desviacion
        deviations = list(float(candles[index][CANDLE_CLOSE]) - float(trendLine[index]) for index in range(len(candles)))
        upperDeviation = list(filter(lambda deviation: deviation > 0, deviations))
        lowerDeviation = list(filter(lambda deviation: deviation < 0, deviations))
        absolute = list(abs(deviation) for deviation in deviations)
        
        # Valores de desviacion expresados en porciento con respecto a la linea de tendencia.
        deviationsAsPercent = list(float(self.delta(float(trendLine[index]), candles[index][CANDLE_CLOSE])) for index in range(len(candles)))
        upperDeviationAsPercent = list(filter(lambda deviation: deviation > 0, deviationsAsPercent))
        lowerDeviationAsPercent = list(filter(lambda deviation: deviation < 0, deviationsAsPercent))
        absoluteAsPercent = list(abs(deviation) for deviation in deviationsAsPercent)
        result = {}
        result["percent"] = {
            "max": max(absoluteAsPercent),
            "average": sum(absoluteAsPercent) / len(absoluteAsPercent),
            "upperMax": max(upperDeviationAsPercent) if len(upperDeviationAsPercent) > 0 else 0,
            "upperAverage": sum(upperDeviationAsPercent) / len(upperDeviationAsPercent) if len(upperDeviationAsPercent) > 0 else 0,
            "lowerMin": min(lowerDeviationAsPercent) if len(lowerDeviationAsPercent) > 0 else 0,
            "lowerAverage": sum(lowerDeviationAsPercent) / len(lowerDeviationAsPercent) if len(lowerDeviationAsPercent) > 0 else 0
        }
        result["absolute"] = {
            "max": max(absolute),
            "average": sum(absolute) / len(absolute),
            "upperMax": max(upperDeviation) if len(upperDeviation) > 0 else 0,
            "upperAverage": sum(upperDeviation) / len(upperDeviation) if len(upperDeviation) > 0 else 0,
            "lowerMin": min(lowerDeviation) if len(lowerDeviation) > 0 else 0,
            "lowerAverage": sum(lowerDeviation) / len(lowerDeviation) if len(lowerDeviation) > 0 else 0
        }
        return result



    def close_conditions(self, marketData:MarketData) -> CloseConditions:
        '''
        Devuelve un objeto con las condiciones de cierre de la inversion.\n
        param ticker: Ultimo ticker del mercado, obtenido del exchange, mediante la librería ccxt.
        return: Objeto con las condiciones de cierre de la inversion. None si el mercado no esta creciendo.
        ''' 
        #self.marketData["analysisCandles"]["data"]["candles"], 
        #analyse['metrics'], 
        #self.marketData
        
        #candlesLenghtAsMinutes = self.temporality_as_minutes(candlesData["temporality"]) * candlesData["count"]
        #deltaPercentPerMinute = candlesData["metrics"]['deltaPercent'] / candlesLenghtAsMinutes
        if False:  #deltaPercentPerMinute > 0:
            takeProfitPercent = candlesData["metrics"]["linearBands"]["lineDeviationUpAverage"]
            stopLossPercent = candlesData["metrics"]["linearBands"]["lineDeviationDownAverage"]    
            minutesToTakeProfit = abs(takeProfitPercent) / deltaPercentPerMinute   
            lastPrice = candlesData["metrics"]["close"]
            takeProfitPrice = lastPrice * (1 + (abs(takeProfitPercent) / 100))
            stopLossPrice = lastPrice * (1 - (abs(stopLossPercent) / 100))
            closeConditions: CloseConditions = {
                "takeProfitPercent": abs(takeProfitPercent),
                "stopLossPercent": abs(stopLossPercent) * -1,
                "takeProfitPrice": takeProfitPrice,
                "stopLossPrice": stopLossPrice,
                "minutesToTakeProfit": minutesToTakeProfit 
            }
            return closeConditions
        else:
            return None



    ###############################################################################################
    ####   Crear el grafico del analisis   ########################################################
    ###############################################################################################
    
    def _create_graph(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["analyse"] is not None:
                count = self.marketData["analysisCandles"]["data"]["count"]
                temporality = self.marketData["analysisCandles"]["data"]["temporality"]
                graphUniqueLabel = f'velas_{count}_temporalidad_{temporality}'
                fileNameGraph = f'{graphUniqueLabel}_{self.uniqueDateTimeLabel}.png'    
                pathFileNameGraph  = f'{self.directory}/{fileNameGraph}'
                titleGraph = 'exchange: {}   market:{}  temporalidad: {}  longitud: {} ({})'.format(
                    self.marketData["analysisCandles"]["data"]["exchangeId"],
                    self.marketData["analysisCandles"]["data"]["marketId"],
                    self.marketData["analysisCandles"]["data"]["temporality"],
                    self.marketData["analysisCandles"]["data"]["count"],
                    self.temporalityLabel
                )
                self.create_graph(self.marketData["analysisCandles"], titleGraph, pathFileNameGraph, False)  
                return {
                    "fileName": fileNameGraph,
                    "pathFileName": pathFileNameGraph
                }
        return None



    def create_graph(self, analysisCandles: Dict, title:str, fileName:str, show:bool=False):
        '''
        Crea un grafico de velas del analisis para guardarlo en un fichero.
        param candleData: Contiene las velas del mercado.
        param title: Titulo que se muestra en el grafico
        param fileName: Nombre del fichero donde se guarda el grafico. Si es cadena vacia, no guarda en fichero.
        param show: True para que se muestre el grafico en el navegador. False para que no se muestre el grafico.
        return: False si ocurre un error. True si se ejecuta correctamente.
        '''
        COLOR_CANDLE_INC = '#25543F' if self.styleDark else '#25943F'
        COLOR_CANDLE_DEC = '#872722' if self.styleDark else '#C72722'
        COLOR_AXES_LINE = '#252525'
        COLOR_AXES_GRID = '#202020'
        if fileName == "" and show == False:
            return True

        candles = analysisCandles["data"]["candles"]
        open = [x[CANDLE_OPEN] for x in candles]
        high = [x[CANDLE_HIGT] for x in candles]
        low = [x[CANDLE_LOW] for x in candles]
        close = [x[CANDLE_CLOSE] for x in candles]
        dt = [x[6] for x in candles]
        metrics = analysisCandles["analyse"]["metrics"]
                
        rowWidth = [0.2, 0.7] if self.showVolume else [0, 1]
        colWidth = [0.85, 0.15] if self.showVolumeProfile else [1, 0]
        fig = make_subplots(
            rows=2, cols=2, shared_xaxes=True, shared_yaxes=True, 
            row_width=rowWidth, column_widths=colWidth, 
            vertical_spacing=0, horizontal_spacing=0
        )
        fig.add_trace(go.Candlestick(x=dt, open=open, high=high, low=low, close=close, name="Velas"), row=1, col=1)  
        fig.data[0].increasing.fillcolor = COLOR_CANDLE_INC
        fig.data[0].increasing.line.color = COLOR_CANDLE_INC
        fig.data[0].decreasing.fillcolor = COLOR_CANDLE_DEC
        fig.data[0].decreasing.line.color = COLOR_CANDLE_DEC

        if "linearBands" in metrics:
            mean = metrics["linearBands"]["lineMean"]
            lineDeviationUpMax = metrics["linearBands"]["lineDeviationUpMax"]
            lineDeviationUpAverage = metrics["linearBands"]["lineDeviationUpAverage"]
            lineDeviationDownAverage = metrics["linearBands"]["lineDeviationDownAverage"]
            lineDeviationDownMin = metrics["linearBands"]["lineDeviationDownMin"]
            if self.showTrendCenter:
                fig.add_trace(go.Scatter(mode="lines", x=dt, y=mean, line=dict(color='orange', width=2), name="Tendencia central"), row=1, col=1)    
            if self.showTrendDeviationsExtremes:
                fig.add_trace(go.Scatter(mode="lines", x=dt, y=lineDeviationUpMax, line=dict(color='#006000', width=1), name="Desviación Máxima"), row=1, col=1)    
                fig.add_trace(go.Scatter(mode="lines", x=dt, y=lineDeviationDownMin, line=dict(color='#600000', width=1), name="Desviación Mínima"), row=1, col=1)    
            if self.showTrendDeviationsMeans:
                fig.add_trace(go.Scatter(mode="lines", x=dt, y=lineDeviationUpAverage, line=dict(color='#00A000', width=1), name="Desviación Superior Media"), row=1, col=1)    
                fig.add_trace(go.Scatter(mode="lines", x=dt, y=lineDeviationDownAverage, line=dict(color='#A00000', width=1), name="Deviation Inferior Media"), row=1, col=1)    

        if "analysisSma" in metrics:
            smaPrice = metrics["analysisSma"]["priceSma"]
            smaTrend = metrics["analysisSma"]["trendSma"]
            if self.showTrendSMA:
                fig.add_trace(go.Scatter(x=dt, y=smaTrend, line_color='blue', name="Media del precio"), row=1, col=1) 
            if self.showPriceSMA:
                fig.add_trace(go.Scatter(x=dt, y=smaPrice, line_color='orange', name="Media del precio"), row=1, col=1) 

        if self.showVolume:
            volumeGreen = [(x[CANDLE_VOLUME] if x[CANDLE_CLOSE] >= x[CANDLE_OPEN] else 0) for x in candles]
            volumeRed = [(x[CANDLE_VOLUME] if x[CANDLE_CLOSE] < x[CANDLE_OPEN] else 0) for x in candles]
            fig.add_trace(go.Bar(x=dt, y=volumeGreen, showlegend=True, marker_color=COLOR_CANDLE_INC, marker_line_width=0, name="Volumen de vela creciente"), row=2, col=1) 
            fig.add_trace(go.Bar(x=dt, y=volumeRed, showlegend=True, marker_color=COLOR_CANDLE_DEC, marker_line_width=0, name="Volumen de vela decreciente"), row=2, col=1) 

        if "volumeProfile" in metrics and self.showVolumeProfile:
            fig.add_trace(go.Scatter(
                x=metrics["volumeProfile"]["volumes"], 
                y=metrics["volumeProfile"]["prices"], 
                showlegend=True, orientation="h",
                line_color='#120d5b',
                fillcolor='#120d5b', opacity=0.1,
                fill='tozerox',
                name="Perfil de volúmen"
            ), row=1, col=2) 
            if self.showVolumeProfilePeacks:
                for peak in metrics["volumeProfile"]["peaks"]:
                    fig.add_shape(
                        type='line', x0=dt[0], y0=peak, x1=dt[-1], y1=peak, opacity=0.7,
                        line=dict(color='#2422ba', width=2), xref='x', yref='y', row=1, col=1
                    )
                   
        fig.update_layout(xaxis_rangeslider_visible=False)
        fig.update_layout(title_text=title, title_x=0.5)
        fig.update_layout(legend=dict(orientation="h"))
        fig.update_layout(showlegend=self.showLegend)
        fig.update_xaxes(showticklabels=False, row=1, col=2)
        fig.update_xaxes(autorange="reversed", row=1, col=2)
        if self.styleDark:
            fig.update_layout(plot_bgcolor="#0E0E0E", paper_bgcolor="#000000")
            fig.update_layout(font=dict(color="#FFFFFF")) 
            fig.update_xaxes(showline=True, linewidth=1, linecolor=COLOR_AXES_LINE, gridcolor=COLOR_AXES_GRID, zerolinecolor=COLOR_AXES_LINE)
            fig.update_yaxes(showline=True, linewidth=1, linecolor=COLOR_AXES_LINE, gridcolor=COLOR_AXES_GRID, zerolinecolor=COLOR_AXES_LINE)
        
        # Muestra las metricas lineales
        if False:  #candleData["metrics"] is not None:
            if candleData["closeConditions"] is not None:
                markWidth = int(round(len(dt) * 0.05)) 
                takeProfitPrice = candleData["closeConditions"]["takeProfitPrice"]
                stopLossPrice = candleData["closeConditions"]["stopLossPrice"]
                fig.add_shape(
                    type='line', x0=dt[-markWidth], y0=takeProfitPrice, x1=dt[-1], y1=takeProfitPrice, 
                    line=dict(color='green', width=3), xref='x', yref='y'
                )
                fig.add_shape(
                    type='line', x0=dt[-markWidth], y0=stopLossPrice, x1=dt[-1], y1=stopLossPrice,
                    line=dict(color='red', width=3), xref='x', yref='y'
                )
                xp = dt[-(markWidth*1)]
                fig.add_trace(go.Scatter(
                    x=[xp, xp], y=[takeProfitPrice, stopLossPrice], 
                    text=["Take Profit Level", "Stop Loss Level"], mode="text", 
                    textposition="middle left", textfont=dict(color=["green", "red"], family="sans serif", size=18)
                    ))
                
            lineStyleTrend = dict(color='orange', width=2)
            fig.add_shape(
                type='line', x0=dt[0], y0=close[0], x1=dt[-1], y1=close[-1], 
                line=lineStyleTrend, xref='x', yref='y'
            )
        if fileName != "": 
            fig.write_image(fileName, format="png", scale=5, width=1200)  #, width=1200, height=1000
        if show:
            fig.show()
        return True



    ###############################################################################################
    ####   Creando el texto explicativo del analisis de los datos   ###############################
    ###############################################################################################
    
    def _create_text(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["analyse"] is not None:
                quoteId = ""
                precisionPrice = 10
                if self.marketData['market'] is not None:
                    quoteId = self.marketData['quoteId']
                    precisionPrice = self.marketData['market']["precision"]["price"]

                analyse = self.marketData["analysisCandles"]["analyse"]
                metrics = self.marketData["analysisCandles"]["analyse"]["metrics"]   
                #linearBands = metrics["linearBands"]
                
                #query += self.kjagjk("exchange", self.marketData["exchangeId"])
                horas = (self.temporality_as_minutes(self.temporality) * self.count) / 60
                params = ""
                params += f"Se analizó el mercado {self.baseId} contra {self.quoteId} y se graficaron {self.count} velas de temporalidad {self.temporality_as_text(self.temporality)}, que abarcan las últimas {round(horas, 2)} horas. "
                if metrics["deltaPercent"] > 0:
                    params += f'\n\nLa linea de tendencia central del grafico muestra un crecimiento de {self.round_str(metrics["deltaPercent"], 2)} %. '
                    params += f'El mercado esta creciendo a una velocidad aproximada de {self.round_str(metrics["profitPercentPerHours"], 2)} % por hora. '
                    params += f'A esa velocidad de crecimiento, se necesitarian {self.round_str(metrics["hoursToProfit1Percent"], 2)} horas para alcazar una ganancia de 1%. '
                else:
                    params += f'\n\nLa linea de tendencia central del gráfico muestra un decrecimiento de menos {self.round_str(abs(metrics["deltaPercent"]), 2)} %. '
                    params += f'El precio del activo esta cayendo a una velocidad aproximada de {self.round_str(abs(metrics["profitPercentPerHours"]), 2)} % por hora. '
                    params += f'A esa velocidad de caida, se necesitarian {self.round_str(abs(metrics["hoursToProfit1Percent"]), 2)} horas para perder 1% del valor. '
                
                #params += f"El precio ha podido desla desviacion media con respecto a la linea de tendencia es de +/-", 
                #    self.delta(metrics["close"], metrics["close"] + linearBands["deltaAverage"]), 2, "%")
                #params += self.text_param("la desviacion maxima por encima de la linea de tendencia es de", 
                #    self.delta(metrics["close"], metrics["close"] + linearBands["deltaUpperMax"]), 2, "%")
                #params += self.text_param("la desviacion minima por debajo de la linea de tendencia es de", 
                #    self.delta(metrics["close"], metrics["close"] - linearBands["deltaLowerMin"]), 2, "%")
                
                #params += self.text_param("precio inicial del grafico es", metrics["open"], precisionPrice, quoteId)
                #params += self.text_param("precio maximo alcanzado en el grafico", metrics["higt"], precisionPrice, quoteId)
                #params += self.text_param("precio minimo alcanzado en el grafico", metrics["low"], precisionPrice, quoteId)
                #params += self.text_param("el ultimo precio del grafico es", metrics["close"], precisionPrice, quoteId)
                
                #****** Estos datos comentados, puedem emplearse para calcular la volatilidad del precio y
                # saber si el mercado es propicio para la inversio, o solo el trading...
                
                # Se puede tamviem comtavilizar los cruces por la media y determimr asi el potemcial de tradimg.
                # 

                if "volumeProfile" in metrics:
                    if metrics["volumeProfile"] is not None: 
                        if len(metrics["volumeProfile"]["peaks"]) == 1:
                            for peaks in metrics["volumeProfile"]["peaks"]:
                                params += f'\n\nSe detectó un nivel significativo de volumen cercano al precio {self.round_str(peaks, precisionPrice)} {quoteId} al cual se le debe prestar atencion, porque puede actuar como '
                                if metrics["close"] * 1.01 > peaks:
                                    params += "soporte del precio, acompañado de compras masivas cercanas ese nivel."
                                elif metrics["close"] * 0.99 < peaks:
                                    params += 'resistencia al crecimiento del precio, acompañado de multiples ventas y tomas de ganancias que podrian hacer caer el precio rapidamente. '
                                else:
                                    params += 'soporte o resistencia en dependencia de la evolución próxima del mercado de manera que: Si el precio cae significativamente por debajo de ese nivel, es posible que el nivel termine covirtiéndose en una resistencia o, si el precio sube es posible que el nivel termine estableciéndose como soporte del precio. '
                        elif len(metrics["volumeProfile"]["peaks"]) > 1:
                            params += f'\n\nSe detectaron {len(metrics["volumeProfile"]["peaks"])} niveles significativos de volumen cercanos a los siguientes precios: '
                            for peaks in metrics["volumeProfile"]["peaks"]:
                                params += f"{self.round_str(peaks, precisionPrice)} {quoteId}, "
                            params += 'Se debe atender a la evolución del mercado teniendo en cuenta que en cada uno de estos niveles de precio se pueden producir múltiples operaciones compra y venta, haciendo que el nivel actue como soporte o resistencia en dependencia de si el precio esta por encima o por debajo. '

                return {"text": params}
        return None



    def text_param(self, lavel:str, value:Union[int, float, str], decimals:Optional[int]=None, unit:str=""):
        separator = " "
        if type(value) == str or value is None:
            return f"{lavel}{separator}{value} {unit}\n"
        else:
            if decimals is not None:
                return f"{lavel}{separator}{str(self.round_str(value, decimals))} {unit}\n"
            else:
                return f"{lavel}{separator}{str(self.as_str(value))} {unit}\n"



    ###############################################################################################
    ####   Creando el audio explicativo del analisisde los datos   ################################
    ###############################################################################################
    
    def _create_audio(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["text"] is not None:
                text = self.marketData["analysisCandles"]["text"]["text"]
                count = self.marketData["analysisCandles"]["data"]["count"]
                temporality = self.marketData["analysisCandles"]["data"]["temporality"]
                audioUniqueLabel = f'velas_{count}_temporalidad_{temporality}'
                fileNameAudio = f'{audioUniqueLabel}_{self.uniqueDateTimeLabel}.mp3'       
                pathFileNameAudio = f'{self.directory}/{fileNameAudio}'     
                self.textToVoice(text, pathFileNameAudio)
                return {
                    "fileName": fileNameAudio,
                    "pathFileName": pathFileNameAudio
                }
        return None



    def textToVoice(self, text:str, fileName:str, voiceIndex=0, rate=150, volume=1.5):
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[voiceIndex].id)
        voices = engine.getProperty('voices')
        engine.save_to_file(text, fileName)
        if self.sound:
            engine.say(text)
        engine.runAndWait()
        return True



    ###############################################################################################
    ####   Creando el componente HTML con resultados del analisis   ###############################
    ###############################################################################################

    def _create_for_html(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["analyse"] is not None:
                imageFileName = self.marketData["analysisCandles"]["graph"]["fileName"]
                componentHTML: str = f'<div><table>\n'
                componentHTML += "<tr>\n"
                componentHTML += f"<td><img src='{imageFileName}' width='800px'></img></td>\n"
                componentHTML += "<td>"
                
                quoteId = ""
                precisionPrice = 10
                if self.marketData['market'] is not None:
                    quoteId = self.marketData['quoteId']
                    precisionPrice = self.marketData['market']["precision"]["price"]
                metrics = self.marketData["analysisCandles"]["analyse"]["metrics"]
                closeConditions = self.marketData["analysisCandles"]["analyse"]["closeConditions"]
                componentHTML += self.value_html("Crecimiento total", metrics["deltaPercent"], 3, unit="%")
                if metrics["deltaPercent"] > 0:
                    componentHTML += self.value_html("Crecimiento aproximado por hora", metrics["profitPercentPerHours"], 3, unit="%")
                    componentHTML += self.value_html("Tiempo estimado para alcanzar 1 %", metrics["hoursToProfit1Percent"], 1, unit="horas")

                componentHTML += self.value_html("Precio inicial", metrics["open"], precisionPrice, unit=quoteId)
                componentHTML += self.value_html("Precio minimo", metrics["low"], precisionPrice, unit=quoteId)
                componentHTML += self.value_html("precio maximo", metrics["higt"], precisionPrice, unit=quoteId)
                componentHTML += self.value_html("Ultimo precio", metrics["close"], precisionPrice, unit=quoteId)
                if "linearBands" in metrics:
                    linearBands = metrics["linearBands"]        
                    componentHTML += self.value_html("Desviacion media por encima y debajo de tendencia", linearBands["deltaAverage"], 2, unit="%")
                    componentHTML += self.value_html("Desviacion maxima por encima", linearBands["deltaUpperMax"], 2, unit="%")
                    componentHTML += self.value_html("Desviacion minima por debajo", linearBands["deltaLowerMin"], 2, unit="%")
                    componentHTML += self.value_html("Media por encima de tendencia", linearBands["deltaUpperAverage"], 2, unit="%")
                    componentHTML += self.value_html("Media por debajo de tendencia", linearBands["deltaLowerAverage"], 2, unit="%")

                if "volumeProfile" in metrics and metrics["volumeProfile"] is not None: 
                    for peaks in metrics["volumeProfile"]["peaks"]:
                        componentHTML += self.value_html("Volumen significativo cercano a", peaks, precisionPrice, unit=quoteId)
                if closeConditions is not None:
                    componentHTML += self.value_html(
                        "Take Profit Price", closeConditions["takeProfitPrice"], precisionPrice, "green", True, unit=quoteId)
                    componentHTML += self.value_html(
                        "Stop Loss Price", closeConditions["stopLossPrice"], precisionPrice, "red", True, unit=quoteId)
                    componentHTML += self.value_html(
                        "Take Profit Percent", closeConditions["takeProfitPercent"], 2, "green", True, unit="%")
                    componentHTML += self.value_html(
                        "Stop Loss Percent", closeConditions["stopLossPercent"], 2, "red", True, unit="%")
                    componentHTML += self.value_html(
                        "Time to Take Profit", self.time_minutes_to_text(closeConditions["minutesToTakeProfit"]))
                    
                componentHTML += "</td>\n"
                componentHTML += "</tr>\n"
                componentHTML += "</table></div>\n"
                if self.marketData["analysisCandles"]["text"] is not None:
                    text = self.marketData["analysisCandles"]["text"]["text"]
                    componentHTML += f"<tr><p>{text}</p></tr>\n"
                return componentHTML
        return None



    def value_html(self, lavel:str, value:Union[int, float, str], decimals:Optional[int]=None, 
                  color:str='#0000ff', strong:bool=False, unit:str=""):
        if type(value) == str:
            valueStr = str(f'{value} {unit}')
        else:
            if decimals is not None:
                value = self.round_str(value, decimals)
            else:
                value = self.as_str(value)
            valueStr = str(f'{value} {unit}')
        if strong:
            valueStr = f"<strong>{valueStr}</strong>"
        return f"<strong>{lavel}</strong>: <font color='{color}'>{valueStr}</font><br>\n"



    ###############################################################################################
    ####   Creando el contenido para mostrar el analisis en un chat   #############################
    ###############################################################################################

    def _create_for_chat(self):
        if self.marketData is not None:
            if self.marketData["analysisCandles"]["analyse"] is not None:
                # Aqui comienza el codigo especifico del tipo de analisis.
                return None     # Si no se hace nada, se debe devolver None.
                # Aqui termina el codigo especifico del tipo de analisis.
        return None



