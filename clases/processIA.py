import json
import requests
from clases.configuracion import Configuracion
from sentence_transformers import SentenceTransformer, util
from clases.utils import Utils
from clases.utilsia import UtilsIA
from clases.myproxies import MyProxies
import pandas as pd
import editdistance
import pyodbc

class ProcessIA(Configuracion):

    def __init__(self):
        self.url = "https://aiopenarena.gcs.int.thomsonreuters.com"
        self.data = self.getConfig()
        self.token = self.data["OPENArena-API_KEY"]
        self.agenteId = self.data.get("Analize", {}).get("OpenArenaAgenteId")

    '''
    '''
    def getSumario(self, textoSentencia):

        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + self.token
        }

        # Cuerpo de la solicitud
        body = {
            "query": "Eres un abogado chileno, Podrias proporcionarme un sumario para este documento: \"" + textoSentencia + "\", quisiera que no superara los 1000 caracteres, y por favor responde solo el texto, sin comillas ni la palabra sumario?",
            "workflow_id": self.agenteId,
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        #response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body), proxies=MyProxies.getConfigHTTPS())
        response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body))

        # Convertir el JSON string a un diccionario
        data = response.json()
        answer = ""
        try:
            # Acceder al campo 'result' de manera segura
            result = data.get('result', None)
            if result:
                # Si 'result' existe, accedemos a sus subcampos
                user_input = result.get('user_input', 'No user input found')
                answer = result.get('answer', {}).get('openai_gpt-41', 'No answer found')
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

    '''
    '''
    def getTituloDescriptor(self, textoSentencia):

        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + self.token
        }

        # Cuerpo de la solicitud
        body = {
            "query": "Eres un abogado chileno, Podrias proporcionarme un titulo descriptor para este documento: \"" + textoSentencia + "\", quisiera que no superara los 300 caracteres, y por favor responde solo el texto, sin texto como titulo: o titulo descriptivo y sin comillas, solo el texto?",
            "workflow_id": self.agenteId,
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body), proxies=MyProxies.getConfigHTTPS())
        #response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body))

        # Convertir el JSON string a un diccionario
        data = response.json()
        answer = ""
        try:
            # Acceder al campo 'result' de manera segura
            result = data.get('result', None)
            if result:
                # Si 'result' existe, accedemos a sus subcampos
                user_input = result.get('user_input', 'No user input found')
                answer = result.get('answer', {}).get('openai_gpt-41', 'No answer found')
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

    '''
    '''
    def getAnalisis(self, textoSentencia):

        textoSentencia = textoSentencia.replace('"', '-')
        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + self.token
        }

        # Cuerpo de la solicitud
        body = {
            "query": "Por favor analisa el siguiente texto, el sumario por favor entrgalo siempre como un string, JAMAS como un arreglo, este es el texto: " + textoSentencia ,
            "workflow_id": self.agenteId,
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        response = requests.post(f"{self.url}/v1/inference",
                                 headers=headers,
                                 data=json.dumps(body),
                                 #proxies=MyProxies.getConfigHTTPS()
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
                answer = result.get('answer', {}).get('openai_gpt-41', 'No answer found')
                #answer = result.get('answer', {}).get('vertexai_gemini-1.5-pro', 'No answer found')
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

        '''
    '''
    
    '''
    '''
    def getAnalisisJad(self, textoSentencia):

        textoSentencia = textoSentencia.replace('"', '-')
        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + self.token
        }

        # Cuerpo de la solicitud
        body = {
            "query": "Por favor analisa el siguiente texto, el sumario por favor entrgalo siempre como un string, JAMAS como un arreglo, este es el texto: " + textoSentencia ,
            "workflow_id": self.agenteId,
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body), proxies=MyProxies.getConfigHTTPS())
        #response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body))

        # Convertir el JSON string a un diccionario
        data = response.json()
        answer = ""
        try:
            # Acceder al campo 'result' de manera segura
            result = data.get('result', None)
            if result:
                # Si 'result' existe, accedemos a sus subcampos
                user_input = result.get('user_input', 'No user input found')
                answer = result.get('answer', {}).get('openai_gpt-41', 'No answer found')
                #answer = result.get('answer', {}).get('vertexai_gemini-1.5-pro', 'No answer found')
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

    '''
    '''
    def getTerminos(self, textoSentencia):

        # Headers de la solicitud
        headers = {
            "Authorization": f"Bearer " + self.token
        }

        # Cuerpo de la solicitud
        body = {
            "query": "Podrias proporcionarme 5 terminos para este documento: \"" + textoSentencia + "\", podrias entregarmelos separados por coma, sin ningun tipo de explicacion ni respuesta, solo los terminos?",
            "workflow_id": self.agenteId,
            "is_persistence_allowed": False
        }

        # Realizar la solicitud POST
        response = requests.post(f"{self.url}/v1/inference",headers=headers,data=json.dumps(body), proxies=MyProxies.getConfigHTTPS())
        #response = requests.post(f"{self.url}/v1/inference", headers=headers, data=json.dumps(body))

        # Convertir el JSON string a un diccionario
        data = response.json()
        answer = ""
        try:
            # Acceder al campo 'result' de manera segura
            result = data.get('result', None)
            if result:
                # Si 'result' existe, accedemos a sus subcampos
                user_input = result.get('user_input', 'No user input found')
                answer = result.get('answer', {}).get('openai_gpt-41', 'No answer found')
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

    '''
    '''
    def setModelVoces(self):

        xlsxVoces = self.data.get("Analize", {}).get("xlsxVoces")    

        # Cargamos los datos del modelo
        # Leer el archivo Excel
        filePath = xlsxVoces

        # Leer sólo "Hoja2" del archivo Excel
        dataHojaVoces = pd.read_excel(filePath, sheet_name="voces", engine='openpyxl')

        # Cargar el modelo preentrenado
        # self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')        
        model_path = self.data.get("Analize", {}).get("ModelPath") 

        # Cargar el modelo desde la ruta local
        self.model = SentenceTransformer(model_path)

        # conjunto de palabras
        self.ids_b_voces = dataHojaVoces["ID"]
        self.terms_b_voces = dataHojaVoces["FACETA"]

        # Convertir términos a embeddings
        self.embeddings_b_voces = self.model.encode(self.terms_b_voces, convert_to_tensor=True)

    '''
    '''
    def setModelLegislacion(self):
        '''-----------------------------------------------------------------------------'''
        # Cargamos los datos del modelo
        # Leer el archivo Excel        
        filePath = self.data.get("Analize", {}).get("xlsxLegislacion")  

        # Leer sólo "Hoja2" del archivo Excel
        dataHojaVoces = pd.read_excel(filePath, sheet_name="lcon", engine='openpyxl')

        model_path = self.data.get("Analize", {}).get("ModelPath")  

        # Cargar el modelo desde la ruta local
        self.model = SentenceTransformer(model_path)

        # conjunto de palabras
        self.ids_b_lcon = dataHojaVoces["GUID"]
        self.terms_b_lcon = dataHojaVoces["Norma"]

        # Convertir términos a embeddings
        self.embeddings_b_lcon = self.model.encode(self.terms_b_lcon, convert_to_tensor=True)

    '''
    '''
    def setModelMinistros(self):
        '''-----------------------------------------------------------------------------'''
        # Cargamos los datos del modelo
        # Leer el archivo Excel
        filePath = self.data.get("Analize", {}).get("xlsxMinistros")

        # Leer sólo "Hoja2" del archivo Excel
        dataHojaVoces = pd.read_excel(filePath, sheet_name="ministros", engine='openpyxl')

        model_path = self.data.get("Analize", {}).get("ModelPath")

        # Cargar el modelo desde la ruta local
        self.model = SentenceTransformer(model_path)

        # conjunto de palabras
        self.ids_b_ministros = dataHojaVoces["id"]
        self.terms_b_ministros = dataHojaVoces["nombre"]

    '''
    '''
    def setModelRelatores(self):
        '''-----------------------------------------------------------------------------'''
        # Cargamos los datos del modelo
        # Leer el archivo Excel
        filePath = self.data.get("Analize", {}).get("xlsxRelatores")

        # Leer sólo "Hoja2" del archivo Excel
        dataHojaVoces = pd.read_excel(filePath, sheet_name="relatores", engine='openpyxl')

        model_path = self.data.get("Analize", {}).get("ModelPath")

        # Cargar el modelo desde la ruta local
        self.model = SentenceTransformer(model_path)

        # conjunto de palabras
        self.ids_b_relatores = dataHojaVoces["id"]
        self.terms_b_relatores = dataHojaVoces["nombre"]

    '''
    '''
    def setModelAbogados(self):
        '''-----------------------------------------------------------------------------'''
        # Cargamos los datos del modelo
        # Leer el archivo Excel
        filePath = self.data.get("Analize", {}).get("xlsxAbogados")

        # Leer sólo "Hoja2" del archivo Excel
        dataHojaVoces = pd.read_excel(filePath, sheet_name="abogados", engine='openpyxl')

        model_path = self.data.get("Analize", {}).get("ModelPath")

        # Cargar el modelo desde la ruta local
        self.model = SentenceTransformer(model_path)

        # conjunto de palabras
        self.ids_b_abogados = dataHojaVoces["id"]
        self.terms_b_abogados = dataHojaVoces["nombre"]

    '''
    '''
    def getVoces(self, terms_a):

        # Convertir términos a embeddings
        embeddings_a = self.model.encode(terms_a, convert_to_tensor=True)

        # Calcular la similitud semántica entre los términos
        arrVoces = list()

        for i, term_a in enumerate(terms_a):
            arr = list()
            for j, term in enumerate(self.terms_b_voces):
                similarity = util.pytorch_cos_sim(embeddings_a[i], self.embeddings_b_voces[j])

                # Asumiendo que tienes una lista de IDs en paralelo a `self.terms_b` llamada `self.ids_b`
                dic = {"ID": self.ids_b_voces[j], "Faceta": term, "Value": similarity.item()}
                arr.append(dic)

            # Ordenar los resultados por similitud
            sorted_data_desc = sorted(arr, key=lambda x: x['Value'], reverse=True)
            bestItem = sorted_data_desc[0]

            # Comparar con la ponderación mínima
            if bestItem["Value"] > self.data.get("Analize", {}).get("ponderacionVoces"):
                faceta_id = {"ID": bestItem["ID"], "Faceta": bestItem["Faceta"]}
                arrVoces.append(faceta_id)

        return arrVoces  # Devuelve una lista de diccionarios con "ID" y "Faceta"


    '''
    SELECT 
    id,
        CONCAT(
            'Articulo N° ', articulo, ', ',
            tiponorma, ' ',
            COALESCE(numero, ''), ', ',
            emisor
        ) AS descripcion
    FROM 
        lconguid
    WHERE 
        articulo IS NOT NULL and id is not null and fechavigenciafinal = '31-DEC-99'
    '''
    def getLegislacion(self, norma):

        norma = norma.replace("°", "")
        embedding_a = self.model.encode(norma, convert_to_tensor=True)

        # Primera capa: Filtro estricto con Levenshtein (para nombres exactos)
        tempTermA = Utils.normalizeText(norma)
        tempTermA = tempTermA.replace("supremo", "")
        exact_matches = []

        for j, term in enumerate(self.terms_b_lcon):
            tempTerm = Utils.normalizeText(term)
            distance = editdistance.eval(tempTermA, tempTerm)
            length = max(len(tempTermA), len(tempTerm))
            similarity_ratio = 1 - (distance / length)

            if similarity_ratio > 0.95:  # Ajusta este umbral
                exact_matches.append({
                    "GUID": self.ids_b_lcon[j],
                    "Norma": term,
                    "Value": similarity_ratio,
                    "Type": "exact"
                })

        if exact_matches:
            exact_matches_sorted = sorted(exact_matches, key=lambda x: x['Value'], reverse=True)
            best_exact = exact_matches_sorted[0]
            #arrLcon.append({"GUID": best_exact["GUID"], "Norma": best_exact["Norma"]})
            return best_exact

        # Segunda capa: Si no hay coincidencia exacta, usar embeddings semánticos
        semantic_candidates = []
        for j in range(len(self.terms_b_lcon)):
            similarity = util.pytorch_cos_sim(embedding_a, self.embeddings_b_lcon[j])

            if similarity > 0.90:  # Umbral más bajo para semántica
                semantic_candidates.append({
                    "GUID": self.ids_b_lcon[j],
                    "Norma": self.terms_b_lcon[j],
                    "Value": similarity.item(),
                    "Type": "semantic"
                })

        if semantic_candidates:
            semantic_candidates_order = sorted(semantic_candidates, key=lambda x: x['Value'], reverse=True)
            best_semantic = semantic_candidates_order[0]
            if best_semantic['Value'] > self.data.get("Analize", {}).get("ponderacionLegislacion"):  # Umbral alto para semántica
                #arrLcon.append({"GUID": best_semantic["GUID"], "Norma": best_semantic["Norma"]})
                return best_semantic

        return None


    '''
    select id_ministro, apellidoynombre from falMinistrosSAE where estado = 1 and tipo = 'Abogado'
    '''
    def getMinistros(self, term_a):
        tempTermA = Utils.normalizeText(term_a)
        arr = list()
        for j, term in enumerate(self.terms_b_ministros):
            # Calcular la similitud de Jaccard en lugar de la similitud coseno
            tempTermB = Utils.normalizeText(term)
            similarity = Utils.combinedSimilarity(tempTermA, tempTermB)

            # Crear el diccionario de resultados
            dic = {"ID": self.ids_b_voces[j], "Nombre": term, "Value": similarity}
            arr.append(dic)

        # Ordenar los resultados por similitud
        sorted_data_desc = sorted(arr, key=lambda x: x['Value'], reverse=True)
        bestItem = sorted_data_desc[0]

        # Comparar con la ponderación mínima
        if bestItem["Value"] > self.data.get("Analize", {}).get("ponderacionMinistros"):
            return bestItem
        else:
            return None

    def getRelatores(self, term_a):
        tempTermA = Utils.normalizeText(term_a)
        arr = list()
        for j, term in enumerate(self.terms_b_relatores):
            # Calcular la similitud de Jaccard en lugar de la similitud coseno
            tempTermB = Utils.normalizeText(term)
            similarity = Utils.combinedSimilarity(tempTermA, tempTermB)

            # Crear el diccionario de resultados
            dic = {"ID": self.ids_b_voces[j], "Nombre": term, "Value": similarity}
            arr.append(dic)

        # Ordenar los resultados por similitud
        sorted_data_desc = sorted(arr, key=lambda x: x['Value'], reverse=True)
        bestItem = sorted_data_desc[0]

        # Comparar con la ponderación mínima
        if bestItem["Value"] > self.data.get("Analize", {}).get("ponderacionRelatores"): 
            return bestItem
        else:
            return None

    def getAbogados(self, term_a):
        tempTermA = Utils.normalizeText(term_a)
        arr = list()
        for j, term in enumerate(self.terms_b_abogados):
            # Calcular la similitud de Jaccard en lugar de la similitud coseno
            tempTermB = Utils.normalizeText(term)
            similarity = Utils.combinedSimilarity(tempTermA, tempTermB)

            # Crear el diccionario de resultados
            dic = {"ID": self.ids_b_voces[j], "Nombre": term, "Value": similarity}
            arr.append(dic)

        # Ordenar los resultados por similitud
        sorted_data_desc = sorted(arr, key=lambda x: x['Value'], reverse=True)
        bestItem = sorted_data_desc[0]

        # Comparar con la ponderación mínima
        if bestItem["Value"] > self.data.get("Analize", {}).get("ponderacionAbogados"):
            return bestItem
        else:
            return None

    def getMinistros(self, term_a):
        tempTermA = Utils.normalizeText(term_a)
        arr = list()
        for j, term in enumerate(self.terms_b_ministros):
            # Calcular la similitud de Jaccard en lugar de la similitud coseno
            tempTermB = Utils.normalizeText(term)
            similarity = Utils.combinedSimilarity(tempTermA, tempTermB)

            # Crear el diccionario de resultados
            dic = {"ID": self.ids_b_voces[j], "Nombre": term, "Value": similarity}
            arr.append(dic)

        # Ordenar los resultados por similitud
        sorted_data_desc = sorted(arr, key=lambda x: x['Value'], reverse=True)
        bestItem = sorted_data_desc[0]

        # Comparar con la ponderación mínima
        if bestItem["Value"] > self.data.get("Analize", {}).get("ponderacionMinistros"):
            return bestItem
        else:
            return None

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

    @staticmethod
    def getEntidadName(fullName):
        try:
            arrFullName = fullName.split(",")
            if len(arrFullName) == 2:
                name = arrFullName[1].strip()
                arrName = name.split(" ")
                return Utils.setCuote(arrName[0])
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
                    return Utils.setCuote(lastName[0: index + 2])
                else:
                    return "" #UtilsIA.setCuote(lastName)

            else:
                return ""
        except Exception as ex:
            print("[i] Error en el parser de apellidos, ", ex)
            return ""

    @staticmethod
    def getIdEntidad(fullName, type):

        idEntidad = ""
        i = 0

        name = IA.getEntidadName(fullName)
        lastName = IA.getEntidadLastname(fullName)

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
                i += 1
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

        if i == 1:
            return idEntidad
        else:
            return 0

    @staticmethod
    def getMinistros(objAnalisis):

        arrIdEntidad = list()
        try:

            ministros = objAnalisis.get("ministros", [])
            for ministro in ministros:
                idMinistro = UtilsIA.getIdEntidad(ministro, "Ministro")
                if idMinistro > 0:
                    arrIdEntidad.append(idMinistro)

            abogados = objAnalisis.get("abogado_integrante", [])
            for abogado in abogados:
                # tempNombre = Utils.getOuterTextWithDelimiters(abogado, "(", ")")
                idAbogado = UtilsIA.getIdEntidad(abogado, "Abogado")
                if idAbogado > 0:
                    arrIdEntidad.append(idAbogado)

            redactores = objAnalisis.get("redactor", [])
            if isinstance(redactores, list):
                for redactor in redactores:
                    if len(redactor.strip()) > 0:
                        # tempNombre = Utils.getOuterTextWithDelimiters(redactor, "(", ")")
                        idRedactor = UtilsIA.getIdEntidad(redactor, "Redactor")
                        if idRedactor > 0:
                            arrIdEntidad.append(idRedactor)
            else:
                if len(redactores.strip()) > 0:
                    # tempNombre = Utils.getOuterTextWithDelimiters(redactores, "(", ")")
                    idRedactor = UtilsIA.getIdEntidad(redactores, "Redactor")
                    if idRedactor > 0:
                        arrIdEntidad.append(idRedactor)

        except Exception as exEstado:
            print("[!] Error en parser json: ", exEstado)


        return arrIdEntidad