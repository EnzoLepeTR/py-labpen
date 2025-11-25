import math

import pyodbc
from tqdm import *
import requests
import json
import os
import logging, sys
import msvcrt
from datetime import datetime
from pathlib import Path
import re
from autocorrect import Speller
from base64 import b64decode
import codecs
from typing import List
from pathlib import Path

from clases.configuracion import Configuracion
from clases.utils import Utils

class OCR(Configuracion):

    def __init__(self):
        self.data = self.getConfig()

    '''
    '''
    def getTtext(self, PDFLocalPath, TXTLocalPath):

        try:
            command = self.data["XpdfPath"]
            os.system(command + " " + PDFLocalPath + " " + TXTLocalPath)
        except:
            return ""

        '''
        if(os.path.exists(TXTLocalPath)):
            with open(TXTLocalPath, "r") as textFile:
                text = textFile.read()            
            return self.cleanText(text.strip(), TXTLocalPath)
        '''
        return self.cleanFile(TXTLocalPath)
    
    '''
    '''
    def cleanFile(self, filePath: str) -> str:
        filas: List[str] = []
        with codecs.open(filePath, "r", encoding="cp1252") as file:
            for line in file:
                fileText = ""

                text = self.replaceHexadecimalSymbols(line.strip())
                if text.strip() == "":
                    continue

                # Elimina número de página
                elif len(text.strip()) < 4:
                    numeroPagina = 0
                    texto = text.strip()
                    if not texto.isdigit():
                        fileText += self.finalPoint(texto)

                else:
                    text = self.finalPoint(text)
                    text = self.doublePoint(text)
                    fileText += text + "\r\n"

                filas.append(fileText)

        # Recorremos el arreglo de filas
        i = 0
        while i < len(filas):
            sFila = filas[i].strip()

            if sFila == "":
                i += 1
                continue

            arrNumero = sFila.split()
            if len(arrNumero) == 2:  # Existe un espacio //0000012 DOCE
                if arrNumero[0].isdigit():
                    numero = int(arrNumero[0])
                    dNumero = int(numero)
                    if self.writtenAmount(dNumero) == arrNumero[1]:
                        filas[i] = ""

            #0000293
            #DOSCIENTOS NOVENTA Y TRES 12
            elif sFila.isdigit():
                numero = int(sFila)
                dNumero = int(numero)
                nextFile = filas[i + 1].strip()
                arrNextFile = nextFile.split(" ")
                sWrittenAmount = ""
                if arrNextFile[-1].isdigit():
                    arrNextFile.remove(arrNextFile[-1])
                    for word in arrNextFile:
                        sWrittenAmount+= word + " "
                    sWrittenAmount =  sWrittenAmount.strip()
                else:
                    sWrittenAmount = filas[i + 1].strip()

                if self.writtenAmount(dNumero) == sWrittenAmount:
                    try:
                        filas[i] = ""
                        filas[i + 1] = ""
                    except Exception as e:
                        pass

            i += 1

        fileText = "".join(filas)

        datePatron = r'(\d{2}/\d{2}/\d{4})'
        fileText = re.sub(datePatron, r'\1\r\n', fileText)

        return fileText

    def replaceHexadecimalSymbols(self, txt:str) -> str:
        r = '[\x00-\x08\x0B\x0C\x0E-\x1F\x26\x91\x92]'
        txt = re.sub(r, ' ', txt)
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('\n\n', '**SALTO**')
        txt = txt.replace('\'', '-')
        txt = txt.replace('**SALTO**', '\n\n')


        return txt

    def finalPoint(self, txt:str) -> str:
        if txt.strip() == "":
            return txt

        if txt[-1] == ".":
            return txt + "\n"
        else:
            return txt + " "

    def doublePoint(self, txt:str) -> str:
        posicion = txt.strip().find(":")
        if posicion == -1: # no existe
            return txt
        else:
            if posicion == len(txt.strip()) - 1:
                return txt + "\n"
            else:
                return txt

    def writtenAmount(self, value:float) -> str:
        num2Text = ""
        try:
            value = int(value)
            if value == 0:
                num2Text = "CERO"
            elif value == 1:
                num2Text = "UNO"
            elif value == 2:
                num2Text = "DOS"
            elif value == 3:
                num2Text = "TRES"
            elif value == 4:
                num2Text = "CUATRO"
            elif value == 5:
                num2Text = "CINCO"
            elif value == 6:
                num2Text = "SEIS"
            elif value == 7:
                num2Text = "SIETE"
            elif value == 8:
                num2Text = "OCHO"
            elif value == 9:
                num2Text = "NUEVE"
            elif value == 10:
                num2Text = "DIEZ"
            elif value == 11:
                num2Text = "ONCE"
            elif value == 12:
                num2Text = "DOCE"
            elif value == 13:
                num2Text = "TRECE"
            elif value == 14:
                num2Text = "CATORCE"
            elif value == 15:
                num2Text = "QUINCE"
            elif value < 20:
                num2Text = "DIECI" + self.writtenAmount(value - 10)
            elif value == 20:
                num2Text = "VEINTE"
            elif value < 30:
                num2Text = "VEINTI" + self.writtenAmount(value - 20)
            elif value == 30:
                num2Text = "TREINTA"
            elif value == 40:
                num2Text = "CUARENTA"
            elif value == 50:
                num2Text = "CINCUENTA"
            elif value == 60:
                num2Text = "SESENTA"
            elif value == 70:
                num2Text = "SETENTA"
            elif value == 80:
                num2Text = "OCHENTA"
            elif value == 90:
                num2Text = "NOVENTA"
            elif value < 100:
                num2Text = self.writtenAmount(int(value / 10) * 10) + " Y " + self.writtenAmount(value % 10)
            elif value == 100:
                num2Text = "CIEN"
            elif value < 200:
                num2Text = "CIENTO " + self.writtenAmount(value - 100)
            elif value in (200, 300, 400, 600, 800):
                num2Text = self.writtenAmount(int(value / 100)) + "CIENTOS"
            elif value == 500:
                num2Text = "QUINIENTOS"
            elif value == 700:
                num2Text = "SETECIENTOS"
            elif value == 900:
                num2Text = "NOVECIENTOS"
            elif value < 1000:
                num2Text = self.writtenAmount(int(value / 100) * 100) + " " + self.writtenAmount(value % 100)
            elif value == 1000:
                num2Text = "MIL"
            elif value < 2000:
                num2Text = "MIL " + self.writtenAmount(value % 1000)
            elif value < 1000000:
                num2Text = self.writtenAmount(math.trunc(value / 1000)) + " MIL"
                if (value % 1000) > 0:
                    num2Text = num2Text + " " + self.writtenAmount(value % 1000)
            elif value == 1000000 :
                num2Text = "UN MILLON"
            elif value < 2000000:
                num2Text = "UN MILLON " + self.writtenAmount(value % 1000000)
            elif value < 1000000000000:
                num2Text = self.writtenAmount(int(value / 1000000)) + " MILLONES "
                if (value - int(value / 1000000) * 1000000) > 0:
                    num2Text = num2Text + " " + self.writtenAmount(value - int(value / 1000000) * 1000000)
            elif value == 1000000000000:
                num2Text = "UN BILLON"
            elif value < 2000000000000:
                num2Text = "UN BILLON " + self.writtenAmount(value - int(value / 1000000000000) * 1000000000000)
            else:
                num2Text = self.writtenAmount(int(value / 1000000000000)) + " BILLONES"
                if (value - int(value / 1000000000000) * 1000000000000) > 0:
                    num2Text = num2Text + " " + self.writtenAmount(value - int(value / 1000000000000) * 1000000000000)
            return num2Text
        except Exception as exEstado:
            print(exEstado)
            return ""
