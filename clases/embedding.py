import openai
from openai import AzureOpenAI
import requests
import json
import numpy as np
from clases.myproxies import MyProxies
import os 

class Embedding():

    def __init__(self):
        # === CONFIGURACIÓN DE CREDENCIALES ===
        self.workspace_id = "TrChileDocumO0KP"
        self.model_name = "text-embedding-3-large"
        self.asset_id = "208321"

        self.payload = {
            "workspace_id": self.workspace_id,
            "model_name": self.model_name
        }

        self.url = "https://aiplatform.gcs.int.thomsonreuters.com/v1/openai/token"
        self.OPENAI_BASE_URL = "https://eais2-use.int.thomsonreuters.com"

    def connect(self):
    
        
        os.environ["HTTP_PROXY"] = "webproxy.msp.cust.services:80"
        os.environ["HTTPS_PROXY"] = "webproxy.msp.cust.services:80"
    
        resp = requests.post(self.url, json=self.payload)
        credentials = json.loads(resp.content)

        if "openai_key" in credentials and "openai_endpoint" in credentials:
            OPENAI_API_KEY = credentials["openai_key"]
            OPENAI_DEPLOYMENT_ID = credentials["azure_deployment"]
            OPENAI_API_VERSION = credentials["openai_api_version"]
            token = credentials["token"]
            llm_profile_key = OPENAI_DEPLOYMENT_ID.split("/")[0]

            headers = {
                "Authorization": f"Bearer {credentials['token']}",
                "api-key": OPENAI_API_KEY,
                "Content-Type": "application/json",
                "x-tr-chat-profile-name": "ai-platforms-chatprofile-prod",
                "x-tr-userid": self.workspace_id,
                "x-tr-llm-profile-key": llm_profile_key,
                "x-tr-user-sensitivity": "true",
                "x-tr-sessionid": OPENAI_DEPLOYMENT_ID,
                "x-tr-asset-id": self.asset_id,
                "x-tr-authorization": self.OPENAI_BASE_URL
            }

            self.client = AzureOpenAI(
                azure_endpoint=self.OPENAI_BASE_URL,
                api_key=OPENAI_API_KEY,
                api_version=OPENAI_API_VERSION,
                azure_deployment=OPENAI_DEPLOYMENT_ID,
                default_headers=headers
            )
            return True
        else:
            return False


    '''
    '
    '''
    def flatten_json_for_embedding(self, data):
        parts = []
        for key, value in data.items():
            if isinstance(value, dict):
                parts.append(self.flatten_json_for_embedding(value))
            elif isinstance(value, list):
                parts.append(" ".join(str(v) if not isinstance(v, dict) else self.flatten_json_for_embedding(v) for v in value))
            else:
                parts.append(str(value))

        var = " ".join(parts)
        return var

    '''
    ' Metodo que crea los embedings para el fallos, a partir de todo el texto del fallo
    '''

    def getEmbeddings(self, fallo_json):
        # Asegúrate de pasar un diccionario limpio, no un objeto complejo
        texto_completo = self.flatten_json_for_embedding(fallo_json)

        max_reintentos = 10
        reintentos = 0

        while reintentos < max_reintentos:
            try:
                # Generar el embedding
                response = self.client.embeddings.create(
                    input=[texto_completo],
                    model=self.model_name,
                    dimensions=1536,
                    timeout=60
                )
                embedding_vector = response.data[0].embedding
                break  # Éxito, salir del bucle
            except Exception as e:
                reintentos += 1
                print(f"Error creando embedding (intento {reintentos} de {max_reintentos}): {e}")
                if reintentos == max_reintentos:
                    print("Se alcanzó el número máximo de reintentos.")
                    return None

        # Agregar al diccionario plano
        fallo_json["embedding_vector"] = embedding_vector

        return fallo_json

    def getEmbedding(self, texto):
        # Asegúrate de pasar un diccionario limpio, no un objeto complejo

        max_reintentos = 10
        reintentos = 0

        while reintentos < max_reintentos:
            try:
                # Generar el embedding
                response = self.client.embeddings.create(
                    input=[texto],
                    model=self.model_name,
                    dimensions=1536,
                    timeout=60
                )
                embedding_vector = response.data[0].embedding
                break  # Éxito, salir del bucle
            except Exception as e:
                reintentos += 1
                print(f"Error creando embedding (intento {reintentos} de {max_reintentos}): {e}")
                if reintentos == max_reintentos:
                    print("Se alcanzó el número máximo de reintentos.")
                    return None

        # Agregar al diccionario plano


        return embedding_vector