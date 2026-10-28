"""Búsqueda de objetos en un inventario (Excel con columnas "Objeto" y "Lugar").

Lo comparten el chat de consola (`cli.py`) y el bot de Telegram (`telegram_bot.py`).
"""

import re
import unicodedata
from typing import List, NamedTuple, Optional

import openpyxl

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "lo", "al", "del", "de",
    "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
    "aquel", "aquella", "aquellos", "aquellas",
}

HELP_TEXT = "Prueba con: '¿Dónde está el martillo?', '¿Dónde están las pilas?' o 'buscar destornillador'."


class Item(NamedTuple):
    objeto: str
    lugar: str


class SearchResult(NamedTuple):
    kind: str  # "exact" | "partial" (todas las palabras) | "related" (alguna palabra) | "none"
    items: List[Item]


def normalize(text: str) -> str:
    """Minúsculas y sin tildes: 'Cámara' -> 'camara'."""
    decomposed = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def clean_query(text: str) -> str:
    """Quita signos de puntuación y artículos: '¿Dónde está el martillo?' -> 'donde esta martillo'."""
    words = re.sub(r"[^\w\s]", " ", normalize(text)).split()
    return " ".join(w for w in words if w not in STOPWORDS)


def load_inventory(path) -> List[Item]:
    """Lee la primera hoja: columna A = objeto, columna B = lugar (la fila 1 es la cabecera)."""
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        items = []
        for row in workbook.active.iter_rows(min_row=2, max_col=2, values_only=True):
            objeto = row[0] if len(row) > 0 else None
            lugar = row[1] if len(row) > 1 else None
            if objeto is None or not str(objeto).strip():
                continue
            items.append(Item(str(objeto).strip(), str(lugar).strip() if lugar else "sin ubicación"))
        return items
    finally:
        workbook.close()


def _unique(items):
    return list(dict.fromkeys(items))


def search(items: List[Item], query: str) -> SearchResult:
    """Coincidencia exacta; si no, objetos con todas las palabras; si no, con alguna."""
    cleaned = clean_query(query)
    words = cleaned.split()
    if not words:
        return SearchResult("none", [])

    # El nombre se limpia igual que la consulta: así "Cámara de fotos" coincide con "camara de fotos".
    exact = [i for i in items if clean_query(i.objeto) == cleaned]
    if exact:
        return SearchResult("exact", _unique(exact))

    partial = [i for i in items if all(w in normalize(i.objeto) for w in words)]
    if partial:
        return SearchResult("partial", _unique(partial))

    related = [i for i in items if any(w in normalize(i.objeto) for w in words)]
    if related:
        return SearchResult("related", _unique(related))

    return SearchResult("none", [])


def extract_query(text: str) -> Optional[str]:
    """Texto tras 'dónde está / dónde están / buscar'; None si no es una consulta de búsqueda."""
    match = re.search(r"(?:donde\s+estan?|buscar)\b(.*)", normalize(text), re.DOTALL)
    return match.group(1) if match else None


def format_result(query: str, result: SearchResult) -> str:
    if result.kind == "none":
        return f"No encontré ningún objeto relacionado con '{clean_query(query)}' en el inventario."
    if result.kind == "exact" and len(result.items) == 1:
        item = result.items[0]
        return f"El objeto '{item.objeto}' está en: {item.lugar}"

    header = "Está en varios sitios:" if result.kind == "exact" else "No encontré el objeto exacto, pero aquí tienes alternativas:"
    lines = [f"{n}. {item.objeto} (ubicación: {item.lugar})" for n, item in enumerate(result.items, 1)]
    return "\n".join([header, *lines])


def answer(items: List[Item], text: str) -> str:
    """Respuesta a un mensaje libre del usuario."""
    query = extract_query(text)
    if query is None:
        if "hola" in normalize(text).split():
            return "¡Hola! Soy tu bot de inventario. " + HELP_TEXT
        return "No entiendo tu pregunta. " + HELP_TEXT
    if not clean_query(query):
        return "Dime qué objeto buscas. " + HELP_TEXT
    return format_result(query, search(items, query))
