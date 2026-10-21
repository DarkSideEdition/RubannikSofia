"""Тесты парсера, команд и стартового скрипта."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from emulator import build_vfs, config_lines, parse_args  # noqa: E402
from shell import Shell, ShellError  # noqa: E402
from vfs import Vfs, load  # noqa: E402


def make_shell(vfs=None):
    """Возвращает оболочку и список, куда попадает её вывод."""
    lines = []
    return Shell(vfs or Vfs(), lines.append), lines


class ParserTests(unittest.TestCase):
    """Разбор строк с кавычками."""

    def test_quotes(self):
        """Аргументы в кавычках - один аргумент."""
        name, args = Shell.parse('ls "a b" \'c d\' e')
        self.assertEqual((name, args), ("ls", ["a b", "c d", "e"]))

    def test_empty_and_unclosed(self):
        """Пустая строка не команда; незакрытая кавычка - ошибка."""
        self.assertEqual(Shell.parse("   "), (None, []))
        with self.assertRaisesRegex(ShellError, "незакрытая кавычка"):
            Shell.parse('ls "abc')


class CommandTests(unittest.TestCase):
    """Выполнение команд."""

    def test_stubs(self):
        """ls и cd печатают имя и аргументы."""
        shell, lines = make_shell()
        shell.execute('ls -l "my dir"')
        shell.execute("cd /home")
        self.assertEqual(lines, ["ls: аргументы ['-l', 'my dir']",
                                 "cd: аргументы ['/home']"])

    def test_errors(self):
        """Неизвестная команда и неверные аргументы."""
        shell, _ = make_shell()
        with self.assertRaisesRegex(ShellError, "команда не найдена"):
            shell.execute("foo")
        with self.assertRaisesRegex(ShellError, "слишком много"):
            shell.execute("cd a b")
        with self.assertRaisesRegex(ShellError, "не принимает"):
            shell.execute("exit now")
        self.assertTrue(shell.running)

    def test_exit(self):
        """exit останавливает оболочку."""
        shell, _ = make_shell()
        shell.execute("exit")
        self.assertFalse(shell.running)

    def test_prompt_has_vfs_name(self):
        """Приглашение содержит имя VFS."""
        shell, _ = make_shell(Vfs("demo.csv"))
        self.assertIn("demo.csv", shell.prompt())

    def test_vfs_commands(self):
        """vfs-info и vfs-tree работают с загруженной VFS."""
        vfs = load(os.path.join(ROOT, "vfs", "several.csv"))
        shell, lines = make_shell(vfs)
        shell.execute("vfs-info")
        self.assertIn("Файлов:     4", lines)
        lines.clear()
        shell.execute("vfs-tree")
        self.assertEqual(lines[0], "/")
        self.assertTrue(any("pixel.png (8 Б)" in item for item in lines))


class ScriptTests(unittest.TestCase):
    """Стартовый скрипт."""

    def run_text(self, text):
        """Выполняет скрипт из text и возвращает (ошибок, вывод)."""
        shell, lines = make_shell()
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "s.txt")
            with open(path, "w", encoding="utf-8") as out:
                out.write(text)
            return shell.run_script(path), lines

    def test_skips_bad_lines(self):
        """Ошибочные строки пропускаются, номер строки в сообщении."""
        errors, lines = self.run_text("# c\n\nls\nfoo\ncd a b\nls\n")
        self.assertEqual(errors, 2)
        self.assertIn("Ошибка в скрипте (строка 4): foo: команда не найдена",
                      lines)
        self.assertEqual(sum(1 for x in lines if x.endswith("$ ls")), 2)

    def test_exit_stops_script(self):
        """После exit остальные строки не выполняются."""
        errors, lines = self.run_text("ls\nexit\nls\n")
        self.assertEqual(errors, 0)
        self.assertEqual(sum(1 for x in lines if x.endswith("$ ls")), 1)

    def test_missing_script(self):
        """Отсутствующий скрипт - сообщение об ошибке."""
        shell, lines = make_shell()
        self.assertEqual(shell.run_script("no_such_script.txt"), 1)
        self.assertIn("не удалось прочитать", lines[0])


class ConfigTests(unittest.TestCase):
    """Параметры запуска и сборка VFS."""

    def test_config_lines(self):
        """Отладочный вывод содержит оба параметра."""
        args = parse_args(["--vfs", "a", "--script", "b"])
        text = "\n".join(config_lines(args))
        self.assertIn("a", text)
        self.assertIn("b", text)
        self.assertIn("(не задан)", "\n".join(config_lines(parse_args([]))))

    def test_build_vfs_error(self):
        """Ошибка загрузки даёт пустую VFS и сообщение."""
        vfs, notes = build_vfs("no_such.csv")
        self.assertEqual(vfs.stats(), (0, 0, 0))
        self.assertTrue(notes[0].startswith("Ошибка VFS"))


if __name__ == "__main__":
    unittest.main()
