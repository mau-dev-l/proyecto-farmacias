
from langchain_core.messages import HumanMessage, SystemMessage

from telegram.ai.llm import obtener_modelo
from telegram.ai.tools import consultar_stock


def responder_stock(medicamento: str, sucursal_id: int) -> str:
    """Genera una respuesta usando existencias reales del inventario."""

    datos = consultar_stock(medicamento, sucursal_id)

    modelo = obtener_modelo()

    mensajes = [
        SystemMessage(
            content=(
                "Eres un asistente de inventario farmacéutico. "
                "Responde en español, de manera breve y clara. "
                "Utiliza únicamente los datos proporcionados. "
                "No inventes cantidades, medicamentos ni sucursales. "
                "Si no hay existencias disponibles, indícalo. "
                "No proporciones recomendaciones médicas."
            )
        ),
        HumanMessage(
            content=(
                f"Pregunta: ¿Cuántas unidades disponibles hay de {medicamento}?\n"
                f"Datos del inventario: {datos}"
            )
        ),
    ]

    respuesta = modelo.invoke(mensajes)

    return str(respuesta.content)





def responder_documentacion(pregunta: str) -> str:
    """Responde preguntas sobre el sistema utilizando RAG."""
    from telegram.ai.rag import responder_con_rag

    return responder_con_rag(pregunta)





if __name__ == "__main__":
    print("Consultando el inventario con inteligencia artificial...")
    print(responder_stock("Paracetamol", 1))




def clasificar_pregunta(pregunta: str) -> str:
    """Identifica si una pregunta corresponde a STOCK o RAG."""
    from langchain_core.messages import HumanMessage, SystemMessage

    if not pregunta.strip():
        return "DESCONOCIDO"

    modelo = obtener_modelo()

    mensajes = [
        SystemMessage(
            content=(
                "Clasifica preguntas de un sistema de inventario farmacéutico. "
                "Responde exclusivamente con una palabra: STOCK, RAG o DESCONOCIDO. "
                "STOCK: preguntas sobre cantidades disponibles, existencias "
                "o disponibilidad de medicamentos en el inventario. "
                "RAG: preguntas sobre procedimientos, manuales, funcionamiento "
                "del sistema, caducidades o método PEPS. "
                "DESCONOCIDO: preguntas que no correspondan a esas categorías. "
                "No respondas la pregunta del usuario. Solo clasifícala."
            )
        ),
        HumanMessage(content=pregunta),
    ]

    respuesta = modelo.invoke(mensajes)
    clasificacion = str(respuesta.content).strip().upper()

    if clasificacion in {"STOCK", "RAG", "DESCONOCIDO"}:
        return clasificacion

    return "DESCONOCIDO"



def responder_pregunta(
    pregunta: str,
    sucursal_id: int,
    medicamento: str | None = None,
) -> str:
    """Dirige una pregunta a la herramienta correspondiente."""

    if not pregunta.strip():
        return "Por favor, escribe una pregunta."

    tipo = clasificar_pregunta(pregunta)

    if tipo == "RAG":
        return responder_documentacion(pregunta)

    if tipo == "STOCK":
        if not medicamento or not medicamento.strip():
            return (
                "Para consultar existencias, necesito identificar "
                "el medicamento. Indica su nombre."
            )

        return responder_stock(medicamento, sucursal_id)

    return (
        "Puedo ayudarte a consultar existencias de medicamentos "
        "o responder preguntas sobre los procedimientos "
        "del sistema de farmacia."
    )
