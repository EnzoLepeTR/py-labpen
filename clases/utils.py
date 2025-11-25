import requests
import os
import glob
from datetime import datetime

from bs4 import BeautifulSoup, NavigableString
import html
import re

class Utils:

    """
        Método que permite extraer desde una cadena stringHTML un sun string
        delimitado por initStringDelimiter y endStringDelimiter
        el string resultante no incluye estos dos elementos
    """
    @staticmethod
    def getDelimiterText(stringHTML, initStringDelimiter, endStringDelimiter):
        try:
            stringInit = initStringDelimiter
            indexInit = stringHTML.index(initStringDelimiter)
            stringEnd = endStringDelimiter
            indexEnd = stringHTML.index(stringEnd, indexInit+1)
            if (indexEnd > indexInit):
                stringHTML = stringHTML[indexInit + len(initStringDelimiter) :indexEnd]
        except Exception as exEstado:
            print("Error al consultar: ", exEstado)
        return stringHTML

    """
        Método que elimina el contenido de un directorio
        Ej: C:\\temp\\txt
    """
    @staticmethod
    def cleanWorkingDir(path):
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))
    
    """
        Método que permite calcular porcentaje
    """
    @staticmethod
    def percentaje(procesados, grabados):
        porcentaje = 0

        if procesados>0:
            porcentaje = (grabados * 100) /procesados

        return round(porcentaje, 2)

    """
        Método que permite ejecutar linea de comandos
    """
    @staticmethod
    def executeCommand(pathProgram,  command):
        os.system(pathProgram + " " + command + " > log.txt")

    """
    Método que permite extraer el año de una fecha
    """
    @staticmethod
    def getYear(date):
        try:
            
            return date[6:10]
            
        except:
            return ""

    """
    Método que permite formatear la fecha en dd/mm/aaaa => aaaa/mm/aa
    01234567890   0123456789
    17/02/2023    10/02/2023

    """
    @staticmethod
    def formatDateSQLLite(date):

        return date[6:10] + "/" + date[3:5] + "/" + date[0:2]

    '''
    Construye el path del PDF para la maquina local
    '''
    @staticmethod   
    def getPDFLocalPath(PDFPath, fallo):
        return PDFPath + "\\" + fallo.rol + ".pdf"

    '''
    Construye el path del txt para la maquina local, este archivo contendra el texto final
    '''
    @staticmethod   
    def getTXTLocalPath(TXTPath, fallo):
        return TXTPath + "\\" + fallo.rol + ".txt"


    '''
    Metodo que permite leer el contenido de un directorio, teniendo en cuenta una extension
     @param folder
     @param ext
     @return arreglo con el nombre de los archivos
    '''
    @staticmethod   
    def readFolder(folder, ext):

        os.chdir(folder)
        files = sorted(filter(os.path.isfile, os.listdir('.')), key=os.path.getmtime)

        images = []

        for file in files:
            filePath = os.path.join(folder, file)
            try:
                if os.path.isfile(filePath):
                    if file.endswith('.' + ext): # Verificamos si posee la extension
                        images.append(file)
            except Exception as e:
                print(e)
        return images

    '''
    Metodo que permite extraer un texto desde otro, mediante delimitadores     
    '''
    @staticmethod   
    def getInnerTextWithDelimiters(txt, stringInit, stringEnd):
        indexInit = txt.find(stringInit)
        
        if(indexInit == -1):
            return ""

        indexEnd = txt.find(stringEnd, indexInit)

        if(indexEnd == -1):
            return ""

        indexInit = indexInit + len(stringInit)
        try:
            finalText = txt[indexInit: indexEnd]
        except:
            return ""

        return finalText.strip()   

    '''
    Metodo que elimina el texto entre los delimitadores del string principal
    '''
    @staticmethod
    def getOuterTextWithDelimiters(txt, stringInit, stringEnd):
  
        indexInit = txt.find(stringInit)

        while(indexInit>-1):

            indexEnd = txt.find(stringEnd, indexInit)

            if(indexEnd == -1):
                break

            indexEnd = indexEnd + len(stringEnd)
            txt = txt[0: indexInit].strip() + " " +  txt[indexEnd: -1].strip()
            indexInit = txt.find(stringInit)

        ##Eliminamos hasta el final
        index = txt.find(stringInit)
        if(index>-1):
            txt = txt[0: indexInit].strip();
        return txt

    '''
    '''
    @staticmethod 
    def getTemplateXML(configData):
        filePath = configData["EmailTemplatePath"]
        f = open(filePath, mode="r", encoding="utf-8")
        template = f.read()
        f.close()
        return template                

    '''
    '''
    @staticmethod
    def getLastFilenameAndRename(save_folder, new_filename):
        try:
            files = glob.glob(save_folder + '/*')
            max_file = max(files, key=os.path.getctime)
            filename = max_file.split("/")[-1].split(".")[0]
            new_path = max_file.replace(filename, save_folder + "\\" +new_filename)
            os.rename(max_file, new_path)
            return new_path
        except:
            return ""
    '''
    '''
    @staticmethod
    def getTribunalId(tribunal: str) -> str:
        # Lista de tribunales como tuplas (id, nombre, tribunal)
        tribunales = [
            ("70", "Nacional", "1º Juzgado de Letras del Trabajo de Santiago"),
            ("71", "Nacional", "2º Juzgado de Letras del Trabajo de Santiago"),
            ("72", "Nacional", "Juzgado de Letras del Trabajo de San Miguel"),
            ("73", "Nacional", "Juzgado de Letras del Trabajo de Valparaíso"),
            ("74", "Nacional", "Juzgado de Letras del Trabajo de Concepción"),
            ("75", "Nacional", "Juzgado de Letras del Trabajo de Antofagasta"),                                 
            ("119", "Nacional", "Juzgado de Letras del Trabajo de Arica"),
            ("120", "Nacional", "Juzgado de Letras del Trabajo de Calama"),
            ("121", "Nacional", "Juzgado de Letras del Trabajo de Copiapó"),
            ("122", "Nacional", "Juzgado de Letras del Trabajo de La Serena"),
            ("123", "Nacional", "Juzgado de Letras del Trabajo de San Felipe"),
            ("124", "Nacional", "Juzgado de Letras del Trabajo de Puente Alto"),
            ("125", "Nacional", "Juzgado de Letras del Trabajo de San Bernardo"),
            ("126", "Nacional", "Juzgado de Letras del Trabajo de Curicó"),
            ("127", "Nacional", "Juzgado de Letras del Trabajo de Talca"),
            ("128", "Nacional", "Juzgado de Letras del Trabajo de Chillán"),
            ("129", "Nacional", "Juzgado de Letras del Trabajo de Los Angeles"),
            ("130", "Nacional", "Juzgado de Letras del Trabajo de Temuco"),
            ("131", "Nacional", "Juzgado de Letras del Trabajo de Valdivia"),
            ("132", "Nacional", "Juzgado de Letras del Trabajo de Osorno"),
            ("133", "Nacional", "Juzgado de Letras del Trabajo de Castro"),
            ("134", "Nacional", "Juzgado de Letras del Trabajo de Coyhaique"),
            ("135", "Nacional", "Juzgado de Letras del Trabajo de Punta Arenas"),
            ("76", "Nacional", "1º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("77", "Nacional", "2º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("78", "Nacional", "3º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("79", "Nacional", "4º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("80", "Nacional", "5º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("81", "Nacional", "6º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("82", "Nacional", "7º Tribunal de Juicio Oral en lo Penal de Santiago"),
            ("83", "Nacional", "Tribunal de Juicio Oral en lo Penal Colina"),
            ("84", "Nacional", "Tribunal de Juicio Oral en lo Penal de Melipilla"),
            ("85", "Nacional", "Tribunal de Juicio Oral en lo Penal de Osorno"),
            ("86", "Nacional", "Tribunal de Juicio Oral en lo Penal Puente Alto"),
            ("87", "Nacional", "Tribunal de Juicio Oral en lo Penal San Bernardo"),
            ("88", "Nacional", "Tribunal de Juicio Oral en lo Penal Talagante"),
            ("89", "Nacional", "Tribunal de Juicio Oral en lo Penal Puerto Montt."),
            ("90", "Nacional", "Tribunal de Juicio Oral en lo Penal Punta Arenas."),
            ("91", "Nacional", "Tribunal de Juicio Oral en lo Penal San Antonio."),
            ("92", "Nacional", "Tribunal de Juicio Oral en lo Penal San Fernando."),
            ("93", "Nacional", "Tribunal de Juicio Oral en lo Penal Viña Del Mar."),
            ("94", "Nacional", "Tribunal de Juicio Oral en lo Penal de Angol."),
            ("95", "Nacional", "Tribunal de Juicio Oral en lo Penal de Antofagasta."),
            ("96", "Nacional", "Tribunal de Juicio Oral en lo Penal de Arica"),
            ("97", "Nacional", "Tribunal de Juicio Oral en lo Penal de Calama"),
            ("98", "Nacional", "Tribunal de Juicio Oral en lo Penal de Cauquenes"),
            ("99", "Nacional", "Tribunal de Juicio Oral en lo Penal de Chillán"),
            ("100", "Nacional", "Tribunal de Juicio Oral en lo Penal de Concepción"),
            ("101", "Nacional", "Tribunal de Juicio Oral en lo Penal de Copiapó"),
            ("102", "Nacional", "Tribunal de Juicio Oral en lo Penal de Coyhaique"),
            ("103", "Nacional", "Tribunal de Juicio Oral en lo Penal de Curicó"),
            ("104", "Nacional", "Tribunal de Juicio Oral en lo Penal de Iquique"),
            ("105", "Nacional", "Tribunal de Juicio Oral en lo Penal de Linares"),
            ("106", "Nacional", "Tribunal de Juicio Oral en lo Penal de Ovalle"),
            ("107", "Nacional", "Tribunal de Juicio Oral en lo Penal de Quillota"),
            ("108", "Nacional", "Tribunal de Juicio Oral en lo Penal de Rancagua"),
            ("109", "Nacional", "Tribunal de Juicio Oral en lo Penal de San Felipe"),
            ("110", "Nacional", "Tribunal de Juicio Oral en lo Penal de Santa Cruz"),
            ("111", "Nacional", "Tribunal de Juicio Oral en lo Penal de Talca"),
            ("112", "Nacional", "Tribunal de Juicio Oral en lo Penal de Temuco"),
            ("113", "Nacional", "Tribunal de Juicio Oral en lo Penal de Valdivia"),
            ("114", "Nacional", "Tribunal de Juicio Oral en lo Penal de Valparaíso"),
            ("115", "Nacional", "Tribunal de Juicio Oral en lo Penal de Villarrica"),
            ("116", "Nacional", "Tribunal de Juicio Oral en lo Penal de La Serena"),
            ("117", "Nacional", "Tribunal de Juicio Oral en lo Penal de Los Andes"),
        ]

        # Buscar el tribunal
        for id_, _, nombre in tribunales:
            print(f"----> Tribunal buscado {tribunal.strip().upper()}")
            if tribunal.strip().upper() == nombre.upper():
                return id_

        return "0"  # Si no se encuentra

    """
    Método que permite formatear la fecha en dd/mm/aaaa => aaaa/mm/aa
    01234567890   0123456789
    17/02/2023    10/02/2023
    """
    @staticmethod
    def formatDate(date, originalFormat, targetFormat):

        originalDate = datetime.strptime(date, originalFormat)
        targetDate = originalDate.strftime(targetFormat)

        return targetDate

    @staticmethod
    def getHtml(html):
        plain = html.replace("<br>", "\r\n")
        plain = html.replace("<br/>", "\r\n")
        return plain

    @staticmethod
    def getPartes(partes):

        arrPartes = partes.split(" con ")
        if len(arrPartes) == 2:
            return arrPartes

        else:
            arrPartes = partes.split("/")
            if len(arrPartes) == 2:
                return arrPartes

        return []


    '''
    '''
    @staticmethod
    def sendMessageTelegram(materia, nProcesados):
        token = "6349966268:AAEeRcSCxLlZAfVHjsJYFIrNpiVG15jNFpw"
        chat_id = "5079994968"

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        try:
            # Mensaje de texto
            text_aux = f"<b>⚠️LOES</b>\nMateria: {materia}\nProcesados: {nProcesados}"

            data = {
                'chat_id': chat_id,
                'text': text_aux,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, verify=False)
            response.raise_for_status()  # Raise an exception for HTTP errors

        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")

    @staticmethod
    def normalizeText(text):
        text = text.lower()
        # Normaliza referencias legales
        text = re.sub(r'ley\s+n°?\s*(\d+)', r'ley \1', text)
        text = re.sub(r'decreto\s+\d+/\d+', 'decreto', text)
        # Elimina preposiciones comunes
        stopwords = ["de", "la", "el", "y", "en"]
        return " ".join([word for word in text.split() if word not in stopwords])