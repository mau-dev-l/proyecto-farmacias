
from langchain_ollama import ChatOllama

# Modelo de inteligencia artificial instalado en Ollama.
MODEL_NAME = "llama3.2:3b"


def obtener_modelo():
    """Crea la conexión entre LangChain y Ollama."""
    return ChatOllama(
        model=MODEL_NAME,
        base_url="http://localhost:11434",
        temperature=0,
    )


def preguntar_ia(pregunta: str) -> str:
    """Envía una pregunta al modelo y devuelve su respuesta."""
    modelo = obtener_modelo()
    respuesta = modelo.invoke(pregunta)
    return str(respuesta.content)


if __name__ == "__main__":
    pregunta = "¿Qué es el control de caducidades en una farmacia? Responde brevemente en español."

    print("Consultando a Ollama...")
    print(preguntar_ia(pregunta))
