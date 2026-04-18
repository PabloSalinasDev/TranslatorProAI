import requests
from collections import OrderedDict

# ==========================================
# CACHE DE TRADUCCIONES (LRU)
# ==========================================

class CacheTraduccion:
    """
    Cache LRU (Least Recently Used) para traducciones.
    Evita llamadas repetidas a la API de Google Translate.
    """

    def __init__(self, max_size=100):
        """
        Inicializa el cache.
        """
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, key):
        """
        Obtiene traducción del cache.
        """
        if key in self.cache:
            self.cache.move_to_end(key)  # Marca como recientemente usado
            return self.cache[key]
        return None

    def set(self, key, value):
        """
        Guarda traducción en cache.
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # Si supera el límite, elimina el menos usado
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


# ==========================================
# GESTOR DE CONECTIVIDAD
# ==========================================


class GestorConectividad:
    """
    Gestiona la verificación de conectividad a internet.
    """

    @staticmethod
    def verificar_conexion(timeout=3):
        """
        Verifica si hay conexión a internet.
        """
        try:
            requests.get("https://www.google.com", timeout=timeout)
            return True
        except:
            return False

    @staticmethod
    def verificar_servicio(servicio, timeout=3):
        """
        Verifica servicios específicos de Google.
        """
        urls = {
            "translate": "https://translate.google.com",
            "speech": "https://speech.googleapis.com",
        }
        try:
            requests.get(urls.get(servicio, urls["translate"]), timeout=timeout)
            return True
        except:
            return False
