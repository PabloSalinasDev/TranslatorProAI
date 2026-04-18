from deep_translator import GoogleTranslator
from utils import CacheTraduccion
import textwrap
import re
import logging

class MotorTraduccion:
    """
    Motor de traducción con cache integrado.
    Usa Google Translate API a través de deep-translator.
    """

    def __init__(self):
        self.cache = CacheTraduccion()

    @staticmethod
    def dividir_texto(texto, max_char=800):
        """
        Divide texto largo respetando puntuación primero, y usando
        textwrap para fragmentos rebeldes (muy largos sin puntos).
        """
        # 1.Dividir por puntos o saltos de línea.
        partes = re.split(r"(?<=[.])\s+|(?<=\n)", texto)
        resultado = []

        for p in partes:
            p = p.strip()
            if not p:
                continue

            # Si el fragmento (oración) cabe en el límite, se deja tal cual
            if len(p) <= max_char:
                resultado.append(p)
            else:
                # Si la oración es gigante (más de 800 chars sin puntos),
                # textwrap la recorta limpiamente.

                # width=max_char: El ancho máximo permitido
                # break_long_words=False: No cortar palabras a la mitad si es posible
                fragmentos = textwrap.wrap(p, width=max_char, break_long_words=False)

                # Se extiende la lista de resultados con estos nuevos sub-fragmentos
                resultado.extend(fragmentos)

        return resultado

    def traducir(self, texto, idioma_destino):
        """
        Traduce detectando automáticamente el idioma de origen.
        """
        cache_key = f"{idioma_destino}:{texto[:100]}"

        # Buscar en cache primero
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            traductor = GoogleTranslator(source="auto", target=idioma_destino)
            texto_traducido = traductor.translate(texto)

            # Se guarda el resultado y el destino usado
            resultado = (texto_traducido, idioma_destino)
            self.cache.set(cache_key, resultado)

            return resultado
        except Exception as e:
            logging.error(f"Error traducción: {e}")
            raise Exception("Error de conexión - Verifica tu internet")