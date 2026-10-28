"""Тесты построения графа."""

import unittest

from depviz.errors import GraphError, RepositoryError
from depviz.graph import build_graph, dependency_edges
from depviz.repository import Repository, parse_test_graph

DIAMOND = "A: B C\nB: D\nC: D E\nD: F\nE:\nF:\n"
CYCLE = "A: B\nB: C\nC: A D\nD: D\n"


def make(text):
    """Создаёт репозиторий из текстового описания."""
    return Repository(parse_test_graph(text))


class GraphTest(unittest.TestCase):
    """Проверка DFS, глубины, фильтра, циклов и обратных зависимостей."""

    def test_transitive(self):
        """Транзитивные зависимости попадают в граф."""
        graph = build_graph(make(DIAMOND), "A", 10, "", False)
        self.assertEqual(set(graph.edges), set("ABCDEF"))
        self.assertEqual(graph.cycles, [])

    def test_max_depth(self):
        """Глубина ограничивает анализ."""
        graph = build_graph(make(DIAMOND), "A", 1, "", False)
        self.assertEqual(set(graph.edges), {"A", "B", "C"})
        zero = build_graph(make(DIAMOND), "A", 0, "", False)
        self.assertEqual(set(zero.edges), {"A"})

    def test_shorter_path_wins(self):
        """Вершина, достижимая коротким путём, раскрывается полностью."""
        repo = make("A: B C\nB: D\nD: C\nC: E\nE:\n")
        graph = build_graph(repo, "A", 3, "", False)
        self.assertIn("E", graph.edges)

    def test_filter(self):
        """Пакеты с подстрокой в имени исключаются вместе с поддеревом."""
        graph = build_graph(make(DIAMOND), "A", 10, "E", False)
        self.assertNotIn("E", graph.edges)
        with self.assertRaises(GraphError):
            build_graph(make(DIAMOND), "A", 10, "A", False)

    def test_cycles(self):
        """Циклы, включая самозависимость, обнаруживаются."""
        graph = build_graph(make(CYCLE), "A", 10, "", False)
        self.assertIn(["A", "B", "C", "A"], graph.cycles)
        self.assertIn(["D", "D"], graph.cycles)

    def test_reverse(self):
        """Обратные зависимости: кто зависит от пакета."""
        graph = build_graph(make(DIAMOND), "D", 10, "", True)
        self.assertEqual(set(graph.edges), {"D", "B", "C", "A"})
        self.assertIn(("B", "D"), dependency_edges(graph))

    def test_unknown_package(self):
        """Неизвестный пакет вызывает GraphError."""
        with self.assertRaises(GraphError):
            build_graph(make(DIAMOND), "Z", 3, "", False)

    def test_bad_test_graph(self):
        """Имена тестового репозитория — большие латинские буквы."""
        for text in ("a: B\n", "A: b\n", "A: B\nA: C\n"):
            with self.subTest(text=text):
                with self.assertRaises(RepositoryError):
                    parse_test_graph(text)

    def test_deep_chain_has_no_recursion_limit(self):
        """Длинная цепочка не приводит к переполнению стека."""
        size = 5000
        adjacency = {f"P{i}": [f"P{i + 1}"] for i in range(size)}
        graph = build_graph(Repository(adjacency), "P0", size, "", False)
        self.assertEqual(len(graph.edges), size + 1)


if __name__ == "__main__":
    unittest.main()
