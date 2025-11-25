import logging, sys
import msvcrt
import re
from datetime import datetime
import pyodbc

from clases.configuracion import Configuracion

class Email(Configuracion):
    '''
    '''

    @staticmethod
    def getRowTemplate(i, fallo):

        color = "#FFF"
        estatusTmp = ""

        if i % 2 == 0:
            color = "EEE"
        else:
            color = "FFF"

        rTemplate = "<tr style=\"border-collapse:collapse; border:1px solid #666; background-color:#[##COLOR##];\">"
        rTemplate += "<td style=\"border-collapse:collapse; border:1px solid #666; padding:5px\" align=\"right\">"
        rTemplate += "<span style=\"color:#000000; font-size:11px; font-family:Arial;\">[##POS##]</span>"
        rTemplate += "</td>\r\n"
        rTemplate += "<td style=\"border-collapse:collapse; border:1px solid #666; padding:5px\">"
        rTemplate += "<span style=\"color:#000000; font-size:11px; font-family:Arial;\">[##ROL##]</span>"
        rTemplate += "</td>\r\n"
        rTemplate += "<td style=\"border-collapse:collapse; border:1px solid #666; padding:5px\" align=\"right\">"
        rTemplate += "<span style=\"color:#000000; font-size:11px; font-family:Arial;\">[##TITULO##]</span>"
        rTemplate += "</td>\r\n"
        rTemplate += "<td style=\"border-collapse:collapse; border:1px solid #666; padding:5px\">"
        rTemplate += "<span style=\"color:#000000; font-size:11px; font-family:Arial;\">[##FECHA##]</span>"
        rTemplate += "</td>\r\n"
        rTemplate += "</tr>\r\n"

        rTemplate = rTemplate.replace("[##COLOR##]", color)
        rTemplate = rTemplate.replace("[##POS##]", str(i + 1))
        rTemplate = rTemplate.replace("[##ROL##]", fallo.rol)
        rTemplate = rTemplate.replace("[##FECHA##]", str(fallo.fechaSentencia))
        rTemplate = rTemplate.replace("[##TITULO##]", fallo.titulo)

        return rTemplate

    @staticmethod
    def saveEmail(smsgHTML, configData):
        cs = configData["EmailCS"]
        DeNombre = configData["EmaildeNombre"]
        DeCorreo = configData["EmaildeCorreo"]
        Titulo = configData["EmailTitulo"]
        ResponderA = configData["EmailResponderA"]
        ParaCC = configData["EmailParaCC"]
        ContentHTML = "1"

        EmailNombre = configData["EmailNombre"]
        EmailEmail = configData["EmailEmail"]

        query = "INSERT INTO ErrMail(ErrNombreDe, ErrMailDe, ErrNombrePara, ErrMailPara, ErrTitulo, ErrMensaje, ErrResponderA, ErrParaCC,ErrTipoMensaje, ErrFechaError, ErrFechaEnviado, ErrEnviado, ErrNroIntento) "
        query += " VALUES('" + DeNombre + "',  '" + DeCorreo + "', '" + EmailNombre + "', '" + EmailEmail + "', '" + Titulo + "', '" + smsgHTML + "', '" + ResponderA + "', '" + ParaCC + "', " + ContentHTML + ", GETDATE(), NULL, 0, 0 )"

        conection = pyodbc.connect(cs)
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            conection.commit()
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("Error al grabar datos de email: ", exEstado)

        finally:
            try:
                conection.close()
            except:
                pass

