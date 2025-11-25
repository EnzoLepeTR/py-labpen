class MyProxies:

    """
        Metodo que contiene la configuración de los proxies
    """
    @staticmethod
    def getConfigHTTPS():
        proxies = {
            "https":"webproxy.msp.cust.services:80",
            "https":"webproxy.msp.corp.services:80",
            "https":"webproxy.msp.cust.services:80",
            "https":"webproxy.msp.mgmt.services:80",
            "https":"webproxy.msp.corp.services:80",
            "https":"webproxy.msp.cust.services:80"       
        }

        return proxies
        
    """
        Metodo que contiene la configuración de los proxies
    """
    @staticmethod        
    def getConfigHTTP():
        proxies = {
            "http":"webproxy.msp.cust.services:80",
            "http":"webproxy.msp.corp.services:80",
            "http":"webproxy.msp.cust.services:80",
            "http":"webproxy.msp.mgmt.services:80",
            "http":"webproxy.msp.corp.services:80",
            "http":"webproxy.msp.cust.services:80"       
        }

        return proxies        
    """
        Metodo que contiene la configuración de los proxies
    """
    @staticmethod        
    def getTimeout():
        return 600