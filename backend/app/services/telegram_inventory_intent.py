import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class IntencionInventario:
    tipo: str
    busqueda: str = ""


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"\s+", " ", texto).strip()


def detectar_intencion_inventario(
    texto: str,
) -> IntencionInventario | None:
    """Identifica preguntas de inventario sin generar datos."""

    if not isinstance(texto, str):
        return None

    texto = _normalizar(texto)

    if not texto or len(texto) > 300:
        return None

    if texto.startswith("/"):
        return None

    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    patrones_lista = (
        r"(?:dime|muestra|muestrame|mostrar|lista|listar|ver)"
        r"\s+(?:(?:que|cuales|los)\s+)?medicamentos"
        r"(?:\s+(?:tenemos|disponibles|en existencia))?",
        r"(?:que|cuales)\s+medicamentos\s+(?:tenemos|hay)",
    )

    for patron in patrones_lista:
        if re.fullmatch(patron, texto):
            return IntencionInventario(tipo="listar")

    
    patrones_busqueda = (
        r"(?:cuanto|cuantos|cuantas)"
        r"(?:\s+(?:unidades|cajas|piezas))?"
        r"\s+(?:de\s+)?(.+?)"
        r"\s+(?:tenemos|quedan|hay|disponibles)",

        r"(?:hay|tenemos)\s+(.+?)\s+disponible",

        r"(?:existencias|stock|inventario)\s+de\s+(.+)",

        # Nuevas preguntas naturales
        r"(?:tenemos|hay)\s+(.+)",

        r"(?:tienen|queda|quedan)\s+(.+)",

        r"(?:esta|se encuentra)\s+(.+?)\s+disponible",
    )


    for patron in patrones_busqueda:
        coincidencia = re.fullmatch(patron, texto)

        if coincidencia:
            medicamento = coincidencia.group(1).strip()
            medicamento = re.sub(
                r"^(?:medicamento|medicamentos|de)\s+",
                "",
                medicamento,
            )

            if medicamento:
                return IntencionInventario(
                    tipo="buscar",
                    busqueda=medicamento,
                )

    return None
