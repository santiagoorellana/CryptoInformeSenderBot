
import time
from typing import List, Any, Dict, Literal, Optional, Union
import os
from math import trunc
import sys
import logging
from statistics import mean
import datetime


CANDLE_TIMESTAMP = 0
CANDLE_OPEN = 1
CANDLE_HIGT = 2
CANDLE_LOW = 3
CANDLE_CLOSE = 4
CANDLE_VOLUME = 5


# Definiciones de datos de la libreria CCXT
Ticker = Dict
DictOfTickers = Dict
Candles = Dict
ListOfCandles = List[Candles]
MarketId = str
ListOfMarketsId = List[MarketId]
Market = Dict
DictOfMarkets = Dict
CurrencyId = str
ListOfCurrenciesId = List[CurrencyId]
Currency = Dict
DictOfCurrencies = Dict
Balance = Dict
Order = Dict
PrecisionType = Literal["price", "amount", "cost"]
Side = Literal["buy", "sell"]
AmountLimit = Literal["min", "max"]


# Definiciones de datos propios
CloseConditions = Dict
Metrics = Dict
ListOfTickers = List[Ticker]
Filters = Dict
MarketData = Dict
ListOfMarketData = List[MarketData]
ComparisonCondition = Literal["above", "below"]
Category = Literal["potentialMarket", "openInvest", "closedInvest"]
Action = Literal["open", "close", "check", "change"]


log = None



class Basics():   

    @staticmethod
    def as_str(value:float) -> str:
        '''
        Devuelve la cadena que representa al valor solo con los decimales sigificativos.
        Esta funcion garantiza tambien que el numero no sea mostrado como notacion cientifica.\n
        param value: Numero con decimales que se debe representar como cadena.
        Solo se representan hasta 15 decimales. Cualquier valor con mas de 15 decimales, 
        sera redondeado a 15 decimales.\n
        return: Devuelve una cadena que representa al numero con solo los decimales significativos.
        '''
        completed = False
        result = ""
        valueStr = "{:.15f}".format(value).strip()[::-1]
        for index in range(len(valueStr)):
            char = valueStr[index]
            if char == "." and not completed:
                result += "0"
                completed = True
            if char != "0" or completed:
                result += char
                completed = True
        return str(result[::-1])



    @staticmethod
    def round_str(value:float, decimals:int) -> str:
        '''
        Devuelve la cadena que representa al valor solo con los decimales especificados.
        Esta funcion garantiza tambien que el numero no sea mostrado como notacion cientifica.\n
        param value: Numero con decimales que se debe representar como cadena.
        Solo se representan hasta 15 decimales. Cualquier valor con mas de 15 decimales, 
        sera redondeado a 15 decimales.\n
        return: Devuelve una cadena qeu representa al numero con solo los decimales especificados.
        '''
        if decimals < 0:
            decimals = 10
        decimals = int(decimals)
        valueStr = "{:." + str(decimals) + "f}"
        return valueStr.format(round(value, decimals))



    @staticmethod
    def cmd_object(data:Any, title:str="", ident:str='\t', level:int=1) -> bool:
        """
        Muestra los datos de un json. 
        param data: Objeto que se debe mostrar en consola.
        param title: Titulo que precede a los datos del objeto que se muestra.
        param ident: Caracteres que se ponen delante de cada linea para indentar.
        param level: Nivel de indentacion en que se muestran los datos.
        return: True si logra mostrar los datos del objeto. False si ocurre error.
        """
        try:
            if type(data) == dict or type(data) == list or type(data) == tuple:
                if title != "":
                    log.info(f"{str(ident) * (level - 1)}{title}")
                if type(data) == dict:
                    for key in data.keys():
                        time.sleep(0.1)
                        Basics.cmd_object(data[key], key, ident=ident, level=level+1)
                else:
                    count = 0
                    for element in data:
                        time.sleep(0.1)
                        Basics.cmd_object(element, f'elemento {count}', ident=ident, level=level+1) 
                        count += 1
            else:
                log.info(f"{str(ident) * (level - 1)}{title}: {str(data)}") 
            return True
        except Exception as e:
            log.info(f"ERROR: No se pudo mostrar el dato.")
            log.info(f"EXCEPTION: {str(e)}")
            return False               



    @staticmethod
    def base_of_symbol(symbol:MarketId) -> CurrencyId:
        '''
        param symbol: Idetificador de symbol compuesto por la estructura "base/quote". 
        return: Devuelve el idetificador de la currency base. Si hay error, devuelve cadena vacia.
        '''
        try:
            return str(symbol).split('/')[0]
        except Exception as e:
            return ""

            

    @staticmethod
    def quote_of_symbol(symbol:MarketId) -> CurrencyId:
        '''
        param symbol: Idetificador de symbol compuesto por la estructura "base/quote". 
        return: Devuelve el idetificador de la currency quote. Si hay error, devuelve cadena vacia.
        '''
        try:
            return str(symbol).split('/')[1]
        except Exception as e:
            return ""



    @staticmethod
    def delta(fromValue: float, toValue: float) -> float:
        '''
        Calcula la variación en porciento entre dos valores.
        Se puede utilizar para calcular el rendimiento de un activo o currecy.
        Para calcular el porciento, se toma como total el valor inicial "fromValue".
        param fromValue: Valor inicial.
        param toValue: Valor final.
        return: Variación en porciento entre los valores "fromValue" y "toValue".
                Si ocurre error no se maneja la excepcion.
        '''
        return (toValue - fromValue) / fromValue * 100
        


    @staticmethod
    def percentage(value:float, total:float) -> float:
        '''
        Calcula el porciento de un valor con respecto a un total.
        param value: Valor al que se le calcula el porciento.
        param total: Valor total.
        return: Porciento del valor con respecto al total. No se maneja excepcion.
        '''
        return value / total * 100 if total != 0 else 0
        


    @staticmethod
    def candle_statistics(candleData):
        valueMean = (candleData[1] + candleData[2] + candleData[3] + candleData[4]) / 4
        return {
            "timestampUTC": candleData[0],
            "open": candleData[1],
            "high": candleData[2],
            "low": candleData[3],
            "close": candleData[4],
            "volume": candleData[5],
            "mean": valueMean,
            "deltaUp": candleData[2] - valueMean,
            "deltaDow": candleData[3] - valueMean
        }



    @staticmethod
    def position_on_range(value:float, rangeValueBegin:float, rangeValueEnd:float, remaining:bool=False) -> float:
        '''
        Calcula la posición en porciento de un valor con respecto a un rango.
        Por defecto se devuelva la posicion con respecto al inicio del rango.
        param value: Valor al que se le va a calcular la posicion dentro del rango.
        param fromValue: Valor inicial del rango.
        param toValue: Valor final del rango.
        param remaining: Poner a True para que se devuelva la posicion con respecto al final del rango.
        return: Posición en porciento del valor en el rango. Si ocurre error no se maneja la excepcion.
        '''
        rangeAmplitude = abs(rangeValueEnd - rangeValueBegin)
        if rangeAmplitude == 0:
            return 0
        positionFromBegin = value - min(rangeValueBegin, rangeValueEnd)
        positionFromBeginAsPercent = (positionFromBegin / rangeAmplitude) * 100
        return 100 - positionFromBeginAsPercent if remaining else positionFromBeginAsPercent
        


    @staticmethod
    def prepare_directory(directoryPath:str) -> bool:
        '''
        Crea el directorio especificado si este no existe.
        param directoryPath: Nombre del directorio icluyedo la ruta completa. 
        return: True si logra crear el directorio o si ya existe. False si no existe y no logra crearlo.
        '''
        try:
            os.stat(directoryPath)
        except:
            try:
                os.mkdir(directoryPath)   
            except Exception as e:
                log.info(f'ERROR: Creando el directorio: {directoryPath}')
                return False
        return True



    @staticmethod
    def hours(timestampBegin, timestampEnd):
        return float((timestampEnd - timestampBegin) / 1000 / 60 / 60)



    @staticmethod
    def script_path():
        return os.path.dirname(os.path.realpath(sys.argv[0]))



    @staticmethod
    def graph_candles(marketId:MarketId, candles:Optional[ListOfCandles]=None, count:int=24, timeFrame:str="1h"):
        SPACE = ' '
        BAR_SHORT = "."
        BAR_LONG =  "|"
        LINES_COUNT = 21
        if candles is not None:
            log.info(f'\n{marketId} en las ultimas {len(candles)} velas {timeFrame}:\n')
            closes = [float(candle[4]) for candle in candles]
            minValue = min(closes)
            rangeValues = max(closes) - minValue
            lines = ["" for i in range(LINES_COUNT)]
            prices = lines.copy()
            for close in closes:
                ratio = (close - minValue) / rangeValues if rangeValues != 0 else 0
                position = trunc((LINES_COUNT - 1) * ratio)
                charBar = BAR_SHORT if (LINES_COUNT - 1) * ratio - position < 0.5 else BAR_LONG
                for index in range(LINES_COUNT):
                    if position == index:
                        lines[index] += charBar
                        if prices[index] == "":
                            prices[index] = f'{Basics.as_str(close)} {Basics.quote_of_symbol(marketId)}'
                    elif position > index:
                        lines[index] += BAR_LONG
                    else:
                        lines[index] += SPACE
            lines.reverse()
            prices.reverse()
            for index in range(LINES_COUNT):
                log.info(f'{"".join(lines[index])} {SPACE} {prices[index]}')



    @staticmethod
    def print_head():
        log.info('\n****************************************')
        log.info('MARKET VIEW 1.0')
        log.info('autor: Santiago A. Orellana Perez')
        log.info('email: tecnochago@gmail.com')



    @staticmethod
    def temporality_as_minutes(temporality):
        temporalitiesAsMinutes = {
            "1m": 1, "2m": 2, "3m": 3, "4m": 4, "5m": 5, "6m": 6, 
            "7m": 7, "8m": 8, "9m": 9, "10m": 10, "15m": 15, "30m": 30,
            
            "1h": 1 * 60, "2h": 2 * 60, "3h": 3 * 60, "4h": 4 * 60, "5h": 5 * 60, "6h": 6 * 60, 
            "7h": 7 * 60, "8h": 8 * 60, "9h": 9 * 60, "10h": 10 * 60, "11h": 11 * 60, "12h": 12 * 60,
            
            "1d": 1 * 24 * 60, "2d": 2 * 24 * 60, "3d": 3 * 24 * 60, 
            "4d": 4 * 24 * 60, "5d": 5 * 24 * 60, "6d": 6 * 24 * 60,

            "1s": 1 * 7 * 24 * 60, "2s": 2 * 7 * 24 * 60, "3s": 3 * 7 * 24 * 60,
            
            "1M": 1 * 30 * 24 * 60, "2M": 2 * 30 * 24 * 60, "3M": 3 * 30 * 24 * 60,
            "4M": 4 * 30 * 24 * 60, "5M": 5 * 30 * 24 * 60, "6M": 6 * 30 * 24 * 60,
            
            "1y": 1 * 365 * 24 * 60
        }
        if temporality in temporalitiesAsMinutes:
            return temporalitiesAsMinutes[temporality]
        return 0
            


    @staticmethod
    def temporality_as_text(temporality):
        if temporality[0] == "1":
            temporality = temporality.replace("m", " minuto") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("h", " hora") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("d", " día") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("s", " semana") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("M", " mes") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("y", " año") if len(temporality) <= 3 else temporality
            return temporality
        else:
            temporality = temporality.replace("m", " minutos") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("h", " horas") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("d", " días") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("s", " semanas") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("M", " meses") if len(temporality) <= 3 else temporality
            temporality = temporality.replace("y", " años") if len(temporality) <= 3 else temporality
            return temporality
            
            

    def candle_resume(self, candle, resumeType:Literal["close", "mean", "border"]):
        if resumeType == "close":
            return candle[CANDLE_CLOSE]
        elif resumeType == "mean":
            return mean([candle[CANDLE_OPEN], candle[CANDLE_LOW], candle[CANDLE_HIGT], candle[CANDLE_CLOSE]])
        elif resumeType == "border":
            if candle[CANDLE_CLOSE] > candle[CANDLE_OPEN]:
                return candle[CANDLE_HIGT]
            else:
                return candle[CANDLE_LOW]


    @staticmethod
    def time_minutes_to_text(minutes):
        if minutes < 60:
            return f"{round(minutes, 1)} minutos"
        if minutes / 60 < 24:
            return f"{round(minutes / 60, 1)} horas"
        return f"{round(minutes / 60 / 24, 1)} días"
    

    def create_unique_id(self) -> str:
        '''Crea un id unico utilizando la fecha-hora actual.'''
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    
    def create_unique_filename(self, prefix:str, extension:str) -> str:
        '''Crea un nombre de fichero unico ubicado en el directorio de reporte.'''
        return f'{self.directoryDateTime}/{prefix}_{self.uniqueDateTimeLabel}.{extension}'
    

    
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))
log.addHandler(logging.FileHandler(f'{Basics.script_path()}/execution.txt'))

