"""Chat de consola para consultar el inventario: python cli.py"""

import os

from dotenv import load_dotenv

from inventory import answer, load_inventory

DEFAULT_INVENTORY = "inventory_example.xlsx"


def main():
    load_dotenv()
    path = os.environ.get("INVENTORY_FILE", DEFAULT_INVENTORY)
    items = load_inventory(path)

    print(f"Inventario cargado: {len(items)} objetos ({path}). Escribe 'salir' para terminar.")
    while True:
        try:
            text = input("¿Qué quieres saber? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.casefold() == "salir":
            print("¡Hasta luego!")
            break
        print(answer(items, text))


if __name__ == "__main__":
    main()
