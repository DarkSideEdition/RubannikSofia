"""Модель репозитория: прямые и обратные зависимости пакетов."""

import re
from pathlib import Path

from depviz.errors import RepositoryError

TEST_NAME = re.compile(r"[A-Z]+")


def invert(adjacency):
    """Строит отображение «пакет -> пакеты, которые от него зависят»."""
    reverse = {}
    for name, dependencies in adjacency.items():
        for dependency in dependencies:
            dependents = reverse.setdefault(dependency, [])
            if name not in dependents:
                dependents.append(name)
    return {key: sorted(value) for key, value in reverse.items()}


class Repository:
    """Хранит граф прямых зависимостей пакетов."""

    def __init__(self, adjacency):
        """Создаёт репозиторий по словарю «пакет -> список зависимостей»."""
        self.adjacency = adjacency
        self.reverse = invert(adjacency)

    def has_package(self, name):
        """Проверяет, известен ли репозиторию пакет."""
        return name in self.adjacency or name in self.reverse

    def dependencies(self, name):
        """Возвращает прямые зависимости пакета."""
        return list(self.adjacency.get(name, []))

    def dependents(self, name):
        """Возвращает пакеты, напрямую зависящие от данного."""
        return list(self.reverse.get(name, []))


def split_test_line(number, line):
    """Разбирает строку тестового репозитория вида «A: B C»."""
    name, _, rest = line.partition(":")
    name = name.strip()
    dependencies = list(dict.fromkeys(rest.split()))
    for item in [name] + dependencies:
        if not TEST_NAME.fullmatch(item):
            raise RepositoryError(
                f"строка {number}: имя «{item}» должно состоять "
                "из больших латинских букв")
    return name, dependencies


def parse_test_graph(text):
    """Разбирает текстовое описание тестового репозитория."""
    adjacency = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        name, dependencies = split_test_line(number, line)
        if name in adjacency:
            raise RepositoryError(f"строка {number}: пакет {name} повторён")
        adjacency[name] = dependencies
    return adjacency


def load_test_repository(path):
    """Загружает тестовый репозиторий из файла."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(
            f"не удалось прочитать {path}: {error}") from error
    return Repository(parse_test_graph(text))
