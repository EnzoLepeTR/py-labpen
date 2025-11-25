import logging, sys
import msvcrt
import re
from datetime import datetime
import pyodbc
from clases.configuracion import Configuracion

class Sumario(Configuracion):

    def __init__(self):
        self.id = 0
        self.id_fallo = 0
        self.texto = ""
        self.data = self.getConfig()

    def updateText(self):

        query = ""
        query = f"""update FalloSumario set texto = '{self.texto}' where id_Doc_Sumario = {self.id}"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[Sumario] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True

    def insertText(self):

        query = ""
        query = f"""insert into FalloSumario(id_fallo, texto) values({self.id_fallo}, '{self.texto}');"""
        cs = self.data["PJCS"]

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error al grabar datos[Sumario] ", exEstado)
            return False

        finally:
            try:
                conection.close()
            except:
                pass

        return True