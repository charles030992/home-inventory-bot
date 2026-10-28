import tempfile
import unittest
from pathlib import Path

import openpyxl

from inventory import (
    Item,
    answer,
    clean_query,
    extract_query,
    format_result,
    load_inventory,
    normalize,
    search,
)

ITEMS = [
    Item("Martillo", "Garaje"),
    Item("Destornillador de estrella", "Cajón del salón"),
    Item("Pilas AA", "Cocina"),
    Item("Pilas AAA", "Mando de la tele"),
    Item("Cámara de fotos", "Estudio"),
]


class NormalizeTests(unittest.TestCase):
    def test_normalize_removes_accents_and_case(self):
        self.assertEqual(normalize("Cámara DE Fotos"), "camara de fotos")

    def test_clean_query_removes_punctuation_and_articles(self):
        # Regresión: "el martillo?" quedaba como "martillo?" y no encontraba nada.
        self.assertEqual(clean_query("¿el martillo?"), "martillo")
        self.assertEqual(clean_query("  Las   pilas!! "), "pilas")
        self.assertEqual(clean_query("Cargador del portátil"), "cargador portatil")


class ExtractQueryTests(unittest.TestCase):
    def test_extracts_the_object_after_the_trigger(self):
        self.assertEqual(extract_query("¿Dónde está el martillo?").strip(), "el martillo?")
        self.assertEqual(extract_query("Dónde están las pilas").strip(), "las pilas")
        self.assertEqual(extract_query("buscar destornillador").strip(), "destornillador")
        self.assertEqual(extract_query("no sé dónde está mi taladro").strip(), "mi taladro")

    def test_returns_none_when_it_is_not_a_search(self):
        self.assertIsNone(extract_query("hola"))
        self.assertIsNone(extract_query("qué tiempo hace"))


class SearchTests(unittest.TestCase):
    def test_exact_match_ignores_accents_and_case(self):
        result = search(ITEMS, "camara de fotos")
        self.assertEqual(result.kind, "exact")
        self.assertEqual(result.items, [Item("Cámara de fotos", "Estudio")])

    def test_names_with_articles_still_match_exactly(self):
        # Regresión: el nombre no se limpiaba, así que "Destornillador de estrella" nunca era exacto.
        result = search(ITEMS, "destornillador de estrella")
        self.assertEqual(result.kind, "exact")
        self.assertEqual(format_result("destornillador de estrella", result),
                         "El objeto 'Destornillador de estrella' está en: Cajón del salón")

    def test_question_marks_do_not_break_the_search(self):
        self.assertEqual(search(ITEMS, "¿el martillo?").items, [Item("Martillo", "Garaje")])

    def test_partial_match_needs_all_the_words(self):
        result = search(ITEMS, "destornillador")
        self.assertEqual(result.kind, "partial")
        self.assertEqual(result.items, [Item("Destornillador de estrella", "Cajón del salón")])

    def test_related_match_needs_any_word(self):
        result = search(ITEMS, "martillo grande")
        self.assertEqual(result.kind, "related")
        self.assertEqual(result.items, [Item("Martillo", "Garaje")])

    def test_several_exact_matches_are_all_returned(self):
        items = ITEMS + [Item("Martillo", "Trastero")]
        self.assertEqual(len(search(items, "martillo").items), 2)

    def test_nothing_found(self):
        self.assertEqual(search(ITEMS, "bicicleta").kind, "none")

    def test_empty_query_does_not_dump_the_whole_inventory(self):
        # Regresión: sin palabras clave, all([]) era True y devolvía todos los objetos.
        self.assertEqual(search(ITEMS, "").items, [])
        self.assertEqual(search(ITEMS, "el la de").items, [])


class LoadInventoryTests(unittest.TestCase):
    def test_reads_rows_skipping_header_and_blank_objects(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Objeto", "Lugar"])
        ws.append(["Taladro", "Trastero"])
        ws.append([None, "Garaje"])
        ws.append(["Linterna", None])
        ws.append(["  Cinta métrica ", " Cajón "])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inv.xlsx"
            wb.save(path)
            items = load_inventory(path)
        self.assertEqual(
            items,
            [Item("Taladro", "Trastero"), Item("Linterna", "sin ubicación"), Item("Cinta métrica", "Cajón")],
        )

    def test_the_bundled_example_loads(self):
        items = load_inventory(Path(__file__).resolve().parent.parent / "inventory_example.xlsx")
        self.assertGreaterEqual(len(items), 5)
        self.assertTrue(all(item.objeto and item.lugar for item in items))


class AnswerTests(unittest.TestCase):
    def test_exact_answer(self):
        self.assertEqual(answer(ITEMS, "¿Dónde está el martillo?"), "El objeto 'Martillo' está en: Garaje")

    def test_alternatives_list_every_location(self):
        text = answer(ITEMS, "dónde están las pilas")
        self.assertIn("alternativas", text)
        self.assertIn("1. Pilas AA (ubicación: Cocina)", text)
        self.assertIn("2. Pilas AAA (ubicación: Mando de la tele)", text)

    def test_not_found_answer(self):
        self.assertIn("No encontré", answer(ITEMS, "dónde está la bicicleta"))

    def test_search_without_object_asks_for_one(self):
        self.assertIn("Dime qué objeto", answer(ITEMS, "dónde está"))

    def test_greeting_and_unknown_messages(self):
        self.assertIn("Hola", answer(ITEMS, "hola"))
        self.assertIn("No entiendo", answer(ITEMS, "qué tiempo hace"))

    def test_format_result_for_no_match(self):
        self.assertIn("'bicicleta'", format_result("la bicicleta", search(ITEMS, "bicicleta")))


if __name__ == "__main__":
    unittest.main()
