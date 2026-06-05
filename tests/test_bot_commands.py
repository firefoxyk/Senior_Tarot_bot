import unittest

from main import build_bot_commands


class BotCommandsTest(unittest.TestCase):
    def test_menu_command_is_registered_for_telegram_command_menu(self) -> None:
        commands = {command.command for command in build_bot_commands()}

        self.assertIn("menu", commands)


if __name__ == "__main__":
    unittest.main()
