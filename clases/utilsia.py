import shutil

import pyodbc
import requests
import json
import logging, sys
import msvcrt
import os
import glob
from subprocess import check_output

import shutil
import re
import regex
from os import path
from zipfile import ZipFile
from shutil import make_archive
from lxml import etree

from datetime import datetime
from clases.configuracion import Configuracion
from clases.utils import Utils


class UtilsIA:

    @staticmethod
    def getTipoRecursoResultadoText(value):

        # Parsear value
        '''
        Tipo de recurso: Recurso de casación en el fondo.
        Resultado: Rechazado.
        '''
        arrValues = str.lower(value).split("resultado:")
        if len(arrValues) == 2:

            # Tipo de Recurso
            strTipoRecurso = arrValues[0].strip()
            strTipoRecurso = strTipoRecurso.lower()
            arrTipoRecurso = strTipoRecurso.split(":")
            strTipoRecurso = arrTipoRecurso[1]
            strTipoRecurso = strTipoRecurso.replace(".", "").strip()

            # Resultado
            strResultado = arrValues[1].strip()
            strResultado = strResultado.replace(".", "")
            strResultado = strResultado.lower()

            return strTipoRecurso, strResultado
        else:
            return "", ""

    @staticmethod
    def getTipoRecurso(value):
        'recurso de protección'
        arrTipoRecurso = {
            "aclaración rectificación o enmienda"	        : 22,
            "actuación administrativa"						: 30,
            "amparo de aguas"								: 23,
            "recurso de casación en la forma y en el fondo"	: 20,
            "consulta"										: 12,
            "contienda de compentencia"					    : 16,
            "declaración de error judicial"				    : 27,
            "desafuero"									    : 19,
            "exequátur"									    : 11,
            "exhorto"										: 25,
            "extradición"									: 17,
            "nulidad de derecho público"					: 18,
            "queja disciplinaria"							: 29,
            "querella de capítulos"				    : 21,
            "reclamo de ilegalidad"				    : 15,
            "reclamo tributario"							: 32,
            "recurso de amparo"						: 7,
            "recurso de amparo de acceso a la información"  : 28,
            "recurso de amparo económico"					: 13,
            "recurso de apelación"							: 3,
            "recurso de casación en el fondo"				: 1,
            "recurso de casación en la forma"				: 2,
            "recurso de casación en la forma y apelación"	: 33,
            "recurso de hecho"								: 9,
            "recurso de inaplicabilidad"					: 8,
            "recurso de nulidad (proceso laboral)"			: 26,
            "recurso de nulidad (proceso penal)"			: 5,
            "recurso de protección"							: 4,
            "recurso de queja"								: 10,
            "recurso de reclamación"					    : 6,
            "recurso de revisión"							: 14,
            "recusación"									: 24,
            "unificación de jurisprudencia laboral"		    : 31,
            "extradición"                                   : 17,
            "recurso de unificación de jurisprudencia laboral": 31

        }
        try:
            return arrTipoRecurso[value]
        except:
            return 0

    '''
    '''
    @staticmethod
    def getResultado(value):

        # Parsear value
        '''
        Tipo de recurso: Recurso de casación en el fondo.
        Resultado: Rechazado.
        '''

        arrResultado = {
            "acogido"               : 1,
            "acogido parcimente"  : 11,
            "acogido-revoca"        : 8,
            "anula de oficio"       : 3,
            "confirma"              : 5,
            "desierto"              : 6,
            "desistido"             : 7,
            "inadmisible"           : 4,
            "incompetente"          : 10,
            "rechazado"             : 2,
            "rechazado y confirma"  : 12
        }

        try:
            return arrResultado[value]
        except:
            return 0

    '''

    '''
    @staticmethod
    def getMinistros(jsonMinistros, idFallo):

        arrIdEntidad = list()
        try:
            person_dict = json.loads(str.lower(jsonMinistros))

            ministros = person_dict['ministros']
            for ministro in ministros:
                # tempNombre = Utils.getOuterTextWithDelimiters(ministro, "(", ")")
                idMinistro = UtilsIA.getIdEntidad(ministro['apellidos'] + "," + ministro["nombres"], "Ministro")
                if idMinistro > 0:
                    arrIdEntidad.append(idMinistro)
                else:  # El ministro no existe, es necesario agregarlo
                    UtilsIA.guardarEntidad(ministro['apellidos'] + ", " + ministro["nombres"], "Ministro", idFallo,
                                           jsonMinistros)

            abogados = person_dict['abogados integrantes']
            for abogado in abogados:
                # tempNombre = Utils.getOuterTextWithDelimiters(abogado, "(", ")")
                idAbogado = UtilsIA.getIdEntidad(abogado['apellidos'] + "," + abogado["nombres"], "Abogado")
                if idAbogado > 0:
                    arrIdEntidad.append(idAbogado)
                else:  # El abogado no existe, es necesario agregarlo
                    UtilsIA.guardarEntidad(abogado['apellidos'] + "," + abogado["nombres"], "Abogado", idFallo, jsonMinistros)

            redactores = person_dict['redactores']
            if isinstance(redactores, list):
                for redactor in redactores:
                    if len(redactor.strip()) > 0:
                        # tempNombre = Utils.getOuterTextWithDelimiters(redactor, "(", ")")
                        idRedactor = UtilsIA.getIdEntidad(redactor['apellidos'] + "," + redactor["nombres"], "Redactor")
                        if idRedactor > 0:
                            arrIdEntidad.append(idRedactor)
                        else:  # El redactor no existe, es necesario agregarlo
                            UtilsIA.guardarEntidad(redactor['apellidos'] + "," + redactor["nombres"], "Redactor", idFallo,
                                                   jsonMinistros)
            else:
                if len(redactores.strip()) > 0:
                    # tempNombre = Utils.getOuterTextWithDelimiters(redactores, "(", ")")
                    idRedactor = UtilsIA.getIdEntidad(redactores['apellidos'] + "," + redactores["nombres"], "Redactor")
                    if idRedactor > 0:
                        arrIdEntidad.append(idRedactor)
                    else:  # El redactor no existe, es necesario agregarlo
                        UtilsIA.guardarEntidad(redactores['apellidos'] + "," + redactores["nombres"], "Redactor", idFallo,
                                               jsonMinistros)

        except Exception as exEstado:
            print("[!] Error en parser json: ", exEstado)

        return arrIdEntidad

    '''           
    '''
    @staticmethod
    def getIdEntidad(fullName, type):

        idEntidad = ""
        i = 0

        name = UtilsIA.getEntidadName(fullName)
        lastName = UtilsIA.getEntidadLastname(fullName)

        if name == "" or lastName == "":
            return 0

        config = Configuracion()
        cs = config.getConfig()

        query = f"""select id_ministro
                    from falministrossae 
                    where (NombreyApellido like '{name}%' or NombreyApellido like '%{name}%') and
                    ApellidoyNombre like '{lastName}%' and
                    estado = 1 and
                    tipo = '{type}';"""

        conection = pyodbc.connect(cs["PJCS"])
        try:
            cursor = conection.cursor()
            cursor.execute(query)

            for row in cursor.fetchall():
                idEntidad = row[0]
                i+= 1
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error en búsqueda de " + fullName + ": ", exEstado)
            return 0

        finally:
            try:
                conection.close()
            except:
                pass

        if i==1:
            return idEntidad
        else:
            return 0

    '''
    '''
    @staticmethod
    def setCuote(name):

        name = name.replace("á", "a")
        name = name.replace("é", "e")
        name = name.replace("í", "i")
        name = name.replace("ó", "o")
        name = name.replace("ú", "u")

        name = name.replace("Á", "A")
        name = name.replace("É", "E")
        name = name.replace("Í", "I")
        name = name.replace("Ó", "O")
        name = name.replace("Ú", "U")

        return name

    '''
     Olivares A., Luis Alberto 
    '''
    @staticmethod
    def getEntidadName(fullName):
        try:
            arrFullName = fullName.split(",")
            if len(arrFullName) == 2:
                name = arrFullName[1].strip()
                arrName = name.split(" ")
                return UtilsIA.setCuote(arrName[0])
            else:
                return ""
        except Exception as ex:
            print("[i] Error en el parser de nombre, ", ex)
            return ""

    '''
    Olivares A., Luis Alberto 
    '''
    @staticmethod
    def getEntidadLastname(fullName):

        try:
            arrFullName = fullName.split(",")
            if len(arrFullName) == 2:
                lastName = arrFullName[0].strip()
                index = lastName.find(" ")
                if index > -1:
                    return UtilsIA.setCuote(lastName[0: index + 2])
                else:
                    return "" #UtilsIA.setCuote(lastName)

            else:
                return ""
        except Exception as ex:
            print("[i] Error en el parser de apellidos, ", ex)
            return ""
    '''    
    '''
    @staticmethod
    def setJson(jsonMinistros):

        jsonMinistros = jsonMinistros.replace("Ministros", "ministros")
        jsonMinistros = jsonMinistros.replace("abogados_integrantes", "abogados integrantes")
        jsonMinistros = jsonMinistros.replace("Abogados", "abogados")
        jsonMinistros = jsonMinistros.replace("Integrantes", "integrantes")
        jsonMinistros = jsonMinistros.replace("Redactor", "redactor")

        return jsonMinistros

    '''
    '''
    @staticmethod
    def guardarEntidad(name, type, idFallo, jsonMinistros):


        config = Configuracion()
        cs = config.getConfig()

        query = f"""insert into nuevosMinistros(nombre, tipo, idfallo, json) values('{name}', '{type}', {idFallo}, '{jsonMinistros}');"""
        conection = pyodbc.connect(cs["PJCS"])
        try:
            cursor = conection.cursor()
            cursor.execute(query)
            cursor.commit()

            cursor.close()
            del cursor

        except Exception as ex:
            print(f"[i] Error al guardar la entidad {name}, y tipo {type}", ex)
            return ""

        finally:
            try:
                conection.close()
            except:
                pass

        return 0

    @staticmethod
    def getHecho(intTipoRecurso, intResultado):


        #1
        if intTipoRecurso==4 and intResultado==1:
            return  "Actor de deduce recurso de protección producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se acoge la acción de protección deducida."

        #2
        if intTipoRecurso==4 and intResultado==2:
            return  "Actor de deduce recurso de protección producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se rechaza la acción de protección deducida."

        #3
        if intTipoRecurso==26 and intResultado==1:
            return  "Actor deduce recurso de nulidad en contra de sentencia de primera instancia aludiendo las causales de nulidad establecidas en autos con respecto al proceso laboral desarrollado. Analizados los antecedentes la Corte acoge la nulidad deducida."

        #4
        if intTipoRecurso==26 and intResultado==2:
            return  "Actor deduce recurso de nulidad en contra de sentencia de primera instancia aludiendo las causales de nulidad establecidas en autos con respecto al proceso laboral desarrollado. Analizados los antecedentes la Corte rechaza la nulidad deducida."

        #5
        if intTipoRecurso==5 and intResultado==2:
            return  "Actor deduce recurso de nulidad en contra de sentencia de primera instancia aludiendo las causales de nulidad establecidas en autos con respecto al proceso penal desarrollado. Analizados los antecedentes la Corte rechaza la nulidad deducida."

        #6
        if intTipoRecurso==5 and intResultado==1:
            return  "Actor deduce recurso de nulidad en contra de sentencia de primera instancia aludiendo las causales de nulidad establecidas en autos con respecto al proceso penal desarrollado. Analizados los antecedentes la Corte acoge la nulidad deducida."

        #7
        if intTipoRecurso==3 and intResultado==5:
            return  "Actor se alza contra sentencia de primera instancia que le genero agravio. Analizados los antecedentes se confirma la sentencia apelada"

        #8
        if intTipoRecurso==3 and intResultado==2:
            return  "Actor se alza contra sentencia de primera instancia que le genero agravio. Analizados los antecedentes se rechaza la sentencia apelada"

        #9
        if intTipoRecurso==3 and intResultado==5:
            return  "Actor se alza contra sentencia de primera instancia que le genero agravio. Analizados los antecedentes se revoca la sentencia y acoge la pretensión deducida."

        #10
        if intTipoRecurso==11 and intResultado==1:
            return  "Se solicita exequatur necesario para cumplir en Chile la sentencia dictada en extranjero. Analizado lo expuesto, la Corte Suprema acoge el exequatur."

        #11
        if intTipoRecurso==11 and intResultado==2:
            return  "Se solicita exequatur necesario para cumplir en Chile la sentencia dictada en extranjero. Analizado lo expuesto, la Corte Suprema rechaza el exequatur."

        #12
        if intTipoRecurso==1 and intResultado==1:
            return  "Actor deduce recurso de casación en el fondo contra sentencia de Corte de Apelaciones. La Corte Suprema analizando los antecedentes esgrimidos en autos se acoge la casación deducida."

        #13
        if intTipoRecurso==1 and intResultado==2:
            return  "Actor deduce recurso de casación en el fondo contra sentencia de Corte de Apelaciones. La Corte Suprema analizando los antecedentes esgrimidos en autos rechaza la casación deducida."

        #14
        if intTipoRecurso==31 and intResultado==1:
            return  "Demandada interpone recurso de unificación de jurisprudencia contra la sentencia de la Corte de Apelaciones. La Corte Suprema acoge el recurso de unificación de jurisprudencia deducido."

        #15
        if intTipoRecurso==31 and intResultado==2:
            return  "Demandada interpone recurso de unificación de jurisprudencia contra la sentencia de la Corte de Apelaciones. La Corte Suprema rechaza el recurso de unificación de jurisprudencia deducido."

        #16
        if intTipoRecurso==10 and intResultado==1:
            return  "Reclamante interpone recurso de queja contra los jueces por las faltas y abusos cometidos en la dictación de la sentencia. La Corte analizados los antecedentes rechaza el recurso de queja deducido."

        #17
        if intTipoRecurso==10 and intResultado==2:
            return  "Demandada interpone recurso de unificación de jurisprudencia contra la sentencia de la Corte de Apelaciones. La Corte Suprema rechaza el recurso de unificación de jurisprudencia deducido."

        #18
        if intTipoRecurso==7 and intResultado==1:
            return  "Actor de deduce recurso de amparo producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se acoge la acción de amparo deducida."

        #19
        if intTipoRecurso==7 and intResultado==2:
            return  "Actor de deduce recurso de amparo producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se rechaza la acción de amparo deducida."

        #20
        if intTipoRecurso==13 and intResultado==1:
            return  "Actor de deduce recurso de amparo económico producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se acoge la acción de amparo deducida."

        #21
        if intTipoRecurso==13 and intResultado==2:
            return  "Actor de deduce recurso de amparo económico producto de vulneración de derechos constitucionales aludidos en autos. Analizados los antecedentes se rechaza la acción de amparo deducida."

        #22
        if intTipoRecurso==33 and intResultado==12:
            return  "Demandada recurre de casación en la forma y de apelación en contra de la sentencia definitiva. Analizado lo expuesto, la Corte de Apelaciones rechaza el recurso de casación y confirma."

        #23
        if intTipoRecurso==9 and intResultado==1:
            return  "Actor deduce recurso de hecho en contra resolución que declara inadmisible recuso de apelación deducido. Analizados los antecedentes se acoge el recurso de hecho y se declara admisible y se concede el recurso de apelación deducido."

        #24
        if intTipoRecurso==9 and intResultado==2:
            return  "Reclamante interpone recurso de hecho contra resolución que negó el recurso de apelación interpuesto. La Corte de Apelaciones rechaza el recurso de hecho deducido."

        #25
        if intTipoRecurso==15 and intResultado==1:
            return  "Actor interpone reclamo de ilegalidad en contra de la sentencia. Analizado lo expuesto, la Corte acoge la reclamación deducida."

        #26
        if intTipoRecurso==15 and intResultado==2:
            return  "Actor interpone reclamo de ilegalidad en contra de la sentencia. Analizado lo expuesto, la Corte se rechaza la reclamación deducida."

        #27
        if intTipoRecurso==6 and intResultado==1:
            return  "Actor deduce recurso de reclamación en contra de sentencia. La Corte analizando los antecedentes acoge recurso de reclamación deducido."

        #28
        if intTipoRecurso==6 and intResultado==2:
            return  "Actor deduce recurso de reclamación en contra de sentencia. La Corte analizando los antecedentes rechaza recurso de reclamación deducido."

        #29
        if intTipoRecurso==14 and intResultado==1:
            return  "Actor interpone acción de revisión de la sentencia dictada. La Corte Suprema acoge la acción de revisión deducida."

        #30
        if intTipoRecurso==14 and intResultado==2:
            return  "Actor interpone acción de revisión de la sentencia dictada. La Corte Suprema rechaza la acción de revisión deducida."

        #31
        if intTipoRecurso==17 and intResultado==1:
            return  "Actor solicita extradición de imputado de delito. Analizado lo expuesto, la Corte acoge la solicitud de extradición."

        #32
        if intTipoRecurso==17 and intResultado==2:
            return  "Actor solicita extradición de imputado de delito. Analizado lo expuesto, la Corte rechaza la solicitud de extradición."

        #33
        if intTipoRecurso==31 and intResultado==4:
            return  "Demandada interpone recurso de unificación de jurisprudencia contra la sentencia de la Corte de Apelaciones. La Corte Suprema declara inadmisible el recurso de unificación de jurisprudencia deducido."

        return ""

    @staticmethod
    def getVocesFromTag(tag, nVoces):

        config = Configuracion()
        cs = config.getConfig()
        arrVoces = list()

        query = f"""select top {nVoces} sv.id as id, sv.faceta as voz, s.faceta as faceta, (select count(*) from SAEVozRelacionada as svr where svr.id_voz = sv.id  group by id_voz) as cantidad 
                    from SAEVoces as sv, SAEVoces as s  
                    where sv.id_padre = {UtilsIA.getFacetaByTag(tag)} and  sv.id_padre = s.id  
                    order by cantidad desc"""

        conection = pyodbc.connect(cs["PJCS"])
        try:
            cursor = conection.cursor()
            cursor.execute(query)

            for row in cursor.fetchall():
                arrVoces.append(row[1])
            cursor.close()
            del cursor

        except Exception as exEstado:
            print("[!] Error en consulta de voces: ", exEstado)
            return 0

        finally:
            try:
                conection.close()
            except:
                pass

        return arrVoces

    @staticmethod
    def getFacetaByTag(tag):

        if tag == "ADM":
            return 1

        if tag == "AMP":
            return 7

        if tag == "CIV":
            return 5

        if tag == "LAB":
            return 15

        if tag == "MIN":
            return 4

        if tag == "NAV":
            return 16

        if tag == "PEN":
            return 19

        if tag == "POL":
            return 5

        if tag == "PRO":
            return 7

        if tag == "TRB":
            return 22

    @staticmethod
    def getVocesFromArr(arrVoces):

        sValues = ""
        for value in arrVoces:
            sValues += value + ","

        sValues = sValues.strip()
        if len(sValues)>0:
            return sValues[0:-1]
        else:
            return ""

    '''
    Metodo que convierte un arreglo con Voces en un string de terminos separados por coma
    '''
    @staticmethod
    def getVocesFromString(stringVoces):
        arrVocesTemp = stringVoces.split(",")
        arrVoces = list()
        for voz in arrVocesTemp:
            arrVoces.append(voz.strip())

        return arrVoces

    def extractLastNConsiderandos(text, n=4):
        # Usando la expresión regular que considera tanto formatos numéricos como escritos.

        '''
        pattern = (r'(?:DÉCIMO\s*(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO)?'
                   r'|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|UNDÉCIMO|DUODÉCIMO|\d+°?)\s*:\s*'
                   r'((?:.|\n)+?)(?=(?:DÉCIMO\s*(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO)?'
                   r'|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|UNDÉCIMO|DUODÉCIMO|\d+°?)\s*:|\d+|$)')
        '''

        pattern = (r'(?:(?:^|\s)DÉCIMO\s*(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO)?|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|UNDÉCIMO|DUODÉCIMO|^(?<!art\.?\s|\bartículo\s)\d+°?)\s*:\s*(?:.|\n)+?(?=(?:DÉCIMO\s*(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO)?|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|UNDÉCIMO|DUODÉCIMO|^(?<!art\.?\s|\bartículo\s)\d+°?)\s*:|$)')

        matches = regex.findall(pattern, text, flags = re.IGNORECASE)
        # Agrupar el texto del arreglo arrTitleText separado por \r\n en la variable
        arrTitleText = matches[-n:]
        titleText = ''
        i = 0
        for temporalText in arrTitleText:
            if(i < 3):
                titleText+= temporalText.strip() + " "
            else:
                arrText = temporalText.split("\n")
                if len(arrText) > 1:
                    titleText+= arrText[0]
                else:
                    titleText += temporalText.strip()
            i+= 1

        return  titleText


    '''
    '''
    @staticmethod
    def getIAQuery(query, configData):

        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + configData["OPENArena-API_KEY"]
        }

        # Cuerpo de la solicitud
        body = {
            "query": query,
            "workflow_id": "8556ba87-acf8-4049-98a3-fc62a300656c",
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        response = requests.post(
            f"{configData['OPENArena-URL']}/v1/inference",
            headers=headers,
            data=json.dumps(body)
        )

        # Convertir el JSON string a un diccionario
        data = response.json()
        answer = ""
        try:
            # Acceder al campo 'result' de manera segura
            result = data.get('result', None)
            if result:
                # Si 'result' existe, accedemos a sus subcampos
                user_input = result.get('user_input', 'No user input found')
                answer = result.get('answer', {}).get('openai_gpt-4o', 'No answer found')
                output_type = result.get('output_type', 'No output type found')

                # Imprimir los valores
                #print(f"User Input: {user_input}")
                #print(f"Answer: {answer}")
                #print(f"Output Type: {output_type}")
            else:
                print("No result found in the JSON data.")
        except Exception as e:
            print(f"An error occurred: {e}")

        return answer












