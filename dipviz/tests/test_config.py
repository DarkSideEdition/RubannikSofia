"""Тесты загрузки конфигурации."""

import tempfile
import unittest
from pathlib import Path

from depviz.config import format_config, load_config
from depviz.errors import ConfigError


class ConfigTest(unittest.TestCase):
    """Проверка разбора и валидации CSV-конфигурации."""

    def setUp(self):
        """Создаёт временный каталог и тестовый репозиторий."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo.txt"
        self.repo.write_text("A: B\n", encoding="utf-8")

    def make(self, lines):
        """Записывает CSV-файл и возвращает путь к нему."""
        path = Path(self.tmp.name) / "config.csv"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def base(self):
        """Минимальный корректный набор строк."""
        return ["package,A", f"repository,{self.repo}", "test_mode,true"]

    def test_valid_with_defaults(self):
        """Необязательные параметры получают значения по умолчанию."""
        config = load_config(self.make(self.base()))
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.output, "graph.svg")
        self.assertFalse(config.ascii_tree)

    def test_header_and_all_values(self):
        """Заголовок пропускается, все параметры разбираются."""
        lines = ["key,value"] + self.base() + [
            "output,x/y.svg", "ascii_tree,yes", "max_depth,7",
            "filter,lib", "reverse,true"]
        config = load_config(self.make(lines))
        self.assertEqual(config.max_depth, 7)
        self.assertEqual(config.filter, "lib")
        self.assertTrue(config.reverse)
        self.assertIn("max_depth = 7", format_config(config))

    def test_errors(self):
        """Некорректные значения приводят к ConfigError."""
        bad_lines = [
            ["package,A"],
            self.base() + ["max_depth,abc"],
            self.base() + ["max_depth,-1"],
            self.base() + ["ascii_tree,maybe"],
            self.base() + ["output,graph.png"],
            self.base() + ["unknown,1"],
            self.base() + ["package,B"],
            self.base() + ["lonely"],
            ["package,A", "repository,nofile.txt", "test_mode,true"],
            ["package,A", "repository,ftp://x", "test_mode,false"],
        ]
        for lines in bad_lines:
            with self.subTest(lines=lines):
                with self.assertRaises(ConfigError):
                    load_config(self.make(lines))

    def test_missing_file(self):
        """Отсутствующий файл конфигурации даёт ConfigError."""
        with self.assertRaises(ConfigError):
            load_config("no_such_config.csv")


if __name__ == "__main__":
    unittest.main()
