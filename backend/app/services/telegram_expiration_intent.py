
import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class IntencionCaducidad:
    dias: int


def detectar_intencion_caducidad(
    texto: str,
) -> IntencionCaducidad | None:
    """Detecta consultas sobre caducidades reales."""

    if not isinstance(texto, str):
        return None

    normalizado = unicodedata.normalize("NFKD", texto)
    normalizado = "".join(
        caracter
        for caracter in normalizado
        if not unicodedata.combining(caracter)
    ).lower()

    # Evitar confundir preguntas de documentación
    # con solicitudes de datos reales.
    if re.search(
        r"\b(como funciona|como se calcula|"
        r"como generar|como crear|explica|"
        r"que significa|que es)\b",
        normalizado,
    ):
        return None

    patrones = (
        r"\bvenc(?:e|en|er|imiento|imientos)\b",
        r"\bcaduc(?:a|an|ar|idad|idades)\b",
        r"\bproxim(?:o|os|a|as|ante|amente)\b",
        r"\bpor vencer\b",
    )

    if not any(
        re.search(patron, normalizado)
        for patron in patrones
    ):
        return None

    # Identificar un plazo solicitado por el usuario.
    coincidencia = re.search(
        r"\b(?:en|dentro de|proximos?)\s+"
        r"(\d{1,3})\s+dias?\b",
        normalizado,
    )

    dias = int(coincidencia.group(1)) if coincidencia else 30

    if dias > 365:
        return None

    return IntencionCaducidad(dias=dias)
