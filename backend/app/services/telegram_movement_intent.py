
import re
import unicodedata


def detectar_intencion_movimiento(texto: str) -> bool:
    """Detecta consultas sobre el ultimo movimiento registrado."""

    if not isinstance(texto, str):
        return False

    normalizado = unicodedata.normalize("NFD", texto.lower())
    normalizado = "".join(
        caracter
        for caracter in normalizado
        if unicodedata.category(caracter) != "Mn"
    )

    normalizado = re.sub(r"[^\w\s]", " ", normalizado)
    normalizado = re.sub(r"\s+", " ", normalizado).strip()

    if not normalizado or len(normalizado) > 300:
        return False

    # No confundir preguntas explicativas con consultas reales.
    if re.search(
        r"\b(como|explica|explicame|que es|que significa)\b",
        normalizado,
    ):
        return False


    
    patrones = (
        r"\bultimo movimiento\b",
        r"\bultimo\s+\w+\s+movimiento\b",
        r"\bmovimiento mas reciente\b",
        r"\bmovimiento mas nuevo\b",
        r"\bmovimiento reciente\b",
        r"\bmovimiento de inventario mas reciente\b",
    )



    return any(
        re.search(patron, normalizado)
        for patron in patrones
    )

