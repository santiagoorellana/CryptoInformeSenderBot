
import os
import json
from basics import *


class Files(Basics):
    
    def __init__(self, fileNameCsv:str):
        '''
        Crea un objeto para manejar el fichero de inversiones.
        param fileName: Nombre del fichero de inversiones.
        '''
        self.fileName = fileNameCsv
        self.headers = ['datetimeUTC', 'hours', 'symbol', 'profitAsPercent', 'profitAsQuote', 'priceOpen', 'priceClose']
        if not os.path.isfile(self.fileName):
            self._create_csv_file()

    

    def write(self, data) -> bool:
        '''
        Escribe una linea con los datos, en el fichero csv.
        param data: Datos que se debes escribir en el fichero csv.
        return: Devuelve True si logra escribir el dato en el fichero csv. De lo contrario devuelve False.
        '''
        if os.path.isfile(self.fileName):
            return self.data_to_file_text(self._csv_line_from(data), self.fileName)
        else:
            log.info(f'No existe el fichero: "{self.fileName}"')
            return self._create_csv_file()
    


    def _create_csv_file(self) -> bool:
        '''
        Crea un nuevo fichero csv.
        return: Devuelve True si logra crear el ficehro csv. De lo contrario devuelve False.
        '''
        if self.data_to_file_text(self._csv_line(self.headers), self.fileName):
            return True
        else:
            return False
        


    def _csv_line(self, valuesList:List[str], separator:str=",", endLine:str="") -> str:
        '''
        Crea una linea CSV de los valores de la lista, con el separador y final de linea especificados.
        param valuesList: Lista de los valores para crear la linea CSV.
        param separator: Caracter separador de los valores.
        param endLine: Caracter que marca el final de la linea.
        return: Devuelve una cadena en formato CSV con los valores de la lista.        
        '''
        line = separator.join(valuesList)
        return line + endLine + '\n'



    def _csv_line_from(self, data) -> str:
        '''
        Crea una linea CSV a partir de los datos de una inversion.
        param argv: Datos de una inversion realizada. 
        return: Devuelve una cadena con los valores de la inversion separados por coma.
        '''
        return self._csv_line([
            str(data["buy"]["datetime"]), 
            str(data["status"]["durationHours"]), 
            str(data["marketId"]), 
            str(data["status"]["profitAsPercent"]), 
            str(data["status"]["profitAsQuote"]), 
            str(data["buy"]["average"]), 
            str(data["sell"]["average"])
        ])



    @staticmethod
    def data_to_file_text(line:str, fileName:str) -> bool:
        '''
        Escribe en un fichero de texto la cadena de texto.
        param line: Cadena que contiene el texto.
        param fileName: Nombre y ruta del fichero que se debe crear.
        return: True si logra crear el fichero. False si ocurre error.
        '''
        try:
            with open(fileName, 'a') as file:
                file.write(line)
                return True
        except Exception as e:
            log.info(f'ERROR: creando el fichero "{fileName}"')
            log.info(f"EXCEPTION: {str(e)}")
        return False


    
    @staticmethod
    def data_to_file_json(data:Any, fileName:str) -> bool:
        '''
        Escribe en un fichero JSON los datos del diccionario.
        Sobrescribe los datos que contenga el fichero.
        param data: Diccionario que contiene los datos.
        param fileName: Nombre y ruta del fichero que se debe crear.
        return: True si logra crear el fichero. False si ocurre error.
        '''
        try:
            with open(fileName, 'w') as file:
                file.write(json.dumps(data, indent=4))
                return True
        except Exception as e:
            log.info(f'ERROR: abriendo el fichero "{fileName}"')
            log.info(f"EXCEPTION: {str(e)}")
        return False


        
    @staticmethod 
    def data_from_file_json(fileName:str, report:bool=True) -> Optional[Any]:
        '''
        Lee desde un fichero JSON los datos del diccionario.
        param fileName: Nombre y ruta del fichero que se debe leer.
        return: Diccionario con los datos del fichero. None si ocurre error.
        '''
        try:
            with open(fileName, 'r') as file:
                return json.load(file)
        except Exception as e:
            if report:
                log.info(f'ERROR: leyendo el fichero "{fileName}"')
                log.info(f"EXCEPTION: {str(e)}")
        return None



