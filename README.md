# Home Inventory Bot

Estado: funcional (prototipo)

¿Dónde está el martillo? Un buscador del inventario de casa: apuntas tus cosas en un Excel (objeto y lugar) y luego preguntas por consola o por Telegram dónde está cada una.

```
> ¿Dónde está el martillo?
El objeto 'Martillo' está en: Garaje, caja de herramientas

> dónde están las pilas
No encontré el objeto exacto, pero aquí tienes alternativas:
1. Pilas AA (ubicación: Cajón de la cocina)
```

## Cómo busca

Ignora mayúsculas, tildes, signos de puntuación y artículos (`el`, `la`, `del`…). Busca, por orden:

1. un objeto cuyo nombre coincida exactamente con lo que pides;
2. objetos que contengan **todas** las palabras;
3. objetos que contengan **alguna** palabra.

Entiende `¿Dónde está …?`, `¿Dónde están …?` y `buscar …`.

## Puesta en marcha

Requisitos: Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Tu inventario

Un Excel con la primera fila de cabecera y, en la primera hoja, el objeto en la columna A y el lugar en la B. Se incluye `inventory_example.xlsx` con objetos ficticios para probar.

Para usar el tuyo, copia `.env.example` a `.env` y pon `INVENTORY_FILE=mi_inventario.xlsx`. Los `.xlsx` (salvo el de ejemplo) están en `.gitignore`: **tu inventario real no se sube a GitHub**.

### Por consola

```bash
python cli.py
```

### Bot de Telegram

1. En Telegram, habla con [@BotFather](https://t.me/BotFather), crea un bot con `/newbot` y copia el token.
2. Averigua tu ID escribiendo a [@userinfobot](https://t.me/userinfobot).
3. En `.env`, rellena `TELEGRAM_BOT_TOKEN` y `ALLOWED_USER_IDS` (varios IDs separados por comas).
4. Arranca el bot y mantén el script en marcha:

```bash
python telegram_bot.py
```

Comandos: `/start`, `/buscar <objeto>`, o escribe directamente `¿Dónde está el martillo?`.

## Seguridad

- **El token nunca va en el código**, solo en `.env` (ignorado por git). Si se filtra, revócalo con `/revoke` en @BotFather.
- **El bot solo responde a los usuarios de `ALLOWED_USER_IDS`.** Cualquier otro recibe un aviso con su propio ID y nada del inventario. Sin usuarios autorizados, el bot se niega a arrancar.

## Tests

```bash
python -m unittest discover -s tests -t .
```

## Limitaciones

- Es solo lectura: para añadir o mover objetos se edita el Excel y se reinicia el bot.
- Lee solo la primera hoja del Excel.
- La búsqueda por palabras es por trozo de texto (`pila` encuentra `pilas`, pero también cualquier nombre que la contenga).
- El bot usa *polling*: solo responde mientras el script esté ejecutándose.
- Mensajes y búsqueda pensados para español.
