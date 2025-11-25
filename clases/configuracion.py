import json

class Configuracion:

    def getConfig(self):
        with open('C:\\Fallos\\py-labpen\\json\\config.json') as config_file:
            data = json.load(config_file)
        return data