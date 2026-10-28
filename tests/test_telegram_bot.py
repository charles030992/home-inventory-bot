import asyncio
import unittest
from types import SimpleNamespace

from inventory import Item
from telegram_bot import build_application, is_authorized, make_handlers, parse_allowed_ids

ITEMS = [Item("Martillo", "Garaje")]
ALLOWED = {111}


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text):
        self.replies.append(text)


def fake_update(user_id, text=""):
    return SimpleNamespace(effective_user=SimpleNamespace(id=user_id), message=FakeMessage(text))


def run(coro):
    return asyncio.run(coro)


class AllowedIdsTests(unittest.TestCase):
    def test_parses_a_comma_separated_list(self):
        self.assertEqual(parse_allowed_ids("111, 222,333"), {111, 222, 333})

    def test_empty_or_missing_gives_no_users(self):
        self.assertEqual(parse_allowed_ids(""), set())
        self.assertEqual(parse_allowed_ids(None), set())

    def test_rejects_non_numeric_ids(self):
        with self.assertRaises(SystemExit):
            parse_allowed_ids("111, abc")

    def test_is_authorized(self):
        self.assertTrue(is_authorized(111, ALLOWED))
        self.assertFalse(is_authorized(999, ALLOWED))
        self.assertFalse(is_authorized(111, set()))


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.start, self.search_command, self.text_message = make_handlers(ITEMS, ALLOWED)

    def test_authorized_user_gets_answers(self):
        update = fake_update(111, "¿Dónde está el martillo?")
        run(self.text_message(update, None))
        self.assertEqual(update.message.replies, ["El objeto 'Martillo' está en: Garaje"])

    def test_buscar_command_uses_its_arguments(self):
        update = fake_update(111)
        run(self.search_command(update, SimpleNamespace(args=["el", "martillo"])))
        self.assertEqual(update.message.replies, ["El objeto 'Martillo' está en: Garaje"])

    def test_unauthorized_user_never_sees_the_inventory(self):
        for handler, context in [
            (self.start, None),
            (self.search_command, SimpleNamespace(args=["martillo"])),
            (self.text_message, None),
        ]:
            update = fake_update(999, "¿Dónde está el martillo?")
            run(handler(update, context))
            self.assertEqual(len(update.message.replies), 1)
            self.assertIn("No estás autorizado", update.message.replies[0])
            self.assertIn("999", update.message.replies[0])
            self.assertNotIn("Garaje", update.message.replies[0])

    def test_update_without_user_is_ignored(self):
        update = SimpleNamespace(effective_user=None, message=FakeMessage("hola"))
        run(self.text_message(update, None))
        self.assertEqual(update.message.replies, [])


class ApplicationTests(unittest.TestCase):
    def test_application_builds_with_the_three_handlers(self):
        app = build_application("123456:TEST-TOKEN-NOT-REAL", ITEMS, ALLOWED)
        self.assertEqual(sum(len(group) for group in app.handlers.values()), 3)


if __name__ == "__main__":
    unittest.main()
