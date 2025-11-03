
# paleta de colores: https://colorswall.com/es/palette/268193

import plotly.graph_objects as go # type: ignore
from plotly.subplots import make_subplots  # type: ignore
from basics import *
from files import *

Formats = Literal["png", "jpg", "jpeg", "webp", "svg", "pdf"]

DIRECTORY_DATA = "analysis"
DIRECTORY_DATETIME_PREFIX = "report"

class Report(Basics):
    
    def __init__(self):
        '''Inicia un objeto para crear reportes.'''
        self.error = True
        self.uniqueDateTimeLabel = self.create_unique_id()
        self.directoryData = f'{self.script_path()}/{DIRECTORY_DATA}/'
        if self.prepare_directory(self.directoryData):
            self.directoryDateTime = f'{self.directoryData}/{DIRECTORY_DATETIME_PREFIX}_{self.uniqueDateTimeLabel}'
            if self.prepare_directory(self.directoryDateTime):
                self.error = False
        self.imagesData = []



    def create(self, marketData, dataToJson:bool=True, toHtml:bool=True, toTelegram:bool=True):
        '''
        Guarda una copia de los datos en fichero JSON.
        Guarda las imagenes de los graficos de los datos.
        Crea un documeto HTML de reporte, con los datos y graficos.
        '''
        # Guarda los datos de analisis e fichero JSON.
        if dataToJson:
            fileNameJson = self.create_unique_filename('datos', 'json')
            Files.data_to_file_json(marketData, fileNameJson)
        
        # Crea los graficos de las velas a partir de los datos de analisis.
        self.create_graph_of_candles(marketData)
        fileNameWeb = f'{self.directoryDateTime}/reporte.html'
        
        if toHtml:
            self.create_report_html(marketData, fileNameWeb, True)
        if toTelegram:
            self.send_report_to_telegram(marketData, fileNameWeb, True)


