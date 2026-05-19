# utils.py
# Funciones auxiliares para procesamiento de texto, chunking, etc.

def clean_text(text):
    """Limpia el texto eliminando espacios extra y saltos de línea innecesarios."""
    return " ".join(text.split())

# Puedes agregar aquí más funciones según lo necesites en el futuro.
