import os
import json
import logging, sys
from datetime import datetime
from clases.fallo import Fallo
from clases.utils import Utils
from clases.utilsia import UtilsIA
from clases.configuracion import Configuracion
from clases.processIA import ProcessIA
class IA:
    '''
    Método que ejecuta el proceso de migración a partir de los datos extraidos desde la base de datos
    '''
    @staticmethod
    def processDB(sessionName):

        i = 1
        ia = Ia()
        for proIA in ia.getAll(): #Analisis Ia en estado 0
            proIA.update(1)
            proIA.numero, proIA.log = IA.process(proIA.ids, proIA.usuario, sessionName + "-" + str(i))
            proIA.update(2)
            i += 1

        #Eliminar programa de bloqueo
        print(f"Proceso terminado.")

    '''
    Metodo que a partir del texto de la sentencia, y mediante el API de ChatGPT, crea el titulo descriptor
    '''
    @staticmethod
    def process(fallosIds, tag, sessionName):
        #Leemos la configuracion
        config = Configuracion()
        configData = config.getConfig()

        #Definicion de directorios
        logPath = configData['logPath']
        elementCount = 0

        #Configuramos el logging en una archivo
        logFileName = "ia-log-" + sessionName + ".log"
        
        logFilePath = logPath + logFileName
        
        logging.basicConfig(filename=logFilePath, level=logging.DEBUG)
        logger = logging.getLogger()
        sys.stderr.write = logger.error
        sys.stdout.write = logger.info
    

        #Fecha inicio
        inicioProceso = str(datetime.today().strftime('%d/%m/%Y %H:%M:%S'))

        #Validamos que el listados de fallos
        arrayIds = fallosIds.split(",")
        arrayValidIds = list()
        countValidId = 0
        for id in arrayIds:
            try:
                iIds = int(id.strip())
                arrayValidIds.append(iIds)
                countValidId += 1
            except:
                print(f"El id: {id}, no es un entero válido.")

        if countValidId == 0:
            print(f"El listado de fallos, no contiene id's de fallos válidos, estos deben ser números enteros.")
            return 0, logFilePath

        # Conversion de documentos
        fallo = Fallo()
        ia = ProcessIA()
        ia.setModelVoces()
        ia.setModelLegislacion()        

        sys.stdout.reconfigure(encoding='utf-8')
        i = 1
        for j in fallo.getAllWithOutTitle(arrayValidIds):

            print("--------------------------------------------------------------------------")
            print(str(i) + ".- LOES ID: " + str(j.id))
            print("--------------------------------------------------------------------------")
            i+=1

            print("Inicio proceso análisis de jurisprudencia.");

            jsonAnalisis = ia.getAnalisis(j.texto)
            
            if jsonAnalisis == '':
                print("[!] Problema en el JSON, posible timeout.")
                continue
        
            jsonAnalisis = jsonAnalisis.replace("```json", "")
            jsonAnalisis = jsonAnalisis.replace("```", "")

            try:
                objAnalisis = json.loads(jsonAnalisis)
            except Exception as e:
                print("[!] Error al convertir en Json:" + str(e))
                continue

          
            j.titulo = objAnalisis.get("titulo_descriptor", "")
            j.hecho = objAnalisis.get("tipo_de_hecho", "")
            j.tipoRecurso = ia.getTipoRecurso(objAnalisis.get("tipo_de_recurso", 0))
            j.resultado = ia.getResultado(objAnalisis.get("resultado", 0))

            if j.update():

                j.delSumarios()
                sumarios = j.getSumarios(objAnalisis.get("sumarios", []))                                
                for sumario in sumarios:
                    j.saveSumario(sumario)

                if len(sumarios) == 0:
                    sumario = objAnalisis.get("sumarios", "")
                    if sumario != "":
                        j.saveSumario(sumario)

                j.delVoces(7352)
                voces = ia.getVoces(objAnalisis.get("voces", []))
                for voz in voces:
                    j.saveVoces(voz["ID"], voz["Faceta"])

                j.saveVoces(7670, 'ANALISIS.IA')

                normas = objAnalisis.get("legislacion_aplicada", [])
                for norma in normas:
                    lcon = ia.getLegislacion(norma)
                    if lcon:
                        text = f"IA - {norma}({lcon['Type']}:{lcon['Value']})"
                        j.saveLegislacion(lcon["GUID"], text)

                arrIdEntidades = ia.getMinistros(objAnalisis)
                for idEntidad in arrIdEntidades:
                    j.saveMinistro(idEntidad)

                print("[+] El fallo Id: {j.id}, ha sido registrado.")

            else:
                print("[!] El fallo Id: {j.id}, no ha podido ser registrado")
            j.updateFalloTerminado()
            elementCount += 1

        finProceso = str(datetime.today().strftime('%d/%m/%Y %H:%M:%S'))

        #Enviamos mail con el termino del proceso
        emailBody = Utils.getTemplateXML(configData)

        # Agregamos la información al email de notificacion
        date = str(datetime.today().strftime('%d/%m/%Y'))
        emailBody = emailBody.replace("[##Fecha##]", date)
        emailBody = emailBody.replace("[##Inicio##]", inicioProceso)
        emailBody = emailBody.replace("[##Fin##]", finProceso)
        emailBody = emailBody.replace("[##Procesados##]", str(elementCount))
        emailBody = emailBody.replace("[##Log##]", logFilePath)
        #Email.saveEmail(emailBody, tag, configData)

        print("::Archivos procesados: " + str(elementCount))
        print("::Termino Proceso: " + str(finProceso))

        return elementCount, logFilePath

    '''
    Método que permite bloquear la ejecucion del programa, de manera que solo 1 programa se ejecute a la vez
    '''
