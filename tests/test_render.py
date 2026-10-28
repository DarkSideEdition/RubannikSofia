"""Тесты визуализации и интерфейса командной строки."""

import contextlib
import io
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

from depviz.cli import main
from depviz.graph import build_graph
from depviz.render import ascii_tree, to_mermaid, to_svg
from depviz.repository import Repository, parse_test_graph

TEXT = "A: B C\nB: D\nC: D A\nD:\n"


def graph():
    """Граф с повторной вершиной и циклом."""
    repo = Repository(parse_test_graph(TEXT))
    return build_graph(repo, "A", 5, "", False)


class RenderTest(unittest.TestCase):
    """Проверка текстовых и графических представлений."""

    def test_ascii_tree(self):
        """ASCII-дерево помечает циклы."""
        expected = ("A\n|-- B\n|   `-- D\n`-- C\n"
                    "    |-- D\n    `-- A (цикл)\n")
        self.assertEqual(ascii_tree(graph()), expected)

    def test_mermaid(self):
        """Mermaid содержит вершины и рёбра."""
        text = to_mermaid(graph())
        self.assertTrue(text.startswith("graph TD"))
        self.assertEqual(text.count("-->"), 5)

    def test_svg_is_valid_xml(self):
        """SVG корректен как XML и содержит подписи вершин."""
        text = to_svg(graph())
        xml.dom.minidom.parseString(text)
        self.assertIn(">A</text>", text)


class CliTest(unittest.TestCase):
    """Проверка запуска из командной строки."""

    def test_main_creates_files(self):
        """Успешный запуск создаёт SVG и Mermaid-файлы."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo.txt"
            repo.write_text(TEXT, encoding="utf-8")
            out = Path(tmp) / "out" / "g.svg"
            config = Path(tmp) / "c.csv"
            config.write_text(
                f"package,A\nrepository,{repo}\ntest_mode,true\n"
                f"output,{out}\nascii_tree,true\n", encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main([str(config)])
            self.assertEqual(code, 0)
            self.assertTrue(out.is_file())
            self.assertTrue(out.with_suffix(".mmd").is_file())
            self.assertIn("Циклическая зависимость", buffer.getvalue())

    def test_main_reports_error(self):
        """Ошибка конфигурации даёт ненулевой код возврата."""
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertNotEqual(main(["no_such.csv"]), 0)


if __name__ == "__main__":
    unittest.main()
